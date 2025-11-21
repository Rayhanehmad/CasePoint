"""
Vector Search Service using ChromaDB
Handles document embedding and semantic search for legal documents
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb.config import Settings
from openai import OpenAI

# Initialize OpenAI client lazily to avoid errors when API key is not set
_client = None

def get_openai_client():
    """Get or create OpenAI client"""
    global _client
    if _client is None and os.environ.get("OPENAI_API_KEY"):
        _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _client

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

# Get or create collection for legal documents
try:
    collection = chroma_client.get_or_create_collection(
        name="legal_documents",
        metadata={"description": "Pakistan legal documents and citations"}
    )
    logging.info("ChromaDB collection initialized successfully")
except Exception as e:
    logging.error(f"Error initializing ChromaDB collection: {e}")
    collection = None


def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector using OpenAI's embedding model"""
    try:
        client = get_openai_client()
        if not client:
            logging.error("OpenAI client not initialized - API key missing")
            return None
        
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"Error generating embedding: {e}")
        return None


def add_document_to_vector_db(doc_id: str, text: str, metadata: Dict) -> bool:
    """Add document to ChromaDB with embedding"""
    if not collection:
        logging.error("ChromaDB collection not initialized")
        return False
    
    if not text or len(text.strip()) < 50:
        logging.warning(f"Document {doc_id} text too short for embedding")
        return False
    
    try:
        # Generate embedding
        embedding = generate_embedding(text)
        if not embedding:
            return False
        
        # Add to collection
        collection.add(
            ids=[str(doc_id)],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
        
        logging.info(f"Added document {doc_id} to vector database")
        return True
        
    except Exception as e:
        logging.error(f"Error adding document to vector DB: {e}")
        return False


def search_similar_documents(query: str, n_results: int = 5, 
                            document_type: Optional[str] = None) -> List[Dict]:
    """Search for similar documents using semantic search"""
    if not collection:
        logging.error("ChromaDB collection not initialized")
        return []
    
    try:
        # Generate query embedding
        query_embedding = generate_embedding(query)
        if not query_embedding:
            return []
        
        # Build where filter
        where_filter = {}
        if document_type:
            where_filter["document_type"] = document_type
        
        # Query collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None
        )
        
        # Format results
        documents = []
        if results and results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                doc = {
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results.get('distances') else None
                }
                documents.append(doc)
        
        logging.info(f"Found {len(documents)} similar documents for query")
        return documents
        
    except Exception as e:
        logging.error(f"Error searching similar documents: {e}")
        return []


def delete_document_from_vector_db(doc_id: str) -> bool:
    """Delete document from ChromaDB"""
    if not collection:
        return False
    
    try:
        collection.delete(ids=[str(doc_id)])
        logging.info(f"Deleted document {doc_id} from vector database")
        return True
    except Exception as e:
        logging.error(f"Error deleting document from vector DB: {e}")
        return False


def get_collection_stats() -> Dict:
    """Get statistics about the vector database collection"""
    if not collection:
        return {"error": "Collection not initialized"}
    
    try:
        count = collection.count()
        return {
            "total_documents": count,
            "collection_name": collection.name
        }
    except Exception as e:
        logging.error(f"Error getting collection stats: {e}")
        return {"error": str(e)}
