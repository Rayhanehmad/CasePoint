"""
AI endpoints for OpenAI integration
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.services.ai_service import AIService
# Simplified AI endpoints without authentication for now
# from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

class AIAnalysisRequest(BaseModel):
    query: str
    documents: Optional[List[str]] = None

class AIAnalysisResponse(BaseModel):
    answer: str
    query: str
    status: str = "success"

@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_legal_query(
    request: AIAnalysisRequest
):
    """
    Analyze legal query using legacy OpenAI API
    """
    try:
        ai_service = AIService()
        
        # Generate analysis using legacy OpenAI API
        analysis = await ai_service.generate_legal_analysis(
            query=request.query,
            documents=request.documents or []
        )
        
        if not analysis or "temporarily unavailable" in analysis:
            raise HTTPException(status_code=503, detail=analysis or "AI service unavailable")
        
        return AIAnalysisResponse(
            answer=analysis,
            query=request.query,
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

@router.post("/complete")
async def complete_text(
    request: dict
):
    """
    Simple text completion using legacy OpenAI API
    """
    try:
        ai_service = AIService()
        
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Use the synchronous version for simple completion
        result = ai_service.generate_legal_analysis_sync(query=prompt)
        
        if not result or "temporarily unavailable" in result:
            raise HTTPException(status_code=503, detail=result or "AI service unavailable")
        
        return {
            "completion": result,
            "prompt": prompt,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text completion failed: {str(e)}")

@router.get("/status")
async def ai_status():
    """
    Check AI service status
    """
    try:
        ai_service = AIService()
        
        # Test with a simple query
        test_result = ai_service.generate_legal_analysis_sync("Test connection")
        
        if test_result and "temporarily unavailable" not in test_result:
            return {
                "status": "healthy",
                "service": "legacy-openai",
                "message": "AI service is operational"
            }
        else:
            return {
                "status": "degraded", 
                "service": "legacy-openai",
                "message": "AI service may be experiencing issues"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "service": "legacy-openai", 
            "message": f"AI service error: {str(e)}"
        }