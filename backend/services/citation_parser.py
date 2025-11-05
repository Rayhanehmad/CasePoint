"""
Pakistani Legal Citation Parser and Extractor
Recognizes and extracts citations in Pakistani legal formats
"""

import re
import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class CitationParser:
    """Parser for Pakistani legal citation formats"""
    
    # Pakistani legal citation patterns
    CITATION_PATTERNS = [
        # PLD format: PLD 2024 SC 1, PLD 2024 Karachi 1
        r'PLD\s+(\d{4})\s+([A-Za-z\s]+?)\s+(\d+)',
        
        # Standard format: YEAR CODE NUMBER (e.g., 2025 CLC 1, 2025 SCMR 1)
        r'(\d{4})\s+(CLC|CLD|MLD|PCrLJ|PLC|PTD|SCMR|YLR)\s+(\d+)',
        
        # CLC format variations
        r'CLC\s+(\d{4})\s+(\d+)',
        
        # General format with court: CODE YEAR COURT NUMBER
        r'(PLD|CLC|CLD|MLD|PCrLJ|PLC|PTD|SCMR|YLR)\s+(\d{4})\s+([A-Za-z\s]+?)\s+(\d+)',
    ]
    
    # Compile all patterns
    COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in CITATION_PATTERNS]
    
    # Citation codes
    VALID_CODES = ['PLD', 'CLC', 'CLD', 'MLD', 'PCrLJ', 'PLC', 'PTD', 'SCMR', 'YLR']
    
    # Court abbreviations
    COURT_MAPPINGS = {
        'SC': 'Supreme Court of Pakistan',
        'FSC': 'Federal Shariat Court',
        'Karachi': 'Karachi High Court',
        'Lahore': 'Lahore High Court',
        'Islamabad': 'Islamabad High Court',
        'Peshawar': 'Peshawar High Court',
        'Quetta': 'Quetta High Court',
    }
    
    def __init__(self):
        """Initialize citation parser"""
        pass
    
    def find_all_citations(self, text: str) -> List[Dict[str, any]]:
        """
        Find all Pakistani legal citations in text
        
        Returns:
            List of dicts with: {
                'citation': 'PLD 2024 SC 1',
                'code': 'PLD',
                'year': 2024,
                'court': 'Supreme Court of Pakistan',
                'number': 1,
                'position': (start, end)
            }
        """
        citations = []
        seen_citations = set()  # Avoid duplicates
        
        for pattern in self.COMPILED_PATTERNS:
            for match in pattern.finditer(text):
                citation_info = self._extract_citation_info(match, text)
                if citation_info and citation_info['citation'] not in seen_citations:
                    citations.append(citation_info)
                    seen_citations.add(citation_info['citation'])
        
        # Sort by position in text
        citations.sort(key=lambda x: x['position'][0])
        return citations
    
    def _extract_citation_info(self, match, text: str) -> Optional[Dict]:
        """Extract structured citation information from regex match"""
        try:
            groups = match.groups()
            matched_text = match.group(0)
            
            # Determine citation format
            if matched_text.upper().startswith('PLD'):
                # PLD format
                if len(groups) == 3:
                    year = int(groups[0])
                    court_raw = groups[1].strip()
                    number = int(groups[2])
                    code = 'PLD'
                else:
                    return None
            elif groups[0].isdigit():
                # Year-first format (e.g., 2025 CLC 1)
                year = int(groups[0])
                code = groups[1].upper()
                number = int(groups[2])
                court_raw = None
            elif groups[0].upper() in self.VALID_CODES:
                # Code-first format
                code = groups[0].upper()
                if len(groups) == 2:
                    year = int(groups[1])
                    number = int(groups[2]) if len(groups) > 2 else 1
                    court_raw = None
                elif len(groups) == 4:
                    year = int(groups[1])
                    court_raw = groups[2].strip()
                    number = int(groups[3])
                else:
                    return None
            else:
                return None
            
            # Map court name
            court = self._map_court_name(court_raw) if court_raw else self._default_court_for_code(code)
            
            return {
                'citation': matched_text,
                'code': code,
                'year': year,
                'court': court,
                'number': number,
                'position': match.span()
            }
            
        except (ValueError, IndexError) as e:
            logger.debug(f"Could not parse citation: {match.group(0)} - {str(e)}")
            return None
    
    def _map_court_name(self, court_raw: str) -> str:
        """Map court abbreviation to full name"""
        court_raw = court_raw.strip()
        return self.COURT_MAPPINGS.get(court_raw, court_raw + ' Court')
    
    def _default_court_for_code(self, code: str) -> str:
        """Get default court for citation code"""
        defaults = {
            'PLD': 'Supreme Court of Pakistan',
            'SCMR': 'Supreme Court of Pakistan',
            'CLC': 'High Court',
            'CLD': 'High Court',
            'MLD': 'High Court',
            'PCrLJ': 'High Court',
            'PLC': 'Labour Court',
            'PTD': 'Tax Court',
            'YLR': 'High Court',
        }
        return defaults.get(code, 'Court of Pakistan')
    
    def split_document_by_citations(self, text: str) -> List[Dict[str, any]]:
        """
        Split document into individual citation blocks
        
        Returns:
            List of dicts with: {
                'citation': 'PLD 2024 SC 1',
                'code': 'PLD',
                'year': 2024,
                'court': 'Supreme Court',
                'number': 1,
                'text': 'Full text content for this citation...'
            }
        """
        citations = self.find_all_citations(text)
        
        if not citations:
            return []
        
        citation_blocks = []
        
        for i, citation_info in enumerate(citations):
            # Determine text range for this citation
            start_pos = citation_info['position'][0]
            
            # End position is start of next citation, or end of document
            if i < len(citations) - 1:
                end_pos = citations[i + 1]['position'][0]
            else:
                end_pos = len(text)
            
            # Extract text block
            citation_text = text[start_pos:end_pos].strip()
            
            # Create citation block
            block = {
                'citation': citation_info['citation'],
                'code': citation_info['code'],
                'year': citation_info['year'],
                'court': citation_info['court'],
                'number': citation_info['number'],
                'text': citation_text,
                'text_length': len(citation_text)
            }
            
            citation_blocks.append(block)
        
        logger.info(f"Extracted {len(citation_blocks)} citation blocks from document")
        return citation_blocks
    
    def extract_title_from_text(self, citation_text: str, citation_code: str) -> Optional[str]:
        """
        Extract case title from citation text
        Usually appears right after the citation line
        """
        lines = citation_text.split('\n')
        
        # Skip the citation line itself
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines and citation lines
            if not line or citation_code in line:
                continue
            
            # Look for common title patterns
            # Typically: "PARTY v. PARTY" or "In the matter of..."
            if ' v. ' in line or ' vs. ' in line or ' V. ' in line:
                return line[:200]  # Limit title length
            
            # If line has reasonable length and doesn't look like a citation
            if 20 < len(line) < 200 and not any(code in line for code in self.VALID_CODES):
                return line
        
        return None


# Global instance
citation_parser = CitationParser()
