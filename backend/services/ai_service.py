"""
AI Service for legal analysis using OpenAI
"""

from openai import OpenAI
import os
import logging
from services import vector_search
import httpx

# Initialize OpenAI client lazily to avoid errors when API key is not set
_client = None

def get_openai_client():
    """Get or create OpenAI client"""
    global _client
    if _client is None and os.getenv("OPENAI_API_KEY"):
        # Create httpx client without proxies to avoid compatibility issues
        http_client = httpx.Client()
        _client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            http_client=http_client
        )
    return _client

logger = logging.getLogger(__name__)


def generate_legal_analysis(query, context="", use_semantic_search=True):
    """Generate AI-powered legal analysis using OpenAI API with ChromaDB semantic search"""
    if not os.getenv("OPENAI_API_KEY"):
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
        
        # Use new OpenAI chat completions API
        client = get_openai_client()
        if not client:
            return "AI analysis requires OpenAI API key configuration. Please set OPENAI_API_KEY environment variable."
        
        response = client.chat.completions.create(
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
        print(f"OpenAI API error: {e}")
        return f"AI analysis temporarily unavailable. Error: {str(e)}"


def generate_summary(citation_text, citation_title=""):
    """
    Generate AI summary for a legal citation.
    
    Args:
        citation_text: Full text of the citation
        citation_title: Optional citation title/number
        
    Returns:
        str: Generated summary or None if failed
    """
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OpenAI API key not configured")
        return None
        
    if not citation_text or len(citation_text.strip()) < 50:
        logger.warning("Citation text too short for summary generation")
        return None
    
    # Limit text to first 8000 characters to stay within token limits
    text_sample = citation_text[:8000]
    
    prompt = f"""You are a senior Pakistani legal expert. Summarize this legal citation focusing on:
- Key facts of the case
- Legal question(s) involved
- Court's judicial reasoning
- Final conclusion/decision

The summary must be concise (150-200 words), accurate, and written in simple, professional language suitable for legal practitioners.

Citation: {citation_title}

Text:
{text_sample}

Summary:"""
    
    try:
        client = get_openai_client()
        if not client:
            logger.error("OpenAI client not initialized - API key missing")
            return None
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert Pakistani legal analyst specializing in case law summarization."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400,
            timeout=30
        )
        
        summary = response.choices[0].message.content.strip()
        logger.info(f"Successfully generated summary for citation: {citation_title}")
        return summary
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return None


def generate_headnotes(citation_text, citation_title=""):
    """
    Generate AI headnotes for a legal citation in PLD/SCMR style.
    
    Args:
        citation_text: Full text of the citation
        citation_title: Optional citation title/number
        
    Returns:
        str: Generated headnotes or None if failed
    """
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OpenAI API key not configured")
        return None
        
    if not citation_text or len(citation_text.strip()) < 50:
        logger.warning("Citation text too short for headnotes generation")
        return None
    
    # Limit text to first 10000 characters
    text_sample = citation_text[:10000]
    
    prompt = f"""You are a senior Pakistani law expert. Based on the following judgment text, generate professional headnotes similar to PLD/SCMR style.

Each headnote must be precise, issue-based, and legally accurate. Include:
• Issues involved
• Legal questions raised
• Statutory provisions applied
• Court's key observations and reasoning
• Ratio decidendi (legal principle)
• Relief granted / Final decision

Format as numbered points. Be concise but comprehensive. Use formal legal language.

Citation: {citation_title}

Judgment Text:
{text_sample}

Headnotes:"""
    
    try:
        client = get_openai_client()
        if not client:
            logger.error("OpenAI client not initialized - API key missing")
            return None
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert Pakistani legal analyst specializing in creating professional headnotes for case law."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=600,
            timeout=40
        )
        
        headnotes = response.choices[0].message.content.strip()
        logger.info(f"Successfully generated headnotes for citation: {citation_title}")
        return headnotes
        
    except Exception as e:
        logger.error(f"Error generating headnotes: {str(e)}")
        return None
