"""
Full System Validation Script

This script performs end-to-end validation of the SHL Assessment Recommendation System.
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists


def check_python_imports():
    """Check if all required Python packages can be imported."""
    print("\n" + "=" * 60)
    print("Checking Python Dependencies...")
    print("=" * 60)
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'streamlit',
        'requests',
        'pandas',
        'numpy',
        'faiss',
        'sentence_transformers',
        'groq',
        'beautifulsoup4',
        'dotenv'
    ]
    
    all_ok = True
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            all_ok = False
    
    return all_ok


def check_data_files():
    """Check if required data files exist."""
    print("\n" + "=" * 60)
    print("Checking Data Files...")
    print("=" * 60)
    
    required_files = [
        ('data/shl_assessments.csv', 'Assessment data CSV'),
        ('data/faiss_index.bin', 'FAISS vector index'),
        ('data/index_to_data.pkl', 'Index to data mapping'),
    ]
    
    all_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist


def check_code_files():
    """Check if all required code files exist."""
    print("\n" + "=" * 60)
    print("Checking Code Files...")
    print("=" * 60)
    
    required_files = [
        ('scraper.py', 'Data scraper'),
        ('build_vector_store.py', 'Vector store builder'),
        ('engine.py', 'Recommendation engine'),
        ('main.py', 'FastAPI backend'),
        ('app.py', 'Streamlit frontend'),
        ('url_extractor.py', 'URL extractor'),
        ('generate_test_predictions.py', 'CSV generator'),
        ('evaluate_performance.py', 'Performance evaluator'),
        ('validate_api.py', 'API validator'),
        ('requirements.txt', 'Dependencies'),
        ('README.md', 'Documentation'),
        ('SOLUTION_APPROACH.md', 'Solution approach'),
    ]
    
    all_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist


def validate_api_structure():
    """Validate API code structure."""
    print("\n" + "=" * 60)
    print("Validating API Structure...")
    print("=" * 60)
    
    try:
        with open('main.py', 'r') as f:
            content = f.read()
        
        checks = {
            "FastAPI import": "from fastapi import" in content,
            "Health endpoint": "@app.get(\"/health\")" in content or '@app.get("/health")' in content,
            "Recommend endpoint": "@app.post(\"/recommend\")" in content or '@app.post("/recommend")' in content,
            "CORS middleware": "CORSMiddleware" in content,
            "RecommendationRequest model": "class RecommendationRequest" in content,
            "RecommendationResponse model": "class RecommendationResponse" in content,
            "Query field in response": '"query"' in content or "'query'" in content or 'query=' in content,
        }
        
        all_ok = True
        for check_name, check_result in checks.items():
            status = "✅" if check_result else "❌"
            print(f"{status} {check_name}")
            if not check_result:
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"❌ Error reading main.py: {e}")
        return False


def generate_system_summary():
    """Generate system summary JSON."""
    print("\n" + "=" * 60)
    print("Generating System Summary...")
    print("=" * 60)
    
    summary = {
        "project_name": "Intelligent SHL Assessment Recommendation System",
        "architecture": "RAG (Retrieval-Augmented Generation)",
        "version": "1.0.0",
        "components": {
            "data_pipeline": {
                "crawler": "scraper.py",
                "vector_store": "build_vector_store.py",
                "embedding_model": "all-MiniLM-L6-v2",
                "vector_database": "FAISS"
            },
            "recommendation_engine": {
                "file": "engine.py",
                "llm": "Groq Llama 3.1 8B Instant",
                "vector_db": "FAISS",
                "retrieval": "Top 20 candidates",
                "re_ranking": "LLM-based"
            },
            "api": {
                "file": "main.py",
                "framework": "FastAPI",
                "endpoints": {
                    "health": {
                        "method": "GET",
                        "path": "/health",
                        "response": {"status": "ok"}
                    },
                    "recommend": {
                        "method": "POST",
                        "path": "/recommend",
                        "request": {"query": "string"},
                        "response": {
                            "query": "string",
                            "recommendations": [
                                {
                                    "assessment_name": "string",
                                    "url": "string"
                                }
                            ]
                        }
                    }
                }
            },
            "frontend": {
                "file": "app.py",
                "framework": "Streamlit"
            }
        },
        "features": {
            "input_types": ["natural_language", "job_description_text", "url"],
            "recommendation_count": {"min": 5, "max": 10},
            "exclusions": ["pre_packaged_job_solutions"],
            "balance": "automatic_mix_of_technical_and_behavioral",
            "additional_fields": ["description", "why_great_fit", "assessment_length"]
        },
        "evaluation": {
            "metric": "Mean Recall@10",
            "script": "evaluate_performance.py"
        },
        "submission": {
            "csv_generator": "generate_test_predictions.py",
            "documentation": "SOLUTION_APPROACH.md"
        },
        "technology_stack": {
            "backend": "FastAPI, Uvicorn",
            "frontend": "Streamlit",
            "ai_ml": "Groq API, Sentence Transformers, FAISS",
            "data_processing": "Pandas, BeautifulSoup, Requests"
        }
    }
    
    # Save to JSON
    with open('system_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✅ System summary saved to: system_summary.json")
    return summary


def main():
    """Run full validation."""
    print("=" * 60)
    print("SHL ASSESSMENT RECOMMENDATION SYSTEM - FULL VALIDATION")
    print("=" * 60)
    
    results = {
        "python_dependencies": check_python_imports(),
        "code_files": check_code_files(),
        "data_files": check_data_files(),
        "api_structure": validate_api_structure(),
    }
    
    # Generate system summary
    summary = generate_system_summary()
    
    # Final summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, check_result in results.items():
        status = "✅ PASS" if check_result else "❌ FAIL"
        print(f"{status} {check_name.replace('_', ' ').title()}")
        if not check_result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All validation checks passed!")
        print("\nNext steps:")
        print("1. Deploy API to cloud (Render/Railway/Heroku)")
        print("2. Deploy frontend to Streamlit Cloud")
        print("3. Push code to GitHub")
        print("4. Generate CSV: python generate_test_predictions.py <test_file>")
        print("5. Submit all URLs and files")
    else:
        print("\n⚠️  Some validation checks failed. Please review above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

