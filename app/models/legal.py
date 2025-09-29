"""
Legal document and search models for Pakistan law research
"""
from enum import Enum
from sqlalchemy.dialects.postgresql import UUID, JSON, ARRAY
from app import db
from app.models.base import BaseModel, TenantMixin

class DocumentType(Enum):
    CASE_LAW = "case_law"
    STATUTE = "statute"
    REGULATION = "regulation"
    ORDINANCE = "ordinance"
    JUDGMENT = "judgment"
    ORDER = "order"
    LEGAL_OPINION = "legal_opinion"
    CONTRACT = "contract"
    PLEADING = "pleading"
    BRIEF = "brief"

class CourtLevel(Enum):
    SUPREME_COURT = "supreme_court"
    HIGH_COURT = "high_court"
    DISTRICT_COURT = "district_court"
    SPECIAL_COURT = "special_court"
    TRIBUNAL = "tribunal"

class Jurisdiction(Enum):
    SUPREME_COURT_PAKISTAN = "Supreme Court of Pakistan"
    FEDERAL_SHARIAT_COURT = "Federal Shariat Court"
    LAHORE_HIGH_COURT = "Lahore High Court"
    KARACHI_HIGH_COURT = "Karachi High Court (Sindh)"
    PESHAWAR_HIGH_COURT = "Peshawar High Court"
    QUETTA_HIGH_COURT = "Quetta High Court (Balochistan)"
    ISLAMABAD_HIGH_COURT = "Islamabad High Court"

class LegalArea(Enum):
    CONSTITUTIONAL_LAW = "Constitutional Law"
    CRIMINAL_LAW = "Criminal Law"
    CIVIL_LAW = "Civil Law"
    COMMERCIAL_LAW = "Commercial Law"
    ISLAMIC_LAW = "Islamic Law"
    ADMINISTRATIVE_LAW = "Administrative Law"
    LABOR_LAW = "Labor Law"
    FAMILY_LAW = "Family Law"
    PROPERTY_LAW = "Property Law"
    CONTRACT_LAW = "Contract Law"
    CORPORATE_LAW = "Corporate Law"
    TAX_LAW = "Tax Law"
    BANKING_LAW = "Banking Law"
    ENVIRONMENTAL_LAW = "Environmental Law"

class LegalDocument(BaseModel, TenantMixin):
    """Enhanced legal document model with Pakistan-specific features"""
    
    # File information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_hash = db.Column(db.String(64), nullable=True)  # SHA-256 hash
    
    # Document classification
    document_type = db.Column(db.Enum(DocumentType), nullable=False)
    court_level = db.Column(db.Enum(CourtLevel), nullable=True)
    jurisdiction = db.Column(db.Enum(Jurisdiction), nullable=True)
    legal_areas = db.Column(ARRAY(db.Enum(LegalArea)), default=list)
    
    # Case/Document details
    case_name = db.Column(db.String(255), nullable=True)
    case_number = db.Column(db.String(100), nullable=True)
    parties = db.Column(JSON, default=dict)  # {'petitioner': [], 'respondent': []}
    judges = db.Column(ARRAY(db.String), default=list)
    
    # Dates
    judgment_date = db.Column(db.Date, nullable=True)
    filing_date = db.Column(db.Date, nullable=True)
    
    # Content and processing
    extracted_text = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    keywords = db.Column(ARRAY(db.String), default=list)
    
    # Citations and references
    extracted_citations = db.Column(JSON, default=list)
    referenced_statutes = db.Column(JSON, default=list)
    precedents_cited = db.Column(JSON, default=list)
    
    # Processing status
    processing_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    extraction_confidence = db.Column(db.Float, nullable=True)
    
    # Vector embeddings
    total_chunks = db.Column(db.Integer, default=0)
    embedding_model = db.Column(db.String(50), default='text-embedding-3-small')
    
    # Metadata
    language = db.Column(db.String(10), default='en')
    tags = db.Column(ARRAY(db.String), default=list)
    custom_metadata = db.Column(JSON, default=dict)
    
    # User and access
    uploaded_by = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    access_level = db.Column(db.String(20), default='private')  # private, team, public
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_documents')
    search_results = db.relationship('SearchResult', backref='document', lazy='dynamic')
    
    def __repr__(self):
        return f'<LegalDocument {self.filename}>'
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def display_name(self):
        """Get display name for document"""
        return self.case_name or self.original_filename
    
    def add_citation(self, citation_text, citation_type, page_number=None):
        """Add a legal citation to the document"""
        if not self.extracted_citations:
            self.extracted_citations = []
        
        citation = {
            'text': citation_text,
            'type': citation_type,
            'page': page_number,
            'extracted_at': datetime.utcnow().isoformat()
        }
        self.extracted_citations.append(citation)
    
    def add_legal_area(self, legal_area):
        """Add legal area to document"""
        if not self.legal_areas:
            self.legal_areas = []
        if legal_area not in self.legal_areas:
            self.legal_areas.append(legal_area)
    
    def get_citation_summary(self):
        """Get summary of citations by type"""
        if not self.extracted_citations:
            return {}
        
        summary = {}
        for citation in self.extracted_citations:
            citation_type = citation.get('type', 'unknown')
            summary[citation_type] = summary.get(citation_type, 0) + 1
        
        return summary

class SearchQuery(BaseModel, TenantMixin):
    """User search queries with enhanced tracking"""
    
    # Query details
    query_text = db.Column(db.Text, nullable=False)
    query_type = db.Column(db.String(50), default='basic')  # basic, advanced, ai, citation
    
    # Filters applied
    filters = db.Column(JSON, default=dict)
    
    # Results
    results_count = db.Column(db.Integer, default=0)
    execution_time_ms = db.Column(db.Integer, nullable=True)
    
    # User and context
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    
    # Search context
    search_context = db.Column(JSON, default=dict)  # Additional context for AI searches
    
    # Relationships
    user = db.relationship('User', backref='search_history')
    results = db.relationship('SearchResult', backref='query', lazy='dynamic')
    
    def __repr__(self):
        return f'<SearchQuery {self.query_text[:50]}>'
    
    @property
    def execution_time_seconds(self):
        """Get execution time in seconds"""
        return self.execution_time_ms / 1000 if self.execution_time_ms else 0

class SearchResult(BaseModel):
    """Individual search results with relevance scoring"""
    
    # Query relationship
    query_id = db.Column(UUID(as_uuid=True), db.ForeignKey('search_query.id'), nullable=False)
    
    # Document relationship
    document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('legal_document.id'), nullable=True)
    
    # Result details
    result_text = db.Column(db.Text, nullable=False)
    relevance_score = db.Column(db.Float, nullable=False)
    confidence_score = db.Column(db.Float, nullable=True)
    
    # Position and context
    result_rank = db.Column(db.Integer, nullable=False)
    chunk_index = db.Column(db.Integer, nullable=True)
    page_number = db.Column(db.Integer, nullable=True)
    
    # Highlighting and snippets
    highlighted_text = db.Column(db.Text, nullable=True)
    context_before = db.Column(db.Text, nullable=True)
    context_after = db.Column(db.Text, nullable=True)
    
    # User interaction
    clicked = db.Column(db.Boolean, default=False)
    clicked_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<SearchResult {self.result_rank}:{self.relevance_score}>'

class Citation(BaseModel):
    """Pakistan legal citations with pattern recognition"""
    
    # Citation text and source
    citation_text = db.Column(db.String(200), nullable=False)
    source_document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('legal_document.id'), nullable=True)
    
    # Citation parsing
    year = db.Column(db.Integer, nullable=True)
    reporter = db.Column(db.String(20), nullable=True)  # PLD, SCMR, CLR, MLD, etc.
    volume = db.Column(db.String(20), nullable=True)
    page = db.Column(db.Integer, nullable=True)
    court = db.Column(db.String(100), nullable=True)
    
    # Citation type and category
    citation_type = db.Column(db.String(20), nullable=False)  # case, statute, article
    reporter_series = db.Column(db.String(50), nullable=True)
    
    # Verification and linking
    is_verified = db.Column(db.Boolean, default=False)
    target_document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('legal_document.id'), nullable=True)
    
    # Context
    context_text = db.Column(db.Text, nullable=True)
    page_reference = db.Column(db.Integer, nullable=True)
    
    # Relationships
    source_document = db.relationship('LegalDocument', foreign_keys=[source_document_id])
    target_document = db.relationship('LegalDocument', foreign_keys=[target_document_id])
    
    def __repr__(self):
        return f'<Citation {self.citation_text}>'
    
    @classmethod
    def parse_pakistan_citation(cls, citation_text):
        """Parse Pakistan legal citation patterns"""
        import re
        
        patterns = {
            'pld': r'(\d{4})\s+(PLD)\s+(\d+)\s+(\w+)',
            'scmr': r'(\d{4})\s+(SCMR)\s+(\d+)',
            'clr': r'(\d{4})\s+(CLR)\s+(\d+)',
            'mld': r'(\d{4})\s+(MLD)\s+(\d+)\s+(\w+)',
            'ylr': r'(\d{4})\s+(YLR)\s+(\d+)',
            'plc': r'(\d{4})\s+(PLC)\s+(\d+)'
        }
        
        for pattern_name, pattern in patterns.items():
            match = re.search(pattern, citation_text, re.IGNORECASE)
            if match:
                groups = match.groups()
                return {
                    'citation_type': 'case',
                    'year': int(groups[0]),
                    'reporter': groups[1].upper(),
                    'volume': groups[2],
                    'court': groups[3] if len(groups) > 3 else '',
                    'reporter_series': pattern_name.upper()
                }
        
        return None

from datetime import datetime