"""
Main blueprint for public pages and core functionality
"""
from flask import Blueprint

main_bp = Blueprint('main', __name__)

# Import routes to register them with the blueprint
from app.main import routes