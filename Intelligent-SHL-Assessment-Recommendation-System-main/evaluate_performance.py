"""
Performance Evaluation Script

Calculates Mean Recall@10 on labeled train set.
"""

import pandas as pd
import os
from engine import get_recommendations
from typing import List, Set


def calculate_recall_at_k(recommended_urls: List[str], relevant_urls: Set[str], k: int = 10) -> float:
    """
    Calculate Recall@K metric.
    
    Args:
        recommended_urls: List of recommended assessment URLs
        relevant_urls: Set of relevant assessment URLs (ground truth)
        k: Number of top recommendations to consider
        
    Returns:
        float: Recall@K score (0.0 to 1.0)
    """
    if not relevant_urls:
        return 0.0
    
    # Take top k recommendations
    top_k = recommended_urls[:k]
    
    # Count how many relevant items are in top k
    relevant_in_top_k = sum(1 for url in top_k if url in relevant_urls)
    
    # Calculate recall
    recall = relevant_in_top_k / len(relevant_urls)
    
    return recall


def evaluate_on_train_set(train_file: str = "train_set.csv"):
    """
    Evaluate performance on labeled train set.
    
    Expected format:
    - Query column: Contains the query text
    - Assessment_url column: Contains relevant assessment URLs
    - Multiple rows per query (one per relevant assessment)
    """
    print("=" * 60)
    print("PERFORMANCE EVALUATION")
    print("=" * 60)
    
    # Try to find train set file
    possible_files = [
        train_file,
        "train_set.csv",
        "train_set.xlsx",
        "labeled_train_set.csv",
        "labeled_train_set.xlsx"
    ]
    
    train_file_path = None
    for f in possible_files:
        if os.path.exists(f):
            train_file_path = f
            break
    
    if not train_file_path:
        print(f"❌ Train set file not found. Tried: {possible_files}")
        print("   Please provide the labeled train set file.")
        return None
    
    print(f"Reading train set from: {train_file_path}\n")
    
    # Read train set
    if train_file_path.endswith('.xlsx'):
        df = pd.read_excel(train_file_path)
    else:
        df = pd.read_csv(train_file_path)
    
    # Find query and url columns
    query_col = None
    url_col = None
    
    for col in df.columns:
        if 'query' in col.lower():
            query_col = col
        if 'assessment' in col.lower() and 'url' in col.lower():
            url_col = col
    
    if not query_col or not url_col:
        print(f"❌ Required columns not found.")
        print(f"   Available columns: {df.columns.tolist()}")
        print(f"   Expected: Query column and Assessment_url column")
        return None
    
    # Group by query to get relevant URLs for each query
    query_groups = df.groupby(query_col)[url_col].apply(set).to_dict()
    
    print(f"Found {len(query_groups)} unique queries\n")
    
    # Evaluate each query
    results = []
    
    for idx, (query, relevant_urls) in enumerate(query_groups.items(), 1):
        print(f"[{idx}/{len(query_groups)}] Processing: {query[:60]}...")
        
        try:
            # Get recommendations
            recommendations = get_recommendations(query)
            
            # Extract URLs from recommendations
            recommended_urls = [rec.get('assessment_url', rec.get('url', '')) for rec in recommendations]
            
            # Calculate Recall@10
            recall_10 = calculate_recall_at_k(recommended_urls, relevant_urls, k=10)
            
            # Count relevant in recommendations
            relevant_found = sum(1 for url in recommended_urls if url in relevant_urls)
            
            results.append({
                'Query': query,
                'Relevant_Count': len(relevant_urls),
                'Recommended_Count': len(recommended_urls),
                'Relevant_Found': relevant_found,
                'Recall@10': recall_10
            })
            
            print(f"   Relevant: {len(relevant_urls)}, Found: {relevant_found}, Recall@10: {recall_10:.3f}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'Query': query,
                'Relevant_Count': len(relevant_urls),
                'Recommended_Count': 0,
                'Relevant_Found': 0,
                'Recall@10': 0.0
            })
    
    # Calculate Mean Recall@10
    df_results = pd.DataFrame(results)
    mean_recall_10 = df_results['Recall@10'].mean()
    
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print("\nDetailed Results:")
    print(df_results.to_string(index=False))
    
    print(f"\n{'='*60}")
    print(f"Mean Recall@10: {mean_recall_10:.4f}")
    print(f"{'='*60}\n")
    
    # Save results
    df_results.to_csv("evaluation_results.csv", index=False)
    print("Results saved to: evaluation_results.csv")
    
    return mean_recall_10


if __name__ == "__main__":
    import sys
    
    train_file = sys.argv[1] if len(sys.argv) > 1 else None
    evaluate_on_train_set(train_file)

