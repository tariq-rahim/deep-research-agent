import os
import requests
import streamlit as st
from typing import List, Dict

def search_web(query: str, num_results: int = 5) -> List[Dict]:
    """
    Search the web using Serper API
    Returns a list of search results with title, link, and snippet
    """
    serper_api_key = os.getenv("SERPER_API_KEY")
    
    if not serper_api_key:
        st.error("SERPER_API_KEY not found in environment variables")
        return []
    
    url = "https://google.serper.dev/search"
    
    payload = {
        "q": query,
        "num": num_results,
        "gl": "us",  # Country
        "hl": "en"   # Language
    }
    
    headers = {
        "X-API-KEY": serper_api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract organic results
        results = []
        organic_results = data.get("organic", [])
        
        for item in organic_results[:num_results]:
            result = {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "position": item.get("position", 0)
            }
            results.append(result)
        
        st.success(f"Found {len(results)} search results for: {query}")
        return results
        
    except requests.exceptions.Timeout:
        st.error("Search request timed out")
        return []
    
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error during search: {e}")
        return []
    
    except requests.exceptions.RequestException as e:
        st.error(f"Request error during search: {e}")
        return []
    
    except KeyError as e:
        st.error(f"Unexpected response format from search API: {e}")
        return []
    
    except Exception as e:
        st.error(f"Unexpected error during search: {e}")
        return []

def test_search():
    """Test function for the search functionality"""
    st.subheader("Web Search Test")
    
    test_query = st.text_input("Enter a test query:", "artificial intelligence news")
    
    if st.button("Test Search"):
        if test_query:
            with st.spinner("Searching..."):
                results = search_web(test_query, num_results=3)
                
            if results:
                st.success(f"Found {len(results)} results")
                for i, result in enumerate(results, 1):
                    with st.expander(f"Result {i}: {result['title']}"):
                        st.write(f"**Link:** {result['link']}")
                        st.write(f"**Snippet:** {result['snippet']}")
            else:
                st.error("No results found or search failed")
        else:
            st.warning("Please enter a search query")

def deep_research(query: str) -> str:
    """
    Perform a quick research summary using Serper API and LLM
    """
    try:
        # Get search results
        search_results = search_web(query, num_results=5)
        
        if not search_results:
            return f"Unable to find information about: {query}"
        
        # Format search results for LLM
        context = "\n\n".join([
            f"Title: {result['title']}\nSnippet: {result['snippet']}\nSource: {result['link']}"
            for result in search_results
        ])
        
        # Create a simple summary (you can enhance this with actual LLM integration)
        summary_parts = [
            f"Quick research summary for: {query}\n",
            "Based on recent web sources:\n"
        ]
        
        for i, result in enumerate(search_results[:3], 1):
            summary_parts.append(f"{i}. {result['title']}")
            summary_parts.append(f"   {result['snippet']}")
            summary_parts.append("")
        
        summary_parts.append("Sources:")
        for result in search_results:
            summary_parts.append(f"- {result['link']}")
        
        return "\n".join(summary_parts)
        
    except Exception as e:
        st.error(f"Deep research failed: {e}")
        return f"Research failed for query: {query}"

def search_company_openweb(company_name: str, num_results: int = 5) -> List[Dict]:
    """
    Search for company information on the open web
    """
    # Create a more specific query for company information
    query = f"{company_name} company information news recent"
    
    return search_web(query, num_results=num_results)

# if __name__ == "__main__":
#     # For testing purposes
#     test_query = "climate change impact"
#     results = search_web(test_query)
    
#     print(f"Search results for '{test_query}':")
#     for i, result in enumerate(results, 1):
#         print(f"{i}. {result['title']}")
#         print(f"   {result['link']}")
#         print(f"   {result['snippet']}")
#         print()
    
#     # Test deep research
#     print("\n" + "="*50)
#     print("Testing deep research:")
#     deep_summary = deep_research("artificial intelligence")
#     print(deep_summary)
