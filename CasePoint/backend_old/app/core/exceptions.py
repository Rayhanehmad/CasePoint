"""
Custom exceptions and exception handlers
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class KanoonPKException(Exception):
    """Base exception for KanoonPK"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

class AuthenticationException(KanoonPKException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)

class AuthorizationException(KanoonPKException):
    """Authorization failed"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, 403)

class SubscriptionException(KanoonPKException):
    """Subscription related exception"""
    def __init__(self, message: str = "Subscription required"):
        super().__init__(message, 402)

class DocumentProcessingException(KanoonPKException):
    """Document processing failed"""
    def __init__(self, message: str = "Document processing failed"):
        super().__init__(message, 422)

def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers"""
    
    @app.exception_handler(KanoonPKException)
    async def kanoonpk_exception_handler(request: Request, exc: KanoonPKException):
        logger.error(f"KanoonPK Exception: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "type": exc.__class__.__name__}
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )