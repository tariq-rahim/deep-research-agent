# file: deep_research_agent.py
import os
import json
import re
from typing import List, Dict, TypedDict, Optional

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from langgraph.graph import StateGraph, END, START
from langchain_groq import ChatGroq
import streamlit as st
import vector_utils
from serper_groq_agent import search_web
from site_scraper import scrape_url

# --- 1. Agent State Definition (Fixed) ---
class ResearchState(TypedDict):
    query: str
    search_results: List[Dict]
    scraped_content: List[Dict]
    knowledge_base_results: List[str]
    final_synthesis: Dict
    error: Optional[str]  # Made optional to prevent KeyError

# --- 2. LLM and KB Initialization (Fixed) ---
def get_llm():
    """
    Initializes and returns the Groq LLM.
    Removed caching to avoid Streamlit context issues.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("Error: GROQ_API_KEY not found in environment variables")
        return None
    
    try:
        llm = ChatGroq(
            model="llama3-70b-8192",
            api_key=groq_api_key,
            temperature=0.1,
            max_tokens=4096,
        )
        # Test the connection
        test_response = llm.invoke("Hello")
        print("✅ LLM initialized and tested successfully")
        return llm
    except Exception as e:
        print(f"❌ Error initializing LLM: {e}")
        return None

def get_knowledge_base():
    """Initializes and returns the ChromaDB collection."""
    try:
        return vector_utils.get_or_create_collection("deep_research")
    except Exception as e:
        print(f"❌ Error getting knowledge base: {e}")
        return None

# --- 3. Graph Nodes (Fixed with proper state management) ---
def search_node(state: ResearchState) -> ResearchState:
    """Web search node with improved error handling"""
    print("--- 🌐 Performing web search... ---")
    
    # Initialize state if needed
    new_state = dict(state)  # Create a copy to avoid mutation issues
    
    try:
        if new_state.get("error"):
            print(f"⚠️ Skipping search due to previous error: {new_state['error']}")
            return new_state
        
        query = new_state.get("query", "")
        if not query:
            error_msg = "No query provided for search"
            print(f"❌ {error_msg}")
            new_state["error"] = error_msg
            return new_state
        
        results = search_web(query, num_results=5)
        new_state["search_results"] = results
        print(f"✅ Found {len(results)} search results")
        
    except Exception as e:
        error_msg = f"Web search failed: {str(e)}"
        print(f"❌ {error_msg}")
        new_state["error"] = error_msg
        new_state["search_results"] = []
    
    return new_state

def knowledge_base_node(state: ResearchState) -> ResearchState:
    """Knowledge base query node with improved error handling"""
    print("--- 📚 Querying knowledge base... ---")
    
    new_state = dict(state)
    
    try:
        if new_state.get("error"):
            print(f"⚠️ Skipping KB query due to previous error: {new_state['error']}")
            return new_state
        
        research_collection = get_knowledge_base()
        if not research_collection:
            print("⚠️ Knowledge base not available")
            new_state["knowledge_base_results"] = []
            return new_state
        
        query = new_state.get("query", "")
        if not query:
            print("⚠️ No query for KB search")
            new_state["knowledge_base_results"] = []
            return new_state
        
        kb_results = vector_utils.query_knowledge_base(query, research_collection, n_results=3)
        new_state["knowledge_base_results"] = kb_results
        print(f"✅ Found {len(kb_results)} KB results")
        
    except Exception as e:
        error_msg = f"Knowledge base query failed: {str(e)}"
        print(f"❌ {error_msg}")
        new_state["knowledge_base_results"] = []
        # Don't set error here, continue with other sources
    
    return new_state

def scrape_node(state: ResearchState) -> ResearchState:
    """Web scraping node with improved error handling"""
    print("--- 📄 Scraping web content... ---")
    
    new_state = dict(state)
    
    try:
        if new_state.get("error"):
            print(f"⚠️ Skipping scraping due to previous error: {new_state['error']}")
            return new_state
        
        scraped_data = []
        search_results = new_state.get("search_results", [])
        
        if not search_results:
            print("⚠️ No search results to scrape")
            new_state["scraped_content"] = []
            return new_state
        
        # Get unique URLs from search results
        urls = []
        for result in search_results:
            if isinstance(result, dict) and result.get("link"):
                url = result["link"]
                if url not in urls and url.startswith(('http://', 'https://')):
                    urls.append(url)
        
        print(f"🔍 Attempting to scrape {len(urls)} URLs")
        
        for i, url in enumerate(urls[:3]):  # Limit to first 3 URLs
            try:
                print(f"📄 Scraping {i+1}/{min(3, len(urls))}: {url}")
                content = scrape_url(url)
                if content and len(content.strip()) > 50:
                    scraped_data.append({
                        "url": url,
                        "content": content[:2000]  # Limit content length
                    })
                    print(f"✅ Successfully scraped: {url[:50]}...")
                else:
                    print(f"⚠️ No meaningful content from: {url[:50]}...")
            except Exception as scrape_error:
                print(f"❌ Failed to scrape {url}: {scrape_error}")
                continue
        
        new_state["scraped_content"] = scraped_data
        print(f"✅ Successfully scraped {len(scraped_data)} pages")
        
    except Exception as e:
        error_msg = f"Scraping failed: {str(e)}"
        print(f"❌ {error_msg}")
        new_state["scraped_content"] = []
        # Don't set error here, continue with synthesis
    
    return new_state

def synthesis_node(state: ResearchState) -> ResearchState:
    """Synthesis node with improved error handling and structured output"""
    print("--- 🧠 Synthesizing report... ---")
    
    new_state = dict(state)
    
    try:
        # Check if we have any data to synthesize
        search_results = new_state.get("search_results", [])
        scraped_content = new_state.get("scraped_content", [])
        kb_results = new_state.get("knowledge_base_results", [])
        
        if not any([search_results, scraped_content, kb_results]):
            error_msg = "No data available for synthesis"
            print(f"❌ {error_msg}")
            new_state["error"] = error_msg
            new_state["final_synthesis"] = {"error": error_msg}
            return new_state

        llm = get_llm()
        if not llm:
            error_msg = "LLM not available for synthesis"
            print(f"❌ {error_msg}")
            new_state["error"] = error_msg
            new_state["final_synthesis"] = {"error": error_msg}
            return new_state

        query = new_state.get("query", "Unknown query")
        
        # Prepare structured content
        content_sections = []
        
        # Knowledge Base Section
        if kb_results:
            content_sections.append("=== KNOWLEDGE BASE RESULTS ===")
            for i, kb_result in enumerate(kb_results[:3], 1):
                content_sections.append(f"KB Result {i}: {kb_result[:800]}...")
        
        # Web Search Section
        if search_results:
            content_sections.append("\n=== WEB SEARCH RESULTS ===")
            for i, result in enumerate(search_results[:5], 1):
                title = result.get('title', 'No title')
                snippet = result.get('snippet', 'No snippet')
                link = result.get('link', 'No link')
                content_sections.append(f"Result {i}: {title}\nSnippet: {snippet}\nURL: {link}")
        
        # Scraped Content Section
        if scraped_content:
            content_sections.append("\n=== SCRAPED CONTENT ===")
            for i, content in enumerate(scraped_content[:3], 1):
                url = content.get('url', 'Unknown')
                text = content.get('content', 'No content')[:1000]
                content_sections.append(f"Source {i} ({url}): {text}...")
        
        combined_content = "\n\n".join(content_sections)
        
        # Create synthesis prompt
        synthesis_prompt = f"""You are an expert research analyst. Analyze the following research data and create a comprehensive report.

RESEARCH QUERY: {query}

AVAILABLE DATA:
{combined_content}

Create a structured JSON response with these exact keys:
{{
    "summary": "A comprehensive 2-3 sentence executive summary addressing the research query",
    "findings": [
        {{
            "title": "Key Finding Title",
            "description": "2-3 sentences explaining this finding",
            "evidence": ["source1", "source2"]
        }}
    ]
}}

Requirements:
- Focus specifically on the research query
- Include 3-5 key findings
- Base findings on the provided data
- For evidence, use actual URLs when available, or "Knowledge Base" for internal sources
- Ensure valid JSON format
- No markdown formatting or code blocks"""
        
        print("🤖 Generating synthesis...")
        response = llm.invoke(synthesis_prompt)
        content = getattr(response, "content", str(response))
        
        # Clean and parse JSON
        cleaned_content = content.strip()
        if cleaned_content.startswith("```"):
            cleaned_content = re.sub(r"```(?:json)?\s*", "", cleaned_content)
            cleaned_content = re.sub(r"\s*```$", "", cleaned_content)
        
        # Attempt JSON parsing
        try:
            synthesis_result = json.loads(cleaned_content)
            print("✅ Successfully parsed synthesis JSON")
            new_state["final_synthesis"] = synthesis_result
            
        except json.JSONDecodeError as json_err:
            print(f"⚠️ JSON parsing failed: {json_err}")
            print(f"Raw content preview: {cleaned_content[:200]}...")
            
            # Create fallback structured result
            fallback_result = {
                "summary": f"Research analysis completed for: {query}. Data was gathered from {len(search_results)} web sources, {len(scraped_content)} scraped pages, and {len(kb_results)} knowledge base entries.",
                "findings": []
            }
            
            # Try to extract some basic findings
            if kb_results:
                fallback_result["findings"].append({
                    "title": "Knowledge Base Analysis",
                    "description": "Relevant information found in the internal knowledge base.",
                    "evidence": ["Knowledge Base"]
                })
            
            if search_results:
                fallback_result["findings"].append({
                    "title": "Web Research Results",
                    "description": f"Found {len(search_results)} relevant web sources with current information.",
                    "evidence": [r.get('link', 'Unknown') for r in search_results[:3]]
                })
            
            if scraped_content:
                fallback_result["findings"].append({
                    "title": "Detailed Content Analysis",
                    "description": f"Successfully extracted detailed content from {len(scraped_content)} web sources.",
                    "evidence": [c.get('url', 'Unknown') for c in scraped_content]
                })
            
            new_state["final_synthesis"] = fallback_result
            print("✅ Using fallback synthesis structure")
            
    except Exception as e:
        error_msg = f"Synthesis failed: {str(e)}"
        print(f"❌ {error_msg}")
        new_state["error"] = error_msg
        new_state["final_synthesis"] = {
            "summary": f"Research synthesis encountered an error: {error_msg}",
            "findings": []
        }
    
    return new_state

# --- 4. Build and Compile the Graph (Fixed) ---
def create_research_workflow():
    """Creates and compiles the LangGraph research workflow with proper state management"""
    try:
        print("🛠️ Creating research workflow...")
        
        # Create the workflow graph
        workflow = StateGraph(ResearchState)
        
        # Add nodes
        workflow.add_node("search", search_node)
        workflow.add_node("query_kb", knowledge_base_node)
        workflow.add_node("scrape", scrape_node)
        workflow.add_node("synthesis", synthesis_node)
        
        # Define the execution flow
        workflow.add_edge(START, "search")
        workflow.add_edge("search", "query_kb")
        workflow.add_edge("query_kb", "scrape")
        workflow.add_edge("scrape", "synthesis")
        workflow.add_edge("synthesis", END)
        
        # Compile the workflow
        app = workflow.compile()
        print("✅ Research workflow compiled successfully")
        return app
        
    except Exception as e:
        print(f"❌ Failed to create workflow: {e}")
        raise e

# # --- 5. Utility Functions ---
# def validate_research_input(query: str) -> bool:
#     """Validate research input"""
#     if not query or not query.strip():
#         return False
#     if len(query.strip()) < 3:
#         return False
#     return True

# def format_research_results(final_state: dict) -> dict:
#     """Format research results for display"""
#     if not final_state:
#         return {"error": "No results available"}
    
#     formatted = {
#         "query": final_state.get("query", "Unknown"),
#         "search_results_count": len(final_state.get("search_results", [])),
#         "scraped_content_count": len(final_state.get("scraped_content", [])),
#         "kb_results_count": len(final_state.get("knowledge_base_results", [])),
#         "synthesis": final_state.get("final_synthesis", {}),
#         "error": final_state.get("error")
#     }
    
#     return formatted
