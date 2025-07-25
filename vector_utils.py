# file: vector_utils.py
import chromadb
from chromadb.utils import embedding_functions
import uuid
import os,time
import shutil
import streamlit as st

# Create a new folder for ChromaDB if it doesn't exist
DB_PATH = os.path.join(os.getcwd(), "chroma_db")
os.makedirs(DB_PATH, exist_ok=True)

# Initialize ChromaDB client with error handling
try:
    client = chromadb.PersistentClient(path=DB_PATH)
    # Use default embedding function (no external dependencies)
    embedding_func = embedding_functions.DefaultEmbeddingFunction()
except Exception as e:
    st.error(f"Failed to initialize ChromaDB: {e}")
    raise

def get_or_create_collection(name="deep_research"):
    """Get or create a ChromaDB collection"""
    try:
        return client.get_or_create_collection(
            name=name,
            embedding_function=embedding_func,
            metadata={"hnsw:space": "cosine"}
        )
    except Exception as e:
        st.error(f"Failed to create collection: {e}")
        raise

def completely_reset_database():
    """Completely reset the ChromaDB database by deleting and recreating it"""
    try:
        global client
        # Close existing client
        if 'client' in globals():
            del client
        
        # Remove the entire database directory
        if os.path.exists(DB_PATH):
            shutil.rmtree(DB_PATH)
            print(f"✅ Removed existing database at {DB_PATH}")
        
        # Recreate the directory
        os.makedirs(DB_PATH, exist_ok=True)
        
        # Reinitialize client
        client = chromadb.PersistentClient(path=DB_PATH)
        print("✅ Database completely reset and reinitialized")
        return True
        
    except Exception as e:
        print(f"❌ Failed to reset database: {e}")
        return False


    
def add_document_to_collection(document_text: str, source: str, collection):
    """Add a document to the collection with text preprocessing"""
    try:
        # Clean and preprocess the text
        processed_text = preprocess_text(document_text)
        
        if len(processed_text.strip()) < 50:
            print(f"Warning: Document {source} has very little content after processing")
            return None
        
        # Split large documents into chunks
        chunks = split_text_into_chunks(processed_text, chunk_size=1000, overlap=100)
        
        doc_ids = []
        for i, chunk in enumerate(chunks):
            doc_id = str(uuid.uuid4())
            collection.add(
                documents=[chunk],
                metadatas=[{
                    "source": source,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "added_timestamp": str(uuid.uuid4())  # Add unique timestamp
                }],
                ids=[doc_id]
            )
            doc_ids.append(doc_id)
        
        print(f"Added document from source: {source} ({len(chunks)} chunks)")
        return doc_ids
    except Exception as e:
        st.error(f"Failed to add document: {e}")
        raise

def preprocess_text(text: str) -> str:
    """Clean and preprocess text for better embedding"""
    import re
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep important punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', ' ', text)
    
    # Remove very short lines that might be artifacts
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 10]
    
    return '\n'.join(cleaned_lines).strip()

def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> list:
    """Split text into overlapping chunks for better retrieval"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to end at a sentence boundary
        if end < len(text):
            # Look for sentence endings within the last 100 characters
            last_period = text.rfind('.', start, end)
            last_newline = text.rfind('\n', start, end)
            
            boundary = max(last_period, last_newline)
            if boundary > start + chunk_size - 200:  # Only use boundary if it's not too early
                end = boundary + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks

def query_knowledge_base(query: str, collection, n_results=2) -> list:
    """Query the Discoverer"""
    try:
        if collection.count() == 0:
            print("Discoverer is empty. Skipping query.")
            return []

        results = collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        documents = results.get('documents', [[]])[0]
        print(f"KB Query returned {len(documents)} results for: {query}")
        return documents
    except Exception as e:
        st.error(f"Failed to query Discoverer: {e}")
        return []

def initialize_with_sample_data(collection):
    """Initialize the Discoverer with sample research data"""
    try:
        sample_docs = [
            {
                "content": """
                Artificial Intelligence in Healthcare Market Analysis:
                The AI in healthcare market is experiencing unprecedented growth, with the global market size expected to reach $102 billion by 2028, growing at a CAGR of 44.9%. 
                Key applications include diagnostic imaging, drug discovery, personalized medicine, and robotic surgery.
                Major players include IBM Watson Health, Google DeepMind, and Microsoft Healthcare Bot.
                Challenges include data privacy, regulatory compliance, and integration with existing healthcare systems.
                """,
                "source": "ai_healthcare_market_2024.txt"
            }
        ]
        
        for doc_data in sample_docs:
            add_document_to_collection(
                document_text=doc_data["content"],
                source=doc_data["source"],
                collection=collection
            )
        
        print(f"Initialized Discoverer with {len(sample_docs)} sample documents")
        return True
        
    except Exception as e:
        st.error(f"Failed to initialize sample data: {e}")
        return False

def get_collection_stats(collection):
    """Get statistics about the collection"""
    try:
        doc_count = collection.count()
        
        # Get sample of documents to check content
        sample_results = collection.get(limit=3)
        
        stats = {
            "document_count": doc_count,
            "status": "Active" if doc_count > 0 else "Empty",
            "sample_sources": [meta.get("source", "Unknown") for meta in sample_results.get("metadatas", [])],
            "collection_name": collection.name if hasattr(collection, 'name') else "deep_research"
        }
        
        return stats
        
    except Exception as e:
        return {
            "document_count": 0,
            "status": f"Error: {str(e)}",
            "sample_sources": [],
            "collection_name": "unknown"
        }

def clear_collection(collection):
    """Clear all documents from the collection"""
    try:
        # Get all IDs and delete them
        all_data = collection.get()
        if all_data.get("ids"):
            collection.delete(ids=all_data["ids"])
        print("Collection cleared successfully")
        return True
    except Exception as e:
        st.error(f"Failed to clear collection: {e}")
        return False

def export_chroma_db(output_file="chroma_db.zip"):
    """Export the ChromaDB to a zip file"""
    try:
        shutil.make_archive(output_file.replace('.zip',''), 'zip', DB_PATH)
        print(f"ChromaDB exported to {output_file}")
        return True
    except Exception as e:
        st.error(f"Failed to export ChromaDB: {e}")
        return False

def search_similar_documents(query: str, collection, n_results=5, include_metadata=True):
    """Enhanced search function that returns documents with metadata"""
    try:
        if collection.count() == 0:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"] if include_metadata else ["documents"]
        )
        
        if not include_metadata:
            return results.get('documents', [[]])[0]
        
        # Combine documents with their metadata and similarity scores
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        
        enhanced_results = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            enhanced_results.append({
                "content": doc,
                "source": meta.get("source", "Unknown"),
                "similarity_score": 1 - dist,  # Convert distance to similarity
                "metadata": meta
            })
        
        return enhanced_results
        
    except Exception as e:
        st.error(f"Failed to search documents: {e}")
        return []

def debug_collection_contents(collection):
    """Debug function to see what's actually in the collection"""
    try:
        all_data = collection.get()
        print(f"Total documents in collection: {len(all_data.get('documents', []))}")
        
        documents = all_data.get('documents', [])
        metadatas = all_data.get('metadatas', [])
        
        for i, (doc, meta) in enumerate(zip(documents[:5], metadatas[:5])):
            print(f"\nDocument {i+1}:")
            print(f"Source: {meta.get('source', 'Unknown')}")
            print(f"Content preview: {doc[:200]}...")
            
        return {
            "total_docs": len(documents),
            "sample_docs": documents[:3],
            "sample_metadata": metadatas[:3]
        }
        
    except Exception as e:
        print(f"Debug failed: {e}")
        return None
