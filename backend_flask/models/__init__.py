"""
Database models for KanoonPK
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models
from .user import User
from .case import LegalCitation

__all__ = ['db', 'User', 'LegalCitation']
