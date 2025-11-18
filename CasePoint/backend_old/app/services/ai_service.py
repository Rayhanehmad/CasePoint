"""
AI service for legal analysis using legacy OpenAI API
"""

import openai
import os
from typing import List, Optional
from app.core.config import settings

class AIService:
    """AI service for legal research and analysis using legacy OpenAI API"""
    
    def __init__(self):
        # Set up legacy OpenAI API
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        else:
            # Fallback to environment variable
            openai.api_key = os.getenv("OPENAI_API_KEY")
    
    async def generate_legal_analysis(self, query: str, documents: Optional[List[str]] = None) -> Optional[str]:
        """Generate AI-powered legal analysis using legacy OpenAI API"""
        if not openai.api_key:
            return "AI analysis requires OpenAI API key configuration."
        
        try:
            # Prepare context from documents if provided
            context = ""
            if documents:
                context = "\n\n".join(documents[:5])  # Limit to first 5 documents
            
            # Create prompt for legal analysis
            if context:
                prompt = f"""
                As a legal research assistant specializing in Pakistan law, analyze the following query and provide a comprehensive response based on the legal documents provided.

                Query: {query}

                Legal Documents Context:
                {context}

                Please provide:
                1. A direct answer to the legal question
                2. Relevant citations and precedents from the provided documents
                3. Key legal principles that apply
                4. Any important considerations or limitations

                Response should be professional, accurate, and cite specific parts of the provided documents.
                """
            else:
                prompt = f"""
                As a legal research assistant specializing in Pakistan law, provide a comprehensive analysis of the following legal query:

                Query: {query}

                Please provide:
                1. A direct answer to the legal question
                2. Relevant legal principles and precedents under Pakistan law
                3. Citations to relevant statutes, cases, or legal authorities
                4. Important considerations or limitations

                Response should be professional and accurate.
                """
            
            # Use legacy OpenAI ChatCompletion API
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",  # Use stable model
                messages=[
                    {"role": "system", "content": "You are an expert legal research assistant specializing in Pakistan law. Provide accurate, well-cited legal analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.2
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Legacy OpenAI API error: {e}")
            return f"AI analysis temporarily unavailable. Error: {str(e)}"
    
    def generate_legal_analysis_sync(self, query: str, documents: Optional[List[str]] = None) -> Optional[str]:
        """Synchronous version using legacy OpenAI API"""
        if not openai.api_key:
            return "AI analysis requires OpenAI API key configuration."
        
        try:
            # Prepare context from documents if provided
            context = ""
            if documents:
                context = "\n\n".join(documents[:3])  # Limit to first 3 documents
            
            # Create prompt for legal analysis
            if context:
                prompt = f"""As a Pakistan law expert, analyze this query with the provided documents:

Query: {query}

Documents: {context}

Provide: 1) Direct answer 2) Relevant citations 3) Key principles 4) Considerations"""
            else:
                prompt = f"""As a Pakistan law expert, analyze this legal query:

Query: {query}

Provide: 1) Direct answer 2) Legal principles 3) Relevant authorities 4) Considerations"""
            
            # Use legacy OpenAI ChatCompletion API (synchronous)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert Pakistan law researcher. Be concise and accurate."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.2
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Legacy OpenAI API error: {e}")
            return f"AI analysis temporarily unavailable. Error: {str(e)}"