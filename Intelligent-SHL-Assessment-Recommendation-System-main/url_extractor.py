"""
URL Extractor for Job Descriptions

This module extracts text content from job description URLs.
"""

import requests
from bs4 import BeautifulSoup
import re


def extract_text_from_url(url: str) -> str:
    """
    Extract text content from a URL (job description).
    
    Args:
        url: URL to extract text from
        
    Returns:
        str: Extracted text content
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script, style, and other non-content elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'noscript']):
            element.decompose()
        
        # Try to find main content area
        main_content = soup.find(['main', 'article', 'div'], 
                                class_=lambda x: x and ('content' in x.lower() or 
                                                       'main' in x.lower() or
                                                       'body' in x.lower() or
                                                       'article' in x.lower() or
                                                       'job' in x.lower() or
                                                       'description' in x.lower()))
        
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
        else:
            # Fallback to body text
            body = soup.find('body')
            if body:
                text = body.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)
        
        # Clean up text
        text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespace with single space
        text = text.strip()
        
        return text
        
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error extracting text from URL: {str(e)}")


def is_url(text: str) -> bool:
    """
    Check if the input text is a URL.
    
    Args:
        text: Input text to check
        
    Returns:
        bool: True if text appears to be a URL
    """
    text = text.strip()
    return (text.startswith('http://') or 
            text.startswith('https://') or
            text.startswith('www.'))


def process_query(query: str) -> str:
    """
    Process a query that could be either text or a URL.
    If it's a URL, extract the text content.
    
    Args:
        query: Query text or URL
        
    Returns:
        str: Processed query text
    """
    query = query.strip()
    
    if is_url(query):
        print(f"Detected URL, extracting content from: {query}")
        extracted_text = extract_text_from_url(query)
        print(f"Extracted {len(extracted_text)} characters from URL")
        return extracted_text
    else:
        return query

