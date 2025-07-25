# file: site_scraper.py
import httpx
from bs4 import BeautifulSoup

def is_probable_pdf(url: str, headers: dict) -> bool:
    """Check if URL is likely a PDF file."""
    if url.lower().split("?")[0].endswith(".pdf"):
        return True
    content_type = headers.get("content-type", "").lower()
    if "pdf" in content_type:
        return True
    return False

def scrape_url(url: str, max_chars: int = 5000) -> str:
    """
    Scrapes text from a URL. Returns an empty string on failure.
    UI-agnostic: No Streamlit calls here.
    """
    if not url or not url.startswith(('http://', 'https://')):
        print(f"Warning: Invalid URL provided to scraper: {url}")
        return ""

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        with httpx.Client(timeout=15.0, follow_redirects=True, headers=headers) as client:
            # Using a single GET request for simplicity
            resp = client.get(url)
            resp.raise_for_status()

            if is_probable_pdf(url, resp.headers):
                print(f"Info: Skipping PDF at {url}")
                return f"[Content is a PDF and was not parsed] URL: {url}"

            soup = BeautifulSoup(resp.text, 'html.parser')

            for element in soup(["script", "style", "nav", "footer", "aside", "header"]):
                element.decompose()

            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)

            if len(clean_text.strip()) < 50:
                print(f"Warning: Very little content extracted from {url}")

            return clean_text[:max_chars]

    except httpx.HTTPStatusError as e:
        print(f"Scraper Error: HTTP {e.response.status_code} for {url}")
        return ""
    except httpx.RequestError as e:
        print(f"Scraper Error: Request failed for {url}. Reason: {e}")
        return ""
    except Exception as e:
        print(f"Scraper Error: An unexpected error occurred for {url}. Reason: {e}")
        return ""
