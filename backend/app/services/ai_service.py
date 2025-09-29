"""
AI service for legal analysis using OpenAI
"""

import openai
from typing import List, Optional
from app.core.config import settings

class AIService:
    """AI service for legal research and analysis"""
    
    def __init__(self):
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
    
    async def generate_legal_analysis(self, query: str, documents: List[str]) -> Optional[str]:
        """Generate AI-powered legal analysis"""
        if not settings.OPENAI_API_KEY:
            return "AI analysis requires OpenAI API key configuration."
        
        try:
            # Prepare context from documents
            context = "\n\n".join(documents[:5])  # Limit to first 5 documents
            
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
            
            response = await openai.ChatCompletion.acreate(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert legal research assistant specializing in Pakistan law. Provide accurate, well-cited legal analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.2
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return f"AI analysis temporarily unavailable. Please try again later."