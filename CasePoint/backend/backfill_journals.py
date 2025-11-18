"""
Backfill script to extract and update journal field for existing citations
Run this script to populate the journal field for all citations in the database
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from models.case import LegalCitation
from services.utils import extract_journal_from_citation

# Create app instance
app = create_app()


def backfill_journals():
    """Extract and update journal field for all existing citations"""
    with app.app_context():
        print("Starting journal backfill...")
        
        # Get all citations
        citations = LegalCitation.query.all()
        total = len(citations)
        updated_count = 0
        
        print(f"Found {total} citations to process")
        
        for i, citation in enumerate(citations, 1):
            if citation.citation:
                # Extract journal from citation text
                journal = extract_journal_from_citation(citation.citation)
                
                if journal:
                    citation.journal = journal
                    updated_count += 1
                    print(f"[{i}/{total}] Updated {citation.citation} → {journal}")
                else:
                    print(f"[{i}/{total}] No journal found in {citation.citation}")
            else:
                print(f"[{i}/{total}] Skipping citation with no citation text (ID: {citation.id})")
            
            # Commit in batches of 100
            if i % 100 == 0:
                db.session.commit()
                print(f"Committed batch up to {i}/{total}")
        
        # Final commit
        db.session.commit()
        
        print(f"\n✓ Backfill complete!")
        print(f"  Total citations: {total}")
        print(f"  Updated with journal: {updated_count}")
        print(f"  No journal found: {total - updated_count}")


if __name__ == '__main__':
    try:
        backfill_journals()
    except Exception as e:
        print(f"\n✗ Error during backfill: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
