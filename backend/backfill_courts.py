"""
Backfill script to automatically populate court fields for existing citations
Uses extract_court_from_citation to parse court names from citation text
"""

import os
import sys

# Set the correct path for imports
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

# Now import Flask and models
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Import models after app initialization
from models.case import LegalCitation
from services.utils import extract_court_from_citation
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backfill_courts():
    """Backfill court field for all citations that don't have it"""
    
    with app.app_context():
        # Find all citations without court information
        citations_without_court = LegalCitation.query.filter(
            (LegalCitation.court == None) | (LegalCitation.court == '')
        ).all()
        
        logger.info(f"Found {len(citations_without_court)} citations without court information")
        
        updated_count = 0
        failed_count = 0
        
        for citation in citations_without_court:
            try:
                # Extract court from citation text
                court = extract_court_from_citation(citation.citation, citation.full_text)
                
                if court:
                    citation.court = court
                    updated_count += 1
                    logger.info(f"Updated citation {citation.citation} with court: {court}")
                else:
                    failed_count += 1
                    logger.warning(f"Could not extract court from citation: {citation.citation}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing citation {citation.citation}: {str(e)}")
        
        # Commit all changes
        try:
            db.session.commit()
            logger.info(f"Successfully updated {updated_count} citations")
            logger.info(f"Failed to extract court for {failed_count} citations")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error committing changes: {str(e)}")
            raise


if __name__ == '__main__':
    logger.info("Starting court backfill process...")
    backfill_courts()
    logger.info("Court backfill complete!")
