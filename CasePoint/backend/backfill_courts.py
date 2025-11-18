"""
Backfill script to automatically populate court fields for existing citations
Uses extract_court_from_citation to parse court names from citation text
"""

import os
import sys

# Set the correct path for imports
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

# Import from existing app
from app import create_app
from models import db
from models.case import LegalCitation
from services.utils import extract_court_from_citation
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app instance
app = create_app(os.getenv('FLASK_ENV', 'default'))


def backfill_courts():
    """Backfill court field for all citations (re-extract to fix incomplete names)"""
    
    with app.app_context():
        # Get ALL citations to re-extract court names (to fix "High Court" → "Lahore High Court")
        all_citations = LegalCitation.query.all()
        
        logger.info(f"Re-extracting court information for {len(all_citations)} citations")
        
        updated_count = 0
        failed_count = 0
        unchanged_count = 0
        
        for citation in all_citations:
            try:
                # Extract court from citation text
                court = extract_court_from_citation(citation.citation, citation.full_text)
                
                if court:
                    if citation.court != court:
                        old_court = citation.court or 'None'
                        citation.court = court
                        updated_count += 1
                        logger.info(f"Updated citation {citation.citation}: {old_court} → {court}")
                    else:
                        unchanged_count += 1
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
            logger.info(f"Unchanged: {unchanged_count} citations")
            logger.info(f"Failed to extract court for {failed_count} citations")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error committing changes: {str(e)}")
            raise


if __name__ == '__main__':
    logger.info("Starting court backfill process...")
    backfill_courts()
    logger.info("Court backfill complete!")
