"""
AI Service for legal analysis using OpenAI
"""

import openai
import os
from . import vector_search

# Configure OpenAI with legacy API
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_legal_analysis(query, context="", use_semantic_search=True):
    """Generate AI-powered legal analysis using legacy OpenAI API with ChromaDB semantic search"""
    if not openai.api_key:
        return "AI analysis requires OpenAI API key configuration. Please set OPENAI_API_KEY environment variable."
    
    try:
        # Search for relevant documents using ChromaDB if enabled
        relevant_docs = []
        if use_semantic_search:
            relevant_docs = vector_search.search_similar_documents(query, n_results=3)
        
        # Build context from relevant documents
        doc_context = ""
        if relevant_docs:
            doc_context = "\n\nRelevant Legal Documents:\n"
            for i, doc in enumerate(relevant_docs, 1):
                metadata = doc.get('metadata', {})
                doc_text = doc.get('text', '')[:500]  # First 500 chars
                doc_context += f"\n{i}. {metadata.get('title', 'Document')}"
                if metadata.get('citation'):
                    doc_context += f" ({metadata.get('citation')})"
                if metadata.get('court'):
                    doc_context += f" - {metadata.get('court')}"
                doc_context += f"\n   {doc_text}...\n"
        
        # Create prompt for legal analysis
        if context or doc_context:
            full_context = (context + doc_context) if context else doc_context
            prompt = f"""As a legal research assistant specializing in Pakistan law, analyze the following query with the provided context:

Query: {query}

Context: {full_context}

Please provide:
1. A direct answer to the legal question
2. Relevant legal principles and precedents under Pakistan law
3. Citations to relevant statutes, cases, or legal authorities from the context
4. Important considerations or limitations

Response should be professional and accurate."""
        else:
            prompt = f"""As a legal research assistant specializing in Pakistan law, provide a comprehensive analysis of the following legal query:

Query: {query}

Please provide:
1. A direct answer to the legal question
2. Relevant legal principles and precedents under Pakistan law
3. Citations to relevant statutes, cases, or legal authorities
4. Important considerations or limitations

Response should be professional and accurate."""
        
        # Use legacy OpenAI ChatCompletion API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert legal research assistant specializing in Pakistan law. Provide accurate, well-cited legal analysis based on the provided context."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Legacy OpenAI API error: {e}")
        return f"AI analysis temporarily unavailable. Error: {str(e)}"
