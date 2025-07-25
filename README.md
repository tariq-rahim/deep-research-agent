# 🧠 Deep Research Agent

**Deep Research Agent** is an intelligent, research assistant designed to streamline your data-gathering, analysis, and conversational workflows. Equipped with advanced tools like web analyzers, LinkedIn profile processors, RAG-based PDF/text extractors, and a powerful chatbot interface, this system is your all-in-one solution for deep research, profiling, and information retrieval.

---

## 🚀 Features

### 🔗 Web Research Agent
- Extracts **relevant links** from the web based on your query.
- Provides **additional sources** and citations to support deep research tasks.
- Returns structured output for better readability and traceability.

### 🕵️ LinkedIn & Web Page Analyzer
- Analyze **LinkedIn profiles** to extract:
  - Work history
  - Skills
  - Education
  - Contact info
- Extract relevant information from **any webpage** to uncover:
  - Key insights
  - Structural content
  - Contact & company data

### 📄 Document Analyzer (PDF & TXT) using RAG
- Uses **Retrieval-Augmented Generation (RAG)** to process documents.
- Supports `.pdf` and `.txt` formats.
- Retrieves **contextual and relevant responses** from loaded files.

### 💬 Conversational AI Chatbot
- Chat with your documents using natural language.
- Ask **random queries** or perform **context-aware Q&A** from:
  - PDFs
  - Text files
  - Web-analyzed content
- Unified chat interface that responds in real-time.

---

## 🧰 Tech Stack

| Component           | Technology Used         |
|--------------------|-------------------------|
| LLM Backbone       | OpenAI GPT / Local Models |
| Document Parsing   | PyMuPDF, LangChain,LangGraph, RAG |
| Web Scraping       | BeautifulSoup, Requests |
| PDF/TXT Handling   | PyMuPDF, LangChain      |
| Chat Interface     | Streamlit / Gradio / Custom Frontend |
| Backend Framework  | FastAPI / Flask         |
| Data Storage       | FAISS / ChromaDB        |

---

## 📦 Installation

```bash
git clone https://github.com/tariq-rahim/deep-research-agent.git
cd deep-research-agent
pip install -r requirements.txt
