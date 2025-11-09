"""
Generate Test Predictions CSV

This script generates predictions for the test set in the required CSV format.
"""

import pandas as pd
import os
from engine import get_recommendations


def generate_predictions_csv(test_file_path: str, output_file: str = "test_predictions.csv"):
    """
    Generate predictions CSV for test set.
    
    Args:
        test_file_path: Path to test set file (CSV or Excel with 'Query' column)
        output_file: Output CSV file path
    """
    # Read test set
    if test_file_path.endswith('.xlsx'):
        df_test = pd.read_excel(test_file_path)
    else:
        df_test = pd.read_csv(test_file_path)
    
    # Check if 'Query' column exists
    if 'Query' not in df_test.columns:
        # Try case-insensitive search
        query_col = None
        for col in df_test.columns:
            if 'query' in col.lower():
                query_col = col
                break
        
        if query_col is None:
            raise ValueError(f"'Query' column not found in test file. Available columns: {df_test.columns.tolist()}")
        
        df_test = df_test.rename(columns={query_col: 'Query'})
    
    print(f"Found {len(df_test)} test queries.")
    
    # Generate predictions
    results = []
    
    for idx, row in df_test.iterrows():
        query = row['Query']
        print(f"\n[{idx + 1}/{len(df_test)}] Processing: {query[:50]}...")
        
        try:
            # Get recommendations
            recommendations = get_recommendations(query)
            
            # Add each recommendation to results
            for rec in recommendations:
                # Handle both 'url' and 'assessment_url' for compatibility
                url = rec.get('assessment_url', rec.get('url', ''))
                results.append({
                    'Query': query,
                    'Assessment_url': url
                })
            
            print(f"  Generated {len(recommendations)} recommendations.")
            
        except Exception as e:
            print(f"  Error processing query: {e}")
            # Add empty result to maintain format
            results.append({
                'Query': query,
                'Assessment_url': ''
            })
    
    # Create DataFrame
    df_results = pd.DataFrame(results)
    
    # Save to CSV
    df_results.to_csv(output_file, index=False)
    print(f"\n✅ Predictions saved to: {output_file}")
    print(f"Total rows: {len(df_results)}")
    print(f"Unique queries: {df_results['Query'].nunique()}")
    
    return df_results


if __name__ == "__main__":
    import sys
    
    # Check for test file path argument
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        # Default test file names to try
        test_file = None
        for filename in ['test_set.csv', 'test_set.xlsx', 'unlabeled_test_set.csv', 'unlabeled_test_set.xlsx']:
            if os.path.exists(filename):
                test_file = filename
                break
        
        if test_file is None:
            print("Error: Test file not found.")
            print("Usage: python generate_test_predictions.py <test_file_path>")
            print("Or place test file as: test_set.csv, test_set.xlsx, unlabeled_test_set.csv, or unlabeled_test_set.xlsx")
            sys.exit(1)
    
    # Check for output file argument
    output_file = sys.argv[2] if len(sys.argv) > 2 else "test_predictions.csv"
    
    print(f"Reading test set from: {test_file}")
    print(f"Output will be saved to: {output_file}")
    
    generate_predictions_csv(test_file, output_file)

