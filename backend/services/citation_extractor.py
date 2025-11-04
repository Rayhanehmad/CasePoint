"""
Citation extraction service for Pakistan legal documents
Extracts metadata: citations, case titles, courts, judges, headnotes, etc.
"""

import re
from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CitationExtractor:
    """Extract legal metadata from Pakistan case law documents"""
    
    PAKISTAN_CITATIONS = [
        'PLD', 'SCMR', 'PCrLJ', 'CLR', 'PTD', 'MLD', 'YLR',
        'CLC', 'CLD', 'PTCL', 'Tax', 'PSC', 'ALD'
    ]
    
    PAKISTAN_COURTS = {
        'Supreme Court': ['Supreme Court', 'SC of Pakistan', 'S.C.'],
        'Lahore High Court': ['Lahore High Court', 'LHC', 'Lahore'],
        'Sindh High Court': ['Sindh High Court', 'SHC', 'Karachi High Court', 'Karachi'],
        'Islamabad High Court': ['Islamabad High Court', 'IHC', 'Islamabad'],
        'Peshawar High Court': ['Peshawar High Court', 'PHC', 'Peshawar'],
        'Balochistan High Court': ['Balochistan High Court', 'BHC', 'Quetta High Court', 'Quetta'],
        'Federal Shariat Court': ['Federal Shariat Court', 'FSC', 'Shariat Court']
    }
    
    HEADNOTE_MARKERS = [
        'HEADNOTE', 'HELD:', 'Held:', 'PRINCIPLE:', 'Principle:',
        'JUDGMENT', 'ORDER:', 'RATIO DECIDENDI'
    ]
    
    def extract_metadata(self, text: str, filename: str = '') -> Dict:
        """
        Extract all legal metadata from document text
        
        Args:
            text: Full text of the legal document
            filename: Original filename for fallback
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            'citation': self._extract_citation(text, filename),
            'title': self._extract_case_title(text),
            'court': self._extract_court(text),
            'jurisdiction': self._extract_jurisdiction(text),
            'year': self._extract_year(text, filename),
            'judges': self._extract_judges(text),
            'headnotes': self._extract_headnotes(text),
            'legal_area': self._extract_legal_area(text),
            'summary': self._extract_summary(text),
            'parties': self._extract_parties(text)
        }
        
        logger.info(f"Extracted metadata - Citation: {metadata['citation']}, Court: {metadata['court']}")
        return metadata
    
    def _extract_citation(self, text: str, filename: str = '') -> str:
        """Extract Pakistan legal citation (e.g., PLD 1984 Karachi 334)"""
        
        # Pattern: CITATION_TYPE YEAR COURT PAGE
        pattern = r'\b(' + '|'.join(self.PAKISTAN_CITATIONS) + r')\s+(\d{4})\s+([A-Za-z\s]+?)\s+(\d+)'
        
        matches = re.findall(pattern, text[:2000])  # Search first 2000 chars
        
        if matches:
            citation_type, year, court, page = matches[0]
            court = court.strip()
            citation = f"{citation_type} {year} {court} {page}"
            logger.info(f"Found citation: {citation}")
            return citation
        
        # Try filename if no citation found in text
        filename_match = re.search(
            r'(' + '|'.join(self.PAKISTAN_CITATIONS) + r')[-_\s]*(\d{4})[-_\s]*([A-Za-z]+)[-_\s]*(\d+)',
            filename
        )
        
        if filename_match:
            cit_type, year, court, page = filename_match.groups()
            citation = f"{cit_type} {year} {court.upper()} {page}"
            logger.info(f"Extracted citation from filename: {citation}")
            return citation
        
        # Generate unique citation from filename and timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        fallback_citation = f"UPLOAD-{timestamp}"
        if filename:
            clean_name = re.sub(r'[^A-Za-z0-9]', '', filename.rsplit('.', 1)[0])[:20]
            fallback_citation = f"{clean_name}-{timestamp}"
        
        logger.warning(f"No citation found, using fallback: {fallback_citation}")
        return fallback_citation
    
    def _extract_case_title(self, text: str) -> str:
        """Extract case title (party names)"""
        
        # Common patterns for case titles
        # Pattern 1: "PARTY1 v. PARTY2" or "PARTY1 vs. PARTY2"
        vs_pattern = r'([A-Z][A-Za-z\s&\.]+?)\s+(?:v\.|vs\.|versus)\s+([A-Z][A-Za-z\s&\.]+?)(?:\n|Before|JUDGMENT)'
        
        match = re.search(vs_pattern, text[:1500])
        if match:
            petitioner = match.group(1).strip()
            respondent = match.group(2).strip()
            title = f"{petitioner} v. {respondent}"
            logger.info(f"Found case title: {title}")
            return title
        
        # Pattern 2: Look for "Petitioner" and "Respondent" labels
        petitioner_match = re.search(r'([A-Z][A-Z\s\.]+?)(?:-Petitioner|—Petitioner)', text[:1500])
        respondent_match = re.search(r'([A-Z][A-Z\s\.]+?)(?:-Respondent|—Respondent)', text[:1500])
        
        if petitioner_match and respondent_match:
            petitioner = petitioner_match.group(1).strip()
            respondent = respondent_match.group(1).strip()
            title = f"{petitioner} v. {respondent}"
            logger.info(f"Found case title from labels: {title}")
            return title
        
        # Fallback: Extract first bold/caps line
        first_lines = text[:500].split('\n')
        for line in first_lines:
            line = line.strip()
            if len(line) > 10 and line.isupper() and 'JUDGMENT' not in line and 'COURT' not in line:
                return line[:200]  # Limit title length
        
        return ''
    
    def _extract_court(self, text: str) -> str:
        """Extract court name"""
        
        text_search = text[:2000]  # Search in first 2000 chars
        
        for standard_name, variations in self.PAKISTAN_COURTS.items():
            for variation in variations:
                if variation in text_search:
                    logger.info(f"Found court: {standard_name}")
                    return standard_name
        
        # Generic high court pattern
        hc_match = re.search(r'([A-Z][a-z]+)\s+High Court', text_search)
        if hc_match:
            court = f"{hc_match.group(1)} High Court"
            logger.info(f"Found court via pattern: {court}")
            return court
        
        return ''
    
    def _extract_jurisdiction(self, text: str) -> str:
        """Extract jurisdiction (Federal, Punjab, Sindh, etc.)"""
        
        court = self._extract_court(text)
        
        jurisdiction_map = {
            'Supreme Court': 'Federal',
            'Federal Shariat Court': 'Federal',
            'Lahore High Court': 'Punjab',
            'Sindh High Court': 'Sindh',
            'Islamabad High Court': 'Islamabad',
            'Peshawar High Court': 'Khyber Pakhtunkhwa',
            'Balochistan High Court': 'Balochistan'
        }
        
        return jurisdiction_map.get(court, '')
    
    def _extract_year(self, text: str, filename: str = '') -> Optional[int]:
        """Extract year from citation or text"""
        
        # Try to find year in citation
        citation_pattern = r'\b(' + '|'.join(self.PAKISTAN_CITATIONS) + r')\s+(\d{4})'
        match = re.search(citation_pattern, text[:2000])
        
        if match:
            year = int(match.group(2))
            if 1900 <= year <= 2100:
                return year
        
        # Try filename
        filename_year = re.search(r'(19\d{2}|20\d{2})', filename)
        if filename_year:
            return int(filename_year.group(1))
        
        # Try to find "decided on" or "judgment dated"
        date_pattern = r'(?:decided on|judgment dated|date[d:])\s+(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(date_pattern, text[:3000], re.IGNORECASE)
        
        if match:
            year = int(match.group(3))
            if 1900 <= year <= 2100:
                return year
        
        return None
    
    def _extract_judges(self, text: str) -> Optional[str]:
        """Extract judge names"""
        
        # Pattern: "Before ... J." or "Coram: ..."
        before_pattern = r'Before\s+([A-Z][^\.]+?(?:and|,)[^\.]+?)\s+JJ?\.'
        coram_pattern = r'Coram:\s+([A-Z][^\n]+?)(?:\n|$)'
        
        match = re.search(before_pattern, text[:1000])
        if match:
            judges = match.group(1).strip()
            judges = re.sub(r'\s+', ' ', judges)  # Clean whitespace
            logger.info(f"Found judges: {judges}")
            return judges
        
        match = re.search(coram_pattern, text[:1000])
        if match:
            judges = match.group(1).strip()
            logger.info(f"Found judges via Coram: {judges}")
            return judges
        
        return None
    
    def _extract_headnotes(self, text: str) -> Optional[str]:
        """Extract headnotes/holdings from judgment"""
        
        headnotes = []
        
        # Look for HELD: or Held: sections
        held_pattern = r'HELD:|Held:'
        matches = list(re.finditer(held_pattern, text[:5000]))
        
        for match in matches:
            start = match.end()
            # Extract until next section marker or 500 chars
            end = start + 500
            
            # Find next section
            next_section = re.search(r'\n[A-Z][A-Z\s]{5,}:', text[start:start+1000])
            if next_section:
                end = start + next_section.start()
            
            headnote = text[start:end].strip()
            if headnote and len(headnote) > 20:
                headnotes.append(headnote)
        
        # Look for numbered headnotes
        headnote_pattern = r'\((?:\d+|[ivxlc]+)\)\s+([A-Z][^\n]{30,300})'
        numbered_headnotes = re.findall(headnote_pattern, text[:3000])
        
        if numbered_headnotes:
            headnotes.extend(numbered_headnotes[:5])  # Max 5 headnotes
        
        if headnotes:
            combined = '\n\n'.join(headnotes)
            logger.info(f"Extracted {len(headnotes)} headnote(s)")
            return combined[:2000]  # Limit total length
        
        return None
    
    def _extract_legal_area(self, text: str) -> str:
        """Detect legal area/subject matter"""
        
        legal_areas = {
            'Constitutional Law': ['constitution', 'fundamental right', 'article 9', 'article 10', 'article 25', 'writ petition'],
            'Criminal Law': ['penal code', 'PPC', 'murder', 'criminal', 'accused', 'prosecution', 'bail', 'FIR'],
            'Civil Law': ['civil suit', 'damages', 'contract', 'tort', 'specific performance', 'injunction'],
            'Tax Law': ['tax', 'income tax', 'sales tax', 'customs', 'revenue'],
            'Family Law': ['divorce', 'custody', 'maintenance', 'marriage', 'nikah', 'talaq', 'khula'],
            'Property Law': ['property', 'ownership', 'possession', 'land', 'transfer', 'mutation'],
            'Labor Law': ['labor', 'labour', 'employment', 'worker', 'service', 'termination', 'industrial'],
            'Administrative Law': ['administrative', 'tribunal', 'service matter', 'pension', 'government servant']
        }
        
        text_lower = text[:3000].lower()
        area_scores = {}
        
        for area, keywords in legal_areas.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            if score > 0:
                area_scores[area] = score
        
        if area_scores:
            best_area = max(area_scores, key=area_scores.get)
            logger.info(f"Detected legal area: {best_area}")
            return best_area
        
        return ''
    
    def _extract_summary(self, text: str) -> str:
        """Generate a brief summary from the first paragraph or judgment"""
        
        # Look for first substantial paragraph
        paragraphs = text.split('\n\n')
        
        for para in paragraphs[:10]:
            para = para.strip()
            # Skip headers, citations, and very short paragraphs
            if (len(para) > 100 and 
                not para.isupper() and 
                not re.match(r'^(Before|Coram|JUDGMENT)', para)):
                # Clean and limit to first 500 chars
                summary = re.sub(r'\s+', ' ', para)
                return summary[:500]
        
        return ''
    
    def _extract_parties(self, text: str) -> Dict[str, str]:
        """Extract petitioner and respondent names"""
        
        parties = {'petitioner': '', 'respondent': ''}
        
        # Look for labeled parties
        petitioner_match = re.search(r'([A-Z][A-Z\s\.&]+?)(?:-Petitioner|—Petitioner)', text[:1500])
        respondent_match = re.search(r'([A-Z][A-Z\s\.&]+?)(?:-Respondent|—Respondent)', text[:1500])
        
        if petitioner_match:
            parties['petitioner'] = petitioner_match.group(1).strip()
        
        if respondent_match:
            parties['respondent'] = respondent_match.group(1).strip()
        
        return parties


# Global instance
citation_extractor = CitationExtractor()
