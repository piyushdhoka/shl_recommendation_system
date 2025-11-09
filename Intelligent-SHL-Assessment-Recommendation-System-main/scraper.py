"""
SHL Assessment Data Scraper

This script reads assessment URLs from Gen_AI_Dataset.xlsx and scrapes
each assessment page to extract detailed information.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from tqdm import tqdm


def scrape_assessment_page(url: str) -> dict:
    """
    Scrape a single assessment page to extract details.
    
    Args:
        url: URL of the assessment page
        
    Returns:
        dict: Dictionary with assessment_name, assessment_url, 
              assessment_description, and assessment_type
    """
    # Use more modern browser headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  Error fetching {url}: {e}")
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove script, style, and other non-content elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'noscript']):
        element.decompose()
    
    # Extract assessment name (title)
    # Try multiple selectors for title
    name_elem = soup.find(['h1', 'h2'], class_=lambda x: x and ('title' in x.lower() or 
                                                                  'heading' in x.lower() or
                                                                  'name' in x.lower()))
    if not name_elem:
        name_elem = soup.find('h1')
    if not name_elem:
        name_elem = soup.find('title')
    
    assessment_name = name_elem.get_text(strip=True) if name_elem else "Unknown Assessment"
    
    # Filter function to exclude browser compatibility messages
    def is_valid_text(text):
        """Check if text is not a browser compatibility message."""
        if not text or len(text.strip()) < 10:
            return False
        text_lower = text.lower()
        # Filter out browser compatibility messages
        invalid_phrases = [
            'outdated browser',
            'recommend upgrading',
            'modern browser',
            'cannot guarantee',
            'wish to continue',
            'latest browser',
            'browser options'
        ]
        return not any(phrase in text_lower for phrase in invalid_phrases)
    
    # Helper function to extract text after a heading
    def extract_after_heading(heading_text):
        """Find text content after a specific heading."""
        # Find all headings and text elements
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b', 'dt'])
        for heading in headings:
            heading_text_lower = heading.get_text().strip().lower()
            if heading_text.lower() in heading_text_lower:
                # Strategy 1: Get the next sibling element
                next_elem = heading.find_next_sibling()
                if next_elem:
                    text = next_elem.get_text(strip=True)
                    if is_valid_text(text) and len(text) > 5:
                        return text
                
                # Strategy 2: Get the next element (could be a div, p, dd, etc.)
                next_elem = heading.find_next(['p', 'div', 'dd', 'li', 'span'])
                if next_elem:
                    text = next_elem.get_text(strip=True)
                    if is_valid_text(text) and len(text) > 5:
                        return text
                
                # Strategy 3: Get parent's next sibling
                parent = heading.parent
                if parent:
                    next_sibling = parent.find_next_sibling()
                    if next_sibling:
                        text = next_sibling.get_text(strip=True)
                        if is_valid_text(text) and len(text) > 5:
                            return text
                    
                    # Strategy 4: Get text from the same parent (after the heading)
                    parent_text = parent.get_text(strip=True)
                    if parent_text:
                        # Extract text after the heading
                        heading_match = heading.get_text().strip()
                        if heading_match in parent_text:
                            parts = parent_text.split(heading_match, 1)
                            if len(parts) > 1:
                                text = parts[1].strip()
                                # Clean up: take first line or first sentence
                                text = text.split('\n')[0].strip()
                                text = text.split('.')[0].strip() if '.' in text else text
                                if is_valid_text(text) and len(text) > 5:
                                    return text
        
        # Strategy 5: Search in all text for the heading pattern
        all_text = soup.get_text()
        if heading_text in all_text:
            parts = all_text.split(heading_text, 1)
            if len(parts) > 1:
                # Get the text after the heading (first line or first sentence)
                next_part = parts[1].strip()
                # Take first line
                first_line = next_part.split('\n')[0].strip()
                # Or take first sentence if it's shorter
                if '.' in first_line:
                    first_sentence = first_line.split('.')[0].strip()
                    if len(first_sentence) < len(first_line) and len(first_sentence) > 5:
                        first_line = first_sentence
                if is_valid_text(first_line) and len(first_line) > 5:
                    return first_line
        
        return None
    
    # Extract description - prioritize finding "Description" heading
    assessment_description = ""
    
    # Strategy 1: Look for "Description" heading
    desc_from_heading = extract_after_heading("Description")
    if desc_from_heading and is_valid_text(desc_from_heading):
        assessment_description = desc_from_heading
    
    # Strategy 2: Try meta description tag
    if not assessment_description or not is_valid_text(assessment_description):
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            assessment_description = meta_desc.get('content', '').strip()
            if not is_valid_text(assessment_description):
                assessment_description = ""
    
    # Strategy 3: Try to find main content area
    if not assessment_description or not is_valid_text(assessment_description):
        # Look for main content containers
        main_content = soup.find(['main', 'article', 'div'], 
                                class_=lambda x: x and ('content' in x.lower() or 
                                                       'main' in x.lower() or
                                                       'body' in x.lower() or
                                                       'article' in x.lower()))
        if main_content:
            # Get all paragraphs from main content
            paragraphs = main_content.find_all('p')
            valid_paragraphs = [p.get_text(strip=True) for p in paragraphs if is_valid_text(p.get_text(strip=True))]
            if valid_paragraphs:
                # Take first few valid paragraphs
                assessment_description = ' '.join(valid_paragraphs[:3])
    
    # Strategy 4: Find all paragraphs and filter
    if not assessment_description or not is_valid_text(assessment_description):
        all_paragraphs = soup.find_all('p')
        for p in all_paragraphs:
            text = p.get_text(strip=True)
            if is_valid_text(text) and len(text) > 50:  # Minimum length
                assessment_description = text
                break
    
    # Final cleanup
    if assessment_description:
        # Remove extra whitespace
        assessment_description = ' '.join(assessment_description.split())
        # Limit length (keep first 1000 characters if too long)
        if len(assessment_description) > 1000:
            assessment_description = assessment_description[:1000] + "..."
    else:
        assessment_description = "Description not available"
    
    # Extract Job levels
    job_levels = ""
    job_levels_text = extract_after_heading("Job levels")
    if job_levels_text:
        job_levels = job_levels_text.strip()
    else:
        # Try alternative: look for text containing "Job levels"
        all_text = soup.get_text()
        if "Job levels" in all_text:
            # Extract text after "Job levels"
            parts = all_text.split("Job levels", 1)
            if len(parts) > 1:
                next_part = parts[1].split("\n", 1)[0].strip()
                if is_valid_text(next_part) and len(next_part) < 500:
                    job_levels = next_part
    
    # Extract Languages
    languages = ""
    languages_text = extract_after_heading("Languages")
    if languages_text:
        languages = languages_text.strip()
    else:
        # Try alternative: look for text containing "Languages"
        all_text = soup.get_text()
        if "Languages" in all_text:
            # Extract text after "Languages"
            parts = all_text.split("Languages", 1)
            if len(parts) > 1:
                next_part = parts[1].split("\n", 1)[0].strip()
                if is_valid_text(next_part) and len(next_part) < 500:
                    languages = next_part
    
    # Extract Assessment length
    assessment_length = ""
    length_text = extract_after_heading("Assessment length")
    if length_text:
        assessment_length = length_text.strip()
    else:
        # Try alternative: look for text containing "Assessment length" or "Completion Time"
        all_text = soup.get_text()
        if "Assessment length" in all_text:
            parts = all_text.split("Assessment length", 1)
            if len(parts) > 1:
                next_part = parts[1].split("\n", 1)[0].strip()
                if is_valid_text(next_part) and len(next_part) < 200:
                    assessment_length = next_part
        elif "Completion Time" in all_text or "completion time" in all_text:
            parts = all_text.split("Completion Time", 1) if "Completion Time" in all_text else all_text.split("completion time", 1)
            if len(parts) > 1:
                next_part = parts[1].split("\n", 1)[0].strip()
                if is_valid_text(next_part) and len(next_part) < 200:
                    assessment_length = next_part
    
    # Extract assessment type/category
    # Try to find category/type information
    type_elem = soup.find(['span', 'div', 'p'], 
                         class_=lambda x: x and ('type' in x.lower() or 
                                                'category' in x.lower() or
                                                'tag' in x.lower() or
                                                'classification' in x.lower()))
    if not type_elem:
        # Try to infer from breadcrumbs or navigation
        breadcrumb = soup.find(['nav', 'div'], class_=lambda x: x and 'breadcrumb' in x.lower())
        if breadcrumb:
            type_elem = breadcrumb.find('a')
    
    assessment_type = type_elem.get_text(strip=True) if type_elem else "General"
    
    # If type is still "General", try to infer from URL or page content
    if assessment_type == "General":
        # Get text from main content area (avoiding browser messages)
        main_content = soup.find(['main', 'article', 'div'], 
                                class_=lambda x: x and ('content' in x.lower() or 
                                                       'main' in x.lower() or
                                                       'body' in x.lower()))
        if main_content:
            page_text = main_content.get_text().lower()
        else:
            page_text = soup.get_text().lower()
        
        # Filter out browser messages
        if is_valid_text(page_text):
            if 'personality' in page_text or 'behavior' in page_text:
                assessment_type = "Personality & Behavior"
            elif 'skill' in page_text or 'knowledge' in page_text or 'cognitive' in page_text:
                assessment_type = "Knowledge & Skills"
            elif 'situational' in page_text:
                assessment_type = "Situational Judgment"
    
    return {
        'assessment_name': assessment_name,
        'assessment_url': url,
        'assessment_description': assessment_description,
        'assessment_type': assessment_type,
        'job_levels': job_levels,
        'languages': languages,
        'assessment_length': assessment_length
    }


def scrape_shl_assessments():
    """
    Read assessment URLs from Excel file and scrape each page.
    
    Returns:
        pd.DataFrame: DataFrame containing assessment information
    """
    excel_path = 'Gen_AI_Dataset.xlsx'
    
    if not os.path.exists(excel_path):
        print(f"Error: {excel_path} not found.")
        return pd.DataFrame()
    
    print(f"Reading Excel file: {excel_path}")
    
    # Read Excel file
    try:
        df_excel = pd.read_excel(excel_path)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return pd.DataFrame()
    
    # Check if required columns exist (case-insensitive)
    url_column = None
    for col in df_excel.columns:
        if 'assessment' in col.lower() and 'url' in col.lower():
            url_column = col
            break
    
    if url_column is None:
        print("Error: 'Assessment_url' column not found in Excel file.")
        print(f"Available columns: {df_excel.columns.tolist()}")
        return pd.DataFrame()
    
    print(f"Found {len(df_excel)} rows in Excel file.")
    print(f"Using column: '{url_column}'")
    
    # Get unique assessment URLs
    unique_urls = df_excel[url_column].dropna().unique()
    print(f"Found {len(unique_urls)} unique assessment URLs.")
    
    # Scrape each assessment page
    assessments = []
    for url in tqdm(unique_urls, desc="Scraping assessments", unit="assessment"):
        # Ensure URL is complete
        if not url.startswith('http'):
            url = f"https://www.shl.com{url}" if url.startswith('/') else f"https://www.shl.com/{url}"
        
        # Skip pre-packaged job solutions (as per requirements)
        url_lower = url.lower()
        if 'pre-packaged' in url_lower or 'job-solution' in url_lower or 'job_solution' in url_lower:
            tqdm.write(f"Skipping pre-packaged job solution: {url}")
            continue
        
        assessment_data = scrape_assessment_page(url)
        
        if assessment_data:
            # Additional check: skip if it's a pre-packaged solution based on name/description
            name_lower = assessment_data.get('assessment_name', '').lower()
            desc_lower = assessment_data.get('assessment_description', '').lower()
            if 'pre-packaged' in name_lower or 'pre-packaged' in desc_lower:
                tqdm.write(f"Skipping pre-packaged job solution: {assessment_data.get('assessment_name')}")
                continue
            
            assessments.append(assessment_data)
        else:
            tqdm.write(f"Failed to scrape: {url}")
    
    # Create DataFrame
    df = pd.DataFrame(assessments)
    
    # Remove duplicates based on URL
    df = df.drop_duplicates(subset=['assessment_url'], keep='first')
    
    return df


def main():
    """Main function to run the scraper and save results."""
    print("Starting SHL assessment scraper...")
    
    # Scrape assessments
    df = scrape_shl_assessments()
    
    if df.empty:
        print("Warning: No assessments found. The website structure may have changed.")
        print("Please check the website and update the scraper selectors accordingly.")
    else:
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Save to CSV
        output_path = 'data/shl_assessments.csv'
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"\nScraping complete. Found {len(df)} assessments.")
        print(f"Data saved to: {output_path}")
        print(f"\nSample data:")
        print(df.head())


if __name__ == "__main__":
    main()

