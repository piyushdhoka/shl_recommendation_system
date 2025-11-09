"""
Streamlit Frontend for SHL Assessment Recommendation System

This module provides a web interface for users to interact with the recommendation system.
"""

import streamlit as st
import requests
import time

# Page configuration
st.set_page_config(
    page_title="SHL Assessment Recommender",
    page_icon="🎯",
    layout="wide"
)

# Title and header
st.title("🎯 Intelligent SHL Assessment Recommendation System")
st.markdown("---")
st.markdown(
    """
    Enter a job description or hiring query below to get personalized SHL assessment recommendations.
    The system uses AI to analyze your requirements and suggest the most relevant assessments.
    """
)

# API endpoint configuration
API_URL = "http://127.0.0.1:8000"

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_url = st.text_input(
        "API URL",
        value=API_URL,
        help="URL of the FastAPI backend server"
    )
    st.markdown("---")
    st.markdown("### 📋 Instructions")
    st.markdown("""
    1. Enter a detailed job description or hiring query
    2. Click "Get Recommendations" to receive AI-powered suggestions
    3. Review the recommended assessments and click links to learn more
    """)

# Main content area
query = st.text_area(
    "Enter Job Description or Hiring Query",
    height=150,
    placeholder="Example: I need to hire a senior Java developer with strong problem-solving skills, leadership capabilities, and experience in agile methodologies. The candidate should be able to work in a team environment and communicate effectively with stakeholders."
)

# Button to get recommendations
if st.button("🔍 Get Recommendations", type="primary", use_container_width=True):
    if not query or not query.strip():
        st.warning("⚠️ Please enter a job description or query before requesting recommendations.")
    else:
        # Show loading spinner
        with st.spinner("🤔 Analyzing your query and generating recommendations..."):
            try:
                # Make API request
                response = requests.post(
                    f"{api_url}/recommend",
                    json={"query": query.strip()},
                    timeout=60
                )
                
                # Check response status
                if response.status_code == 200:
                    data = response.json()
                    recommendations = data.get("recommendations", [])
                    
                    if recommendations:
                        st.success(f"✅ Found {len(recommendations)} recommended assessments!")
                        st.markdown("---")
                        
                        # Display recommendations
                        st.subheader("📊 Recommended Assessments")
                        
                        for i, rec in enumerate(recommendations, 1):
                            with st.container():
                                # Assessment name and link
                                col1, col2 = st.columns([4, 1])
                                
                                with col1:
                                    st.markdown(f"### {i}. {rec.get('assessment_name', 'Unknown Assessment')}")
                                
                                with col2:
                                    # Handle both 'url' and 'assessment_url' for compatibility
                                    url = rec.get('url', rec.get('assessment_url', '#'))
                                    st.markdown(f"[🔗 View Details]({url})")
                                
                                # Description
                                if rec.get('description'):
                                    with st.expander("📝 Description", expanded=False):
                                        st.write(rec['description'])
                                
                                # Why it's a great fit
                                if rec.get('why_great_fit'):
                                    st.info(f"💡 **Why this is a great fit:** {rec['why_great_fit']}")
                                
                                # Assessment length
                                if rec.get('assessment_length'):
                                    st.caption(f"⏱️ **Assessment Length:** {rec['assessment_length']}")
                                
                                st.markdown("---")
                        
                        # Alternative: Display as dataframe
                        st.subheader("📋 Summary Table")
                        df_data = {
                            "Assessment Name": [r.get("assessment_name", "") for r in recommendations],
                            "Description": [r.get("description", "")[:100] + "..." if len(r.get("description", "")) > 100 else r.get("description", "") for r in recommendations],
                            "Length": [r.get("assessment_length", "Not specified") for r in recommendations],
                            "URL": [r.get("url", r.get("assessment_url", "")) for r in recommendations]
                        }
                        st.dataframe(
                            df_data,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Description": st.column_config.TextColumn(
                                    "Description",
                                    width="medium",
                                ),
                                "URL": st.column_config.LinkColumn("URL")
                            }
                        )
                        
                    else:
                        st.warning("⚠️ No recommendations found. Try refining your query.")
                        
                elif response.status_code == 400:
                    error_data = response.json()
                    st.error(f"❌ Bad Request: {error_data.get('detail', 'Invalid request')}")
                    
                elif response.status_code == 500:
                    error_data = response.json()
                    st.error(f"❌ Server Error: {error_data.get('detail', 'Internal server error')}")
                    st.info("💡 Make sure the vector store files are generated and the Groq API key is set correctly.")
                    
                else:
                    st.error(f"❌ Unexpected error: Status code {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Connection Error: Could not connect to the API server.")
                st.info("💡 Make sure the FastAPI server is running. Start it with: `python main.py` or `uvicorn main:app --reload`")
                
            except requests.exceptions.Timeout:
                st.error("❌ Request Timeout: The API took too long to respond.")
                
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <p>Powered by Groq AI & FAISS Vector Search</p>
    </div>
    """,
    unsafe_allow_html=True
)

