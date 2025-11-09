"""
Vector Store Builder for SHL Assessments

This script processes the scraped assessment data and creates a FAISS vector index
for semantic search using sentence transformers.
"""

import pandas as pd
import faiss
import pickle
import os
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm


def build_vector_store():
    """
    Build FAISS vector index from assessment CSV data.
    
    Creates:
        - data/faiss_index.bin: FAISS index file
        - data/index_to_data.pkl: Mapping from index to assessment data
    """
    # Load the CSV file
    csv_path = 'data/shl_assessments.csv'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Please run scraper.py first.")
        return
    
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    if df.empty:
        print("Error: CSV file is empty. Please run scraper.py first.")
        return
    
    print(f"Loaded {len(df)} assessments.")
    
    # Initialize the sentence transformer model
    print("Loading sentence transformer model: all-MiniLM-L6-v2...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Get the embedding dimension
    embedding_dim = model.get_sentence_embedding_dimension()
    print(f"Embedding dimension: {embedding_dim}")
    
    # Create consolidated documents for embedding
    print("Creating consolidated documents...")
    documents = []
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing documents"):
        # Build comprehensive document with all available information
        doc_parts = [
            f"Name: {row['assessment_name']}",
            f"Type: {row['assessment_type']}",
            f"Description: {row['assessment_description']}"
        ]
        
        # Add optional fields if they exist
        if 'job_levels' in row and pd.notna(row['job_levels']) and row['job_levels']:
            doc_parts.append(f"Job Levels: {row['job_levels']}")
        
        if 'languages' in row and pd.notna(row['languages']) and row['languages']:
            doc_parts.append(f"Languages: {row['languages']}")
        
        if 'assessment_length' in row and pd.notna(row['assessment_length']) and row['assessment_length']:
            doc_parts.append(f"Assessment Length: {row['assessment_length']}")
        
        doc = "\n".join(doc_parts)
        documents.append(doc)
    
    # Generate embeddings
    print("Generating embeddings...")
    embeddings = model.encode(documents, show_progress_bar=True, convert_to_numpy=True)
    
    # Ensure embeddings are float32 for FAISS
    embeddings = embeddings.astype('float32')
    
    # Create FAISS index
    print("Creating FAISS index...")
    index = faiss.IndexFlatL2(embedding_dim)
    
    # Add embeddings to index
    index.add(embeddings)
    print(f"Index created with {index.ntotal} vectors.")
    
    # Create mapping from index position to assessment data
    print("Creating index-to-data mapping...")
    index_to_data = []
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Creating mappings"):
        data_item = {
            'assessment_name': row['assessment_name'],
            'assessment_url': row['assessment_url'],
            'assessment_description': row['assessment_description'],
            'assessment_type': row['assessment_type']
        }
        
        # Add optional fields if they exist
        if 'job_levels' in row:
            data_item['job_levels'] = row['job_levels'] if pd.notna(row['job_levels']) else ""
        if 'languages' in row:
            data_item['languages'] = row['languages'] if pd.notna(row['languages']) else ""
        if 'assessment_length' in row:
            data_item['assessment_length'] = row['assessment_length'] if pd.notna(row['assessment_length']) else ""
        
        index_to_data.append(data_item)
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Save FAISS index
    index_path = 'data/faiss_index.bin'
    faiss.write_index(index, index_path)
    print(f"FAISS index saved to: {index_path}")
    
    # Save mapping using pickle
    mapping_path = 'data/index_to_data.pkl'
    with open(mapping_path, 'wb') as f:
        pickle.dump(index_to_data, f)
    print(f"Index-to-data mapping saved to: {mapping_path}")
    
    print("\nVector store build complete!")
    print(f"  - Index file: {index_path}")
    print(f"  - Mapping file: {mapping_path}")
    print(f"  - Total vectors: {index.ntotal}")


if __name__ == "__main__":
    build_vector_store()

