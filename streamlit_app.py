# file: streamlit_app.py
import os
import json
import streamlit as st
import traceback
import time

# Set page config first
st.set_page_config(
    page_title="Deep Research Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

#Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import modules with error handling
try:
    import vector_utils
    import site_scraper
    import linkedin_scraper
    # Import our corrected agent functions
    from deep_research_agent import create_research_workflow, get_llm
    from serper_groq_agent import search_web
except ImportError as e:
    st.error(f"❌ Import error: {e}. Please ensure all .py files are in the same directory.")
    st.stop()

# --- Session State Initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []
if "kb_initialized" not in st.session_state:
    st.session_state.kb_initialized = False

# --- Cached Resources ---
@st.cache_resource
def get_collection():
    """Get or create ChromaDB collection"""
    try:
        return vector_utils.get_or_create_collection("deep_research")
    except Exception as e:
        st.error(f"Failed to initialize collection: {e}")
        return None

def initialize_demo_kb():
    """Initialize Discoverer - REMOVED AUTO DEMO DATA"""
    if not st.session_state.kb_initialized:
        collection = get_collection()
        if collection is None:
            st.error("Failed to initialize Discoverer")
            return
            
        try:
            # Just mark as initialized, don't add demo data automatically
            st.session_state.kb_initialized = True
            st.toast("Deep Research Agent - Ready to Launch!")
        except Exception as e:
            st.error(f"Failed to initialize KB: {e}")
################
# SECURE API KEYS
groq_key = os.environ["GROQ_API_KEY"]
serper_key=os.environ["SERPER_API_KEY"]

# --- Sidebar Configuration ---
# with st.sidebar:
#     st.header("⚙️ Configuration")
#     groq_key = st.text_input("Groq API Key", value=os.getenv("GROQ_API_KEY", ""), type="password", key="sidebar_groq_key")
#     serper_key = st.text_input("Serper API Key", value=os.getenv("SERPER_API_KEY", ""), type="password", key="sidebar_serper_key")

#     # Set environment variables if provided
#     if groq_key:
#         os.environ["GROQ_API_KEY"] = groq_key
#     if serper_key:
#         os.environ["SERPER_API_KEY"] = serper_key

#     if st.button("🔄 Clear Cache"):
#         st.cache_resource.clear()
#         st.success("Cache cleared!")
#         st.rerun()

# Uncessesary
    # st.markdown("### Status")
    # st.success("✅ Groq API Key set") if groq_key else st.error("❌ Groq API key required")
    # st.success("✅ Serper API Key set") if serper_key else st.error("❌ Serper API key required")

    # st.markdown("---")
    # st.markdown("### Settings")
    # linkedin_mode = st.selectbox("Scraping Mode", options=["stub", "static"], index=0)
######################   

# Initialize KB on first run
initialize_demo_kb()

# --- Main App Interface ---
st.title("🧠 Deep Research Agent")
st.markdown("Advanced AI-powered research agent.")

# Display KB status
collection = get_collection()
if collection:
    try:
        kb_stats = vector_utils.get_collection_stats(collection)
        st.info(f"📚 Discoverer: {kb_stats['document_count']} documents | Status: {kb_stats['status']}")
    except:
        st.info(f"📚 Discoverer: {collection.count()} documents | Status: Active")

tab1, tab2, tab3, tab4 = st.tabs(["🔍 Research", "🏢 Company Analysis", "📚 Discoverer", "💬 Chat"])

with tab1:
    st.subheader("Deep Research Tool")
    
    # Input section
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "Begin your investigation:",
            placeholder="Drop your query here",
            help="Be specific for better results",
            key="research_query_input"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True) 
        start_research = st.button("🔍 Let’s Discover", type="primary", use_container_width=True)
    
    if start_research:
        if not query.strip():
            st.error("Spark the search — type your question.")
        elif not groq_key or not serper_key:
            st.error("❌ Please provide both API keys in the sidebar.")
        else:
            # Validate LLM before starting research
            try:
                test_llm = get_llm()
                if not test_llm:
                    st.error("❌ Failed to initialize LLM. Please check your Groq API key.")
                else:
                    with st.status("🚀 Running deep research...", expanded=True) as status:
                        try:
                            # Create research workflow
                            research_app = create_research_workflow()
                            inputs = {"query": query}
                            
                            # Progress tracking
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            status_text.text("Initializing research workflow...")
                            progress_bar.progress(10)
                            
                            # Run the research workflow with error handling
                            try:
                                final_state = research_app.invoke(inputs)
                                progress_bar.progress(100)
                                
                                if final_state.get("error"):
                                    status.update(label="Research Failed!", state="error", expanded=True)
                                    st.error(f"Error in research pipeline: {final_state['error']}")
                                else:
                                    status.update(label="Research Complete!", state="complete")
                                    
                            except KeyError as ke:
                                st.error(f"❌ Configuration error: Missing required checkpoint data. This might be due to LangGraph state management issues.")
                                st.error(f"Technical details: {str(ke)}")
                                final_state = {"error": f"Checkpoint error: {str(ke)}"}
                            except Exception as workflow_error:
                                st.error(f"❌ Workflow execution error: {str(workflow_error)}")
                                st.error("This might be due to API connectivity or workflow configuration issues.")
                                final_state = {"error": f"Workflow error: {str(workflow_error)}"}

                            # Display results if successful
                            if final_state and not final_state.get("error"):
                                st.success("✅ Research completed successfully!")
                                
                                # Main report section
                                st.subheader("📊 Research Report")
                                report = final_state.get("final_synthesis", {})
                                
                                if report:
                                    # Executive Summary
                                    st.markdown("### Executive Summary")
                                    summary = report.get("summary", "No summary provided.")
                                    st.markdown(f"📋 {summary}")
                                    
                                    # Key Findings
                                    st.markdown("### Key Findings")
                                    findings = report.get("findings", [])
                                    
                                    if findings:
                                        for i, finding in enumerate(findings, 1):
                                            with st.expander(f"Finding {i}: {finding.get('title', 'Untitled')}", expanded=True):
                                                st.markdown(f"**Description:** {finding.get('description', 'No description provided.')}")
                                                
                                                evidence = finding.get('evidence', [])
                                                if evidence:
                                                    st.markdown("**Sources:**")
                                                    for source in evidence:
                                                        if source.startswith('http'):
                                                            st.markdown(f"- 🔗 [{source}]({source})")
                                                        else:
                                                            st.markdown(f"- 📚 {source}")
                                    else:
                                        st.info("No specific findings generated.")
                                
                                # Additional data sections
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    search_results = final_state.get("search_results", [])
                                    if search_results:
                                        with st.expander(f"🌐 Web Search Results ({len(search_results)})"):
                                            for result in search_results:
                                                st.markdown(f"**{result.get('title', 'No title')}**")
                                                st.markdown(f"🔗 {result.get('link', 'No link')}")
                                                st.markdown(f"📝 {result.get('snippet', 'No snippet')}")
                                                st.markdown("---")
                                
                                with col2:
                                    scraped_content = final_state.get("scraped_content", [])
                                    if scraped_content:
                                        with st.expander(f"📄 Scraped Content ({len(scraped_content)})"):
                                            for content in scraped_content:
                                                st.markdown(f"**Source:** {content.get('url', 'Unknown')}")
                                                st.markdown(f"**Content Preview:** {content.get('content', 'No content')[:200]}...")
                                                st.markdown("---")
                                
                                # Raw data for debugging
                                with st.expander("🔧 View Raw Research Data (Debug)"):
                                    st.json(final_state)
                            
                            # Clean up progress indicators
                            progress_bar.empty()
                            status_text.empty()
                            
                        except Exception as status_error:
                            status.update(label="Research Failed!", state="error", expanded=True)
                            st.error(f"❌ Status execution error: {str(status_error)}")
                            
            except Exception as e:
                st.error(f"❌ Critical error during research initialization: {str(e)}")
                with st.expander("View Full Error Details"):
                    st.code(traceback.format_exc())

# --- TAB 2 ---
with tab2:
    st.subheader("Analysis Dashboard")
    company_url = st.text_input("Company Website or Profile Link:", placeholder="Drop your query here", key="link/url_input")
    
    if st.button("🌐 Let's Discover", type="primary"):
        if not company_url.strip():
            st.error("Spark the search — drop your query.")
        elif not groq_key or not serper_key:
            st.error("Please provide API keys")
        else:
            with st.spinner("Analyzing..."):
                try:
                    company_data = linkedin_scraper.scrape_linkedin_profile(company_url.strip())
                    # company_data = linkedin_scraper.scrape_linkedin_profile(company_url.strip(), mode=linkedin_mode)
                    st.success("✅ Findings retrieved")
                    
                    # Company Overview
                    st.markdown("## Overview")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Name:** {company_data.get('name', 'N/A')}")
                        st.markdown(f"**Industry:** {company_data.get('industry', 'N/A')}")
                    with col2:
                        st.markdown(f"**Employees:** {company_data.get('employees_range', 'N/A')}")
                        st.markdown(f"**Website:** {company_data.get('website', 'N/A')}")
                    
                    if 'description' in company_data:
                        st.markdown("**Description:**")
                        st.markdown(company_data['description'])
                    
                    # Recent News
                    company_name = company_data.get('name', '')
                    if company_name:
                        st.markdown(f"## 📰 Recent News for {company_name}")
                        try:
                            news_results = search_web(f"{company_name} news and developments", num_results=5)
                            for result in news_results:
                                with st.expander(result['title']):
                                    st.markdown(f"🔗 **Source:** {result['link']}")
                                    st.markdown(f"📝 **Summary:** {result['snippet']}")
                        except Exception as news_error:
                            st.error(f"Failed to fetch news: {news_error}")
                            
                except Exception as e:
                    st.error(f"Company analysis failed: {e}")

# --- TAB 3 ---
with tab3:
    st.subheader("Discoverer")
    collection = get_collection()
    
    if collection:
        try:
            doc_count = collection.count()
            st.info(f"📚 Discoverer {doc_count} documents")
            
            # Show some sample sources if available
            if doc_count > 0:
                sample_data = collection.get(limit=1)
                sources = set()
                for meta in sample_data.get("metadatas", []):
                    if meta and "source" in meta:
                        sources.add(meta["source"])
                
                if sources:
                    st.write("**Current sources:**", ", ".join(list(sources)[:10]))
                    
        except Exception as e:
            st.error(f"Failed to get collection stats: {e}")
            doc_count = 0
    else:
        st.error("Discoverer not available")
        doc_count = 0
    
    # Add option to initialize with demo data
    st.markdown("#### initialize Discoverer")
    col1, col2, col3 = st.columns(3)
# type="primary", use_container_width=True
    with col1:
        if st.button("📚 Add Demo Data",type="primary") and collection:
            with st.spinner("Adding demo documents..."):
                try:
                    if vector_utils.initialize_with_sample_data(collection):
                        st.success("✅ Demo data added successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to add demo data")
                except Exception as e:
                    st.error(f"❌ Error adding demo data: {e}")
    
    with col2:
        if st.button("🗑️ Clear All Data",type="primary") and collection:
            if vector_utils.clear_collection(collection):
                st.success("✅ Discoverer cleared!!!")
                st.rerun()
            else:
                st.error("❌ Failed to clear DISCOVERER!!!")
    
    with col3:
        if st.button("🔄 Complete Reset"):
            with st.spinner("Completely resetting database..."):
                if vector_utils.completely_reset_database():
                    st.success("✅ Database completely reset!")
                    st.cache_resource.clear()  # Clear Streamlit cache
                    st.rerun()
                else:
                    st.error("❌ Failed to reset database")

    
    st.markdown("#### Upload Your Documents")
    uploaded_files = st.file_uploader("Upload .txt or .pdf files", type=["txt", "pdf"], accept_multiple_files=True)
    
    if st.button("📚 Add to Discoverer",type="primary") and uploaded_files and collection:
        with st.spinner("Processing and adding documents..."):
            success_count = 0
            for file in uploaded_files:
                try:
                    if file.type == "text/plain":
                        content = str(file.read(), "utf-8", errors='ignore')
                    elif file.type == "application/pdf":
                        # For PDF files, try to extract text
                        try:
                            import PyPDF2
                            import io
                            
                            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
                            content = ""
                            for page_num in range(len(pdf_reader.pages)):
                                page = pdf_reader.pages[page_num]
                                content += page.extract_text() + "\n"
                                
                        except ImportError:
                            st.warning(f"PyPDF2 not installed. Trying alternative method for {file.name}")
                            # Fallback: treat as binary and extract what we can
                            content = str(file.read(), "utf-8", errors='ignore')
                        except Exception as pdf_error:
                            st.warning(f"PDF extraction failed for {file.name}: {pdf_error}")
                            content = str(file.read(), "utf-8", errors='ignore')
                    else:
                        content = str(file.read(), "utf-8", errors='ignore')
                    
                    if content.strip():
                        # Add document with better processing
                        doc_ids = vector_utils.add_document_to_collection(content, file.name, collection)
                        if doc_ids:
                            st.success(f"✅ Added {file.name} ({len(doc_ids)} chunks)")
                            success_count += 1
                        else:
                            st.warning(f"⚠️ {file.name} was processed but may have limited content")
                    else:
                        st.warning(f"⚠️ {file.name} appears to be empty or unreadable")
                        
                except Exception as e:
                    st.error(f"❌ Failed to process {file.name}: {e}")
            
            if success_count > 0:
                st.success(f"✅ Successfully added {success_count} documents!")
                st.rerun()

    st.markdown("#### Ask Discoverer")
    kb_query = st.text_input("What would you like to find in the DISCOVERER?", key="kb_search_query")
    if st.button("🔍 Let's Discover",type="primary") and kb_query.strip() and collection:
        try:
            # Use the enhanced search function
            enhanced_results = vector_utils.search_similar_documents(kb_query, collection, n_results=1, include_metadata=True)
            
            if enhanced_results:
                st.markdown(f"**Found {len(enhanced_results)} results:**")
                for i, result in enumerate(enhanced_results, 1):
                    similarity_score = result.get("similarity_score", 0)
                    source = result.get("source", "Unknown")
                    content_preview = result.get("content", "")[:]
                    
                    with st.expander(f"Result {i} - {source} (Similarity: {similarity_score:.2f})"):
                        st.markdown(f"**Source:** {source}")
                        st.markdown(f"**Score:** {similarity_score:.3f}")
                        st.markdown(f"**Content:**")
                        st.write(content_preview + "..." if len(result.get("content", "")) > 300 else content_preview)
            else:
                st.info("No relevant results found in the Discoverer.")
                
                # Debug: Show what's actually in the KB
                if collection.count() > 0:
                    st.write("**Debug: Sample Discoverer content:**")
                    debug_info = vector_utils.debug_collection_contents(collection)
                    if debug_info:
                        st.write(f"Total documents: {debug_info['total_docs']}")
                        for i, doc in enumerate(debug_info['sample_docs']):
                            st.write(f"Document {i+1}: {doc[:100]}...")
                            
        except Exception as e:
            st.error(f"Discoverer search failed: {e}")
            
    # Add debug section
    # st.markdown("#### Debug Discoverer")
    # if st.button("🔍 Debug Collection Contents"):
    #     if collection:
    #         debug_info = vector_utils.debug_collection_contents(collection)
    #         if debug_info:
    #             st.write(f"**Total documents:** {debug_info['total_docs']}")
    #             st.write("**Sample documents:**")
    #             for i, doc in enumerate(debug_info['sample_docs']):
    #                 st.write(f"Doc {i+1}: {doc[:200]}...")
    #             st.write("**Sample metadata:**")
    #             for i, meta in enumerate(debug_info['sample_metadata']):
    #                 st.write(f"Meta {i+1}: {meta}")
    #         else:
    #             st.error("Failed to debug collection")
    #     else:
    #         st.error("Collection not available")
            
    # Export functionality
    # if st.button("📥 Export Discoverer"):
    #     if vector_utils.export_chroma_db():
    #         st.success("Discoverer exported to chroma_db.zip")

# --- TAB 4: CHAT ---
with tab4:
    st.subheader("💬 Answerly")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if chat_input := st.chat_input("Ask here..."):
        if not groq_key:
            st.warning("Please provide your Groq API key in the sidebar.")
        else:
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": chat_input})
            with st.chat_message("user"):
                st.markdown(chat_input)

            # Generate assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        llm = get_llm()
                        if not llm:
                            st.error("Failed to initialize LLM. Check API key.")
                        else:
                            # Get context from Discoverer
                            context = ""
                            if collection:
                                try:
                                    kb_results = vector_utils.query_knowledge_base(chat_input, collection)
                                    context = "\n".join(kb_results) if kb_results else "No relevant context found."
                                except Exception as kb_error:
                                    context = f"Discoverer error: {str(kb_error)}"
                            
                            # Create prompt with context
                            prompt = f"Context from Discoverer:\n{context}\n\nUser question: {chat_input}\n\nPlease provide a helpful response based on the context and your knowledge."
                            
                            # Get LLM response
                            response = llm.invoke(prompt)
                            assistant_response = getattr(response, "content", str(response))
                            
                            st.markdown(assistant_response)
                            st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
                            
                    except Exception as e:
                        error_msg = f"Chat failed: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

# Clear chat history button
with tab4:
    if st.button("🗑️ Clear Chat History",type="primary"):
        st.session_state.chat_history = []
        st.rerun()

# st.markdown("---")
# st.markdown("Powered by **LangGraph**, **ChromaDB**, and **Groq**.")
