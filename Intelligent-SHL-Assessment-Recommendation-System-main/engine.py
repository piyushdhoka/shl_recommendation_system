"""
Recommendation Engine with RAG Pipeline

This module contains the core logic for the Retrieval-Augmented Generation (RAG)
pipeline that powers the SHL assessment recommendation system.
"""

import os
import json
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
from url_extractor import process_query

# Load environment variables
try:
    load_dotenv()
except UnicodeDecodeError:
    # If .env file has encoding issues, try to handle it
    import sys
    print("Warning: .env file encoding issue detected. Please ensure .env is UTF-8 encoded.", file=sys.stderr)
    # Try to load with explicit encoding
    try:
        with open('.env', 'r', encoding='utf-8-sig') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"\'')
    except Exception as e:
        print(f"Error loading .env file: {e}", file=sys.stderr)


def get_recommendations(query: str) -> list:
    """
    Get assessment recommendations using RAG pipeline.
    
    Args:
        query: User's hiring query, job description text, or URL containing a JD
        
    Returns:
        list: List of dictionaries with 'assessment_name' and 'assessment_url' keys
        (minimum 5, maximum 10 recommendations)
    """
    # Process query - extract text if URL is provided
    query = process_query(query)
    # Load FAISS index and mapping data
    index_path = 'data/faiss_index.bin'
    mapping_path = 'data/index_to_data.pkl'
    
    if not os.path.exists(index_path) or not os.path.exists(mapping_path):
        raise FileNotFoundError(
            "Vector store files not found. Please run build_vector_store.py first."
        )
    
    print("Loading FAISS index and mapping data...")
    index = faiss.read_index(index_path)
    
    with open(mapping_path, 'rb') as f:
        index_to_data = pickle.load(f)
    
    # Load sentence transformer model
    print("Loading sentence transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Load Groq API key and initialize client
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in .env file")
    
    # Clean up API key (remove quotes if present)
    groq_api_key = groq_api_key.strip().strip('"').strip("'")
    
    # Initialize Groq client
    # Workaround for old Groq library versions (0.4.1) that have proxies issue
    try:
        # Try standard initialization
        client = Groq(api_key=groq_api_key)
    except Exception as e:
        error_msg = str(e)
        # Check if it's the proxies error (common in groq 0.4.1)
        if 'proxies' in error_msg.lower():
            # Workaround: Monkey-patch the Client class to remove proxies parameter
            try:
                import groq._client
                original_init = groq._client.Client.__init__
                
                def patched_init(self, *args, **kwargs):
                    # Remove proxies if present
                    kwargs.pop('proxies', None)
                    return original_init(self, *args, **kwargs)
                
                groq._client.Client.__init__ = patched_init
                
                # Now try again
                client = Groq(api_key=groq_api_key)
            except Exception as e2:
                raise ValueError(
                    f"Failed to initialize Groq client due to version compatibility issue. "
                    f"Error: {error_msg}\n"
                    f"Please upgrade the groq library by running: `uv pip install --upgrade groq`\n"
                    f"Make sure to stop the server first before upgrading."
                )
        else:
            raise ValueError(f"Failed to initialize Groq client: {error_msg}")
    
    # RETRIEVAL STEP
    print("Performing semantic search...")
    # Convert query to vector
    query_embedding = model.encode([query], convert_to_numpy=True).astype('float32')
    
    # Search for top 20 most similar assessments
    k = 20
    distances, indices = index.search(query_embedding, k)
    
    # Retrieve full details of top candidates
    retrieved_assessments = []
    for idx in indices[0]:
        if idx < len(index_to_data):
            retrieved_assessments.append(index_to_data[idx])
    
    # Format retrieved context for the prompt
    retrieved_context = ""
    for i, assessment in enumerate(retrieved_assessments, 1):
        retrieved_context += f"{i}. **{assessment['assessment_name']}**\n"
        retrieved_context += f"   Type: {assessment['assessment_type']}\n"
        retrieved_context += f"   Description: {assessment['assessment_description']}\n"
        
        # Add optional fields if available
        if 'job_levels' in assessment and assessment.get('job_levels'):
            retrieved_context += f"   Job Levels: {assessment['job_levels']}\n"
        if 'languages' in assessment and assessment.get('languages'):
            retrieved_context += f"   Languages: {assessment['languages']}\n"
        if 'assessment_length' in assessment and assessment.get('assessment_length'):
            retrieved_context += f"   Assessment Length: {assessment['assessment_length']}\n"
        
        retrieved_context += f"   URL: {assessment['assessment_url']}\n\n"
    
    # GENERATION STEP
    # Construct the prompt
    prompt = f"""**Role:** You are an expert HR Recruitment Assistant specializing in SHL assessments. Your primary goal is to provide precise, balanced, and relevant assessment recommendations based on a user's hiring query and a list of potential assessments.

**User's Hiring Query:**

"{query}"

**Context: Potential SHL Assessments:**

Here is a numbered list of potentially relevant assessments retrieved based on the query. Analyze these carefully to make your final selection.

---

{retrieved_context}

---

**Your Task & Instructions:**

1.  **Analyze the Query:** Deconstruct the user's query to identify key requirements: job role, seniority, technical skills (e.g., Java, Python, SQL), and behavioral competencies (e.g., teamwork, leadership, communication, cultural fit).

2.  **Evaluate Context:** Review the provided list of assessments and evaluate how each one maps to the specific requirements you identified in the query.

3.  **Select & Re-Rank:** Choose the most relevant 5 to 10 assessments from the list. Your selection must be directly justified by the query's needs.

4.  **Ensure Balance:** This is critical. If the query mentions both technical abilities and behavioral traits (e.g., "a Java developer who can collaborate effectively"), you MUST ensure your final recommendations include a mix of assessments covering both "Knowledge & Skills" and "Personality & Behavior".

5.  **Provide Detailed Information:** For each selected assessment, provide:
   - A brief description of what the assessment measures
   - A clear explanation of why it's a great fit for the user's query (connect specific requirements from the query to the assessment's capabilities)
   - The assessment length/completion time if available

6.  **Strict Output Format:** You must format your final answer ONLY as a valid JSON array of objects. Each object must have the following keys:
   - "assessment_name": The name of the assessment
   - "assessment_url": The URL to the assessment page
   - "description": A brief description of what the assessment measures
   - "why_great_fit": A clear explanation (2-3 sentences) of why this assessment is a great fit for the user's query
   - "assessment_length": The assessment length/completion time (e.g., "15 to 35 minutes" or "Approximate Completion Time in minutes = 15 to 35")
   
   Do not include any introductory text, explanations, or markdown formatting around the JSON.
"""
    
    print("Calling Groq API...")
    # Make API call to Groq
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=4000
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        # Sometimes the model includes markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON response
        try:
            recommendations = json.loads(response_text)
            
            # Validate structure
            if not isinstance(recommendations, list):
                raise ValueError("Response is not a list")
            
            # Ensure each item has required keys and extract all fields
            validated_recommendations = []
            for item in recommendations:
                if isinstance(item, dict) and 'assessment_name' in item and 'assessment_url' in item:
                    # Build recommendation with all available fields
                    rec = {
                        'assessment_name': item['assessment_name'],
                        'assessment_url': item['assessment_url']
                    }
                    
                    # Add optional fields if provided by the model
                    if 'description' in item:
                        rec['description'] = item['description']
                    elif 'assessment_description' in item:
                        rec['description'] = item['assessment_description']
                    else:
                        # Try to get from retrieved assessments by matching URL
                        matching_assessment = next(
                            (a for a in retrieved_assessments if a.get('assessment_url') == rec['assessment_url']),
                            None
                        )
                        if matching_assessment and matching_assessment.get('assessment_description'):
                            rec['description'] = matching_assessment['assessment_description']
                        else:
                            rec['description'] = ""
                    
                    if 'why_great_fit' in item:
                        rec['why_great_fit'] = item['why_great_fit']
                    else:
                        rec['why_great_fit'] = "This assessment is recommended based on your query requirements."
                    
                    if 'assessment_length' in item:
                        rec['assessment_length'] = item['assessment_length']
                    else:
                        # Try to get from retrieved assessments by matching URL
                        matching_assessment = next(
                            (a for a in retrieved_assessments if a.get('assessment_url') == rec['assessment_url']),
                            None
                        )
                        if matching_assessment and matching_assessment.get('assessment_length'):
                            rec['assessment_length'] = matching_assessment['assessment_length']
                        else:
                            rec['assessment_length'] = "Not specified"
                    
                    validated_recommendations.append(rec)
            
            print(f"Successfully retrieved {len(validated_recommendations)} recommendations.")
            
            # Ensure minimum 5 and maximum 10 recommendations
            if len(validated_recommendations) < 5:
                # If we have less than 5, add more from retrieved assessments
                print(f"Only {len(validated_recommendations)} recommendations found. Adding more from retrieved assessments...")
                for item in retrieved_assessments:
                    if len(validated_recommendations) >= 5:
                        break
                    # Check if already in recommendations
                    if not any(rec['assessment_url'] == item.get('assessment_url') for rec in validated_recommendations):
                        fallback_rec = {
                            'assessment_name': item['assessment_name'],
                            'assessment_url': item['assessment_url'],
                            'description': item.get('assessment_description', ''),
                            'why_great_fit': f"This assessment is recommended based on your query requirements. It measures {item.get('assessment_type', 'relevant skills')} that align with your hiring needs.",
                            'assessment_length': item.get('assessment_length', 'Not specified')
                        }
                        validated_recommendations.append(fallback_rec)
            
            # Limit to maximum 10
            if len(validated_recommendations) > 10:
                validated_recommendations = validated_recommendations[:10]
                print(f"Limited to top 10 recommendations.")
            
            return validated_recommendations
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response text: {response_text[:500]}")
            # Fallback: return top 5-10 from retrieved assessments with all available info
            print("Falling back to top 5-10 retrieved assessments...")
            fallback_recommendations = []
            # Take at least 5, up to 10
            num_to_take = min(max(5, len(retrieved_assessments)), 10)
            for item in retrieved_assessments[:num_to_take]:
                fallback_rec = {
                    'assessment_name': item['assessment_name'],
                    'assessment_url': item['assessment_url'],
                    'description': item.get('assessment_description', ''),
                    'why_great_fit': f"This assessment is recommended based on your query requirements. It measures {item.get('assessment_type', 'relevant skills')} that align with your hiring needs.",
                    'assessment_length': item.get('assessment_length', 'Not specified')
                }
                fallback_recommendations.append(fallback_rec)
            return fallback_recommendations
            
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        # Fallback: return top 5-10 from retrieved assessments with all available info
        print("Falling back to top 5-10 retrieved assessments...")
        fallback_recommendations = []
        # Take at least 5, up to 10
        num_to_take = min(max(5, len(retrieved_assessments)), 10)
        for item in retrieved_assessments[:num_to_take]:
            fallback_rec = {
                'assessment_name': item['assessment_name'],
                'assessment_url': item['assessment_url'],
                'description': item.get('assessment_description', ''),
                'why_great_fit': f"This assessment is recommended based on your query requirements. It measures {item.get('assessment_type', 'relevant skills')} that align with your hiring needs.",
                'assessment_length': item.get('assessment_length', 'Not specified')
            }
            fallback_recommendations.append(fallback_rec)
        return fallback_recommendations

