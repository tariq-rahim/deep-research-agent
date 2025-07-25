import re
import requests
from bs4 import BeautifulSoup
import streamlit as st
from typing import Dict, Any, Optional, List
import time

def scrape_linkedin_profile(
    url: str,
    mode: str = "stub",
    html: Optional[str] = None,
    cache: bool = False
) -> Dict[str, Any]:
    """
    Scrape LinkedIn profile data with various modes.
    
    Args:
        url: LinkedIn profile/company URL
        mode: "stub", "static", "playwright", "html", "cached"
        html: Pre-fetched HTML content
        cache: Whether to use caching (placeholder)
    
    Returns:
        Dictionary with profile data
    """
    
    if mode == "stub":
        return _create_stub_linkedin_profile(url)
    elif mode == "static":
        return _scrape_linkedin_static(url)
    elif mode == "html" and html:
        return _parse_linkedin_html(html, url)
    elif mode == "playwright":
        st.warning("Playwright mode not implemented - falling back to stub")
        return _create_stub_linkedin_profile(url)
    elif mode == "cached":
        st.info("Cache mode not implemented - falling back to stub")
        return _create_stub_linkedin_profile(url)
    else:
        return _create_stub_linkedin_profile(url)

def _create_stub_linkedin_profile(url: str) -> Dict[str, Any]:
    """Create a stub LinkedIn profile for demonstration purposes"""
    
    # Determine if it's a company or person profile
    is_company = "/company/" in url.lower()
    
    if is_company:
        # Extract company name from URL
        company_match = re.search(r'/company/([^/?]+)', url)
        company_name = company_match.group(1).replace('-', ' ').title() if company_match else "Unknown Company"
        
        return {
            "entity_type": "company",
            "name": company_name,
            "url": url,
            "description": f"A leading technology company focused on innovation and growth.",
            "industry": "Technology",
            "employees_range": "1,000-5,000",
            "headquarters": "San Francisco, CA",
            "founded": "2010",
            "specialties": ["Artificial Intelligence", "Software Development", "Innovation"],
            "website": f"https://www.{company_name.lower().replace(' ', '')}.com",
            "followers": "50,000+",
            "scrape_mode": "stub",
            "scrape_timestamp": time.time()
        }
    else:
        # Extract person name from URL (rough approximation)
        person_match = re.search(r'/in/([^/?]+)', url)
        person_slug = person_match.group(1) if person_match else "unknown-person"
        person_name = person_slug.replace('-', ' ').title()
        
        return {
            "entity_type": "person",
            "name": person_name,
            "url": url,
            "headline": "Technology Professional | AI Enthusiast",
            "summary": f"{person_name} is an experienced professional in the technology sector with expertise in artificial intelligence and software development.",
            "location": "San Francisco Bay Area",
            "connections": "500+",
            "experiences": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "date_range": "2020 - Present",
                    "description": "Leading AI initiatives and software development projects."
                },
                {
                    "title": "Software Engineer",
                    "company": "StartupXYZ",
                    "date_range": "2018 - 2020",
                    "description": "Developed scalable web applications and machine learning models."
                }
            ],
            "education": [
                {
                    "school": "Stanford University",
                    "degree": "Master of Science",
                    "field": "Computer Science",
                    "date_range": "2016 - 2018"
                }
            ],
            "skills": ["Python", "Machine Learning", "Artificial Intelligence", "Software Development"],
            "scrape_mode": "stub",
            "scrape_timestamp": time.time()
        }

def _scrape_linkedin_static(url: str) -> Dict[str, Any]:
    """
    Attempt static scraping of LinkedIn (limited due to anti-scraping measures)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to extract basic information
        profile_data = _parse_linkedin_html(response.text, url)
        profile_data["scrape_mode"] = "static"
        
        return profile_data
        
    except requests.exceptions.RequestException as e:
        st.warning(f"Static scraping failed: {e}. Falling back to stub.")
        return _create_stub_linkedin_profile(url)
    except Exception as e:
        st.error(f"Unexpected error in static scraping: {e}. Falling back to stub.")
        return _create_stub_linkedin_profile(url)

def _parse_linkedin_html(html: str, url: str) -> Dict[str, Any]:
    """
    Parse LinkedIn HTML content to extract profile information
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # This is a simplified parser - LinkedIn's actual structure is complex
    # and frequently changes to prevent scraping
    
    is_company = "/company/" in url.lower()
    
    if is_company:
        # Try to extract company information
        name = _extract_text_safe(soup, 'h1') or "Unknown Company"
        description = _extract_text_safe(soup, '.org-top-card__summary') or "Company description not available"
        
        return {
            "entity_type": "company",
            "name": name,
            "url": url,
            "description": description,
            "industry": "Technology",  # Default fallback
            "scrape_mode": "html_parsed",
            "scrape_timestamp": time.time()
        }
    else:
        # Try to extract person information
        name = _extract_text_safe(soup, 'h1') or "Unknown Person"
        headline = _extract_text_safe(soup, '.text-body-medium') or "Professional"
        
        return {
            "entity_type": "person",
            "name": name,
            "url": url,
            "headline": headline,
            "summary": f"Professional profile for {name}",
            "scrape_mode": "html_parsed",
            "scrape_timestamp": time.time()
        }

def _extract_text_safe(soup: BeautifulSoup, selector: str) -> Optional[str]:
    """Safely extract text from soup using CSS selector"""
    try:
        element = soup.select_one(selector)
        return element.get_text(strip=True) if element else None
    except:
        return None

def validate_linkedin_url(url: str) -> bool:
    """Validate if URL is a proper LinkedIn profile/company URL"""
    if not url:
        return False
    
    url_lower = url.lower()
    return (
        "linkedin.com" in url_lower and
        ("/in/" in url_lower or "/company/" in url_lower)
    )

def get_linkedin_entity_type(url: str) -> str:
    """Determine if LinkedIn URL is for a person or company"""
    if "/company/" in url.lower():
        return "company"
    elif "/in/" in url.lower():
        return "person"
    else:
        return "unknown"

# Test function
def test_linkedin_scraper():
    """Test the LinkedIn scraper with sample URLs"""
    st.subheader("LinkedIn Scraper Test")
    
    test_urls = [
        "https://www.linkedin.com/company/openai/",
        "https://www.linkedin.com/in/sample-person/"
    ]
    
    for url in test_urls:
        st.write(f"Testing: {url}")
        
        if validate_linkedin_url(url):
            entity_type = get_linkedin_entity_type(url)
            st.write(f"Entity type: {entity_type}")
            
            result = scrape_linkedin_profile(url, mode="stub")
            st.json(result)
        else:
            st.error(f"Invalid LinkedIn URL: {url}")
        
        st.markdown("---")

if __name__ == "__main__":
    # Test the scraper
    test_url = "https://www.linkedin.com/company/openai/"
    result = scrape_linkedin_profile(test_url, mode="stub")
    print("Test result:")
    print(result)
