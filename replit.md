# CasePoint - Modern Legal Research Platform

## Overview

CasePoint (formerly KanoonPK) is a full-stack legal research platform for Pakistan law. The application has been restructured into a modern, modular architecture with a Flask backend and React frontend, ready for production deployment. The platform provides intelligent legal research capabilities using AI-powered search, document management, and case analysis. The system combines OpenAI's GPT models with ChromaDB vector search to deliver contextually relevant legal information with proper citations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Architecture (Fully Migrated to React SPA - November 2025)
- **Pure API Backend**: Flask configured as a pure REST API with no template rendering
- **React SPA Frontend**: Complete migration from Flask Jinja2 templates to React Single Page Application
- **SPA Routing**: Flask serves React build from `frontend/dist` with catch-all route for client-side routing
- **API-Only Blueprints**: Flask only registers `api_bp` and `auth_bp` - all UI handled by React
- **CORS Enabled**: Configured for seamless React frontend communication during development

### Authentication & Authorization System
- **Session Authentication**: Secure session-based authentication with Flask sessions
- **Role-Based Access**: Admin and User roles for access control
- **Multi-User Support**: Multiple user accounts with personal dashboards
- **Session Management**: Secure cookie-based session handling

### Frontend Architecture (Complete React Migration - November 2025)
- **Modern UI**: React 18 + Vite + TailwindCSS for responsive design
- **Dark Theme Design**: Production-ready dark glassmorphism UI across all pages
  - Consistent dark gradient backgrounds (slate-900 via blue-950 to slate-800)
  - Glassmorphism effects with backdrop-blur and translucent rgba backgrounds
  - Professional typography using Orbitron (headings), Exo 2 (subheadings), and Inter (body text)
  - Glowing text animations for AI-powered sections
  - Tailwind CSS v4 with @tailwindcss/vite plugin
- **Component-Based**: Reusable components with clean separation
- **Service Layer**: Dedicated API service files (authService, caseService)
- **State Management**: Zustand for lightweight state management
- **Routing**: React Router DOM for complete client-side navigation
- **All Pages in React**: Complete set of React pages including:
  - Public: LandingPage, LoginPage, RegisterPage, HowToUsePage
  - Search: UnifiedSearch (with keyword, citation, advanced tabs), CaseDetailPage, ActsPage
  - AI Features: AIAnalysisPage, CaseAnalyzerPage, CitationGenerator
  - Upload: UploadCitationPage, UploadMultiPDFPage (protected)
  - User: ProfilePage (protected), SharedExcerptPage
  - Admin: AdminPage (admin-only)
  - Special: EmbedView (iframe embedding)
- **Protected Routes**: Authentication guards using ProtectedRoute component
- **Proxy Configuration**: Vite proxy for seamless API communication during development

### Backend Architecture (API-Only - November 2025)
- **Pure REST API**: Flask configured as backend API only, no template rendering
- **API Endpoints** (`api_routes.py`):
  - Search: `/api/search`, `/api/keyword_search`, `/api/search_citations`
  - Citations: `/api/citations/<id>`, `/api/related_cases/<id>`
  - Acts: `/api/acts`
  - Uploads: `/api/upload_citation`, `/api/upload_multi_pdf`
  - AI Generation: `/api/generate_summary/<id>`, `/api/generate_headnotes/<id>`
  - AI Analysis: `/api/auto_counter_arguments`, `/api/analyze_case`, `/api/which_laws_apply`, `/api/generate_citation`
  - User: `/api/profile` (GET/PUT)
  - Sharing: `/api/shared/<code>`, `/api/share_excerpt`
- **Authentication API** (`auth_routes.py`):
  - `/auth/register` (JSON API)
  - `/auth/login` (JSON API)
  - `/auth/logout` (JSON API)
  - `/auth/session` (check session status)
- **SPA Serving**: Catch-all route serves React build from `frontend/dist`
- **Error Handling**: JSON error responses with proper HTTP status codes
- **CORS Configuration**: Configured for React frontend during development

### Legal Research Features
- **Pakistan Law Filters**: Jurisdiction, legal area, document type, court level, journal filtering via SQL
- **Database Search**: Full-text search across cases, acts, and statutes
- **Journal Auto-Extraction**: Automatic extraction and indexing of legal journals (PLD, MLD, SCMR, YLR, CLC, CLD, PCrLJ, PTD, PLC) from citation text
- **Related Cases**: Find similar cases by legal area
- **AI Analysis**: OpenAI-powered legal question answering (via /ai routes)
- **AI Case Analyzer**: Comprehensive case analysis tool with three integrated features:
  - `/api/auto_counter_arguments` - GPT-4 powered counter arguments generation from prosecution narratives
  - `/api/analyze_case` - Automatic citation and statute detection with database matching
  - `/api/which_laws_apply` - Smart detection of applicable laws/sections using regex patterns
  - React frontend at `/case-analyzer` with 3-column results layout and modal-based law display
- **One-Click Excerpt Sharing** (November 2025):
  - Text selection sharing on citation detail pages
  - UUID-based shareable links with 90-day expiration
  - Public excerpt viewing with Open Graph meta tags for social media
  - Deduplication and rate limiting (50 shares per user per day)
  - View tracking and analytics
  - Social media sharing buttons (Twitter, Facebook, LinkedIn, WhatsApp)
  - API endpoints: `POST /api/share_excerpt`, `GET /api/shared/<code>`, `GET /shared/<code>` (HTML)
- **Usage Analytics**: Built-in tracking for share counts, embed views, and last activity timestamps
- **Services Available**: Vector search (ChromaDB) and classification services implemented but not yet integrated into main API

### Database Architecture
- **PostgreSQL Database**: SQLAlchemy ORM with full ACID compliance
- **User Management**: User accounts with authentication and profiles
- **Legal Citations**: Cases, acts, statutes with metadata and full-text
  - Auto-extracted journal field (indexed for fast filtering)
  - Usage tracking fields: share_count, embed_views, last_shared, last_embedded
- **Shared Excerpts**: One-click sharing system for legal document excerpts (November 2025)
  - UUID share codes for unique public links
  - Automatic deduplication via SHA256 hashing
  - Configurable expiration (default 90 days) and revocation support
  - View count tracking without PII collection
  - Indexed fields for performance: excerpt_hash, citation_id, created_at, expires_at
- **Vector Storage**: ChromaDB for document embeddings and semantic search

### Document Management System
- **Multi-Format Processing**: PDF and DOCX text extraction using pdfplumber and python-docx
- **File Upload**: Secure document upload with file type validation
- **Database Storage**: Citation metadata and full-text stored in PostgreSQL
- **OCR Services**: OCR extraction service available in backend/services/ocr_service.py
- **Smart Metadata Extraction**: Automatic journal extraction from citation text during upload
- **Batch Processing**: Backfill script (backend/backfill_journals.py) for updating existing citations


### Security Features
- **Secure Authentication**: Session-based authentication with secure cookies
- **File Security**: Secure upload handling with file type validation
- **CORS Protection**: Properly configured CORS for React frontend
- **Password Hashing**: Werkzeug password hashing for user credentials

## External Dependencies

### AI Services
- **OpenAI API**: GPT-4 model for legal question answering and text-embedding-3-small for document vectorization
- **API Key Management**: Environment variable-based secure authentication (OPENAI_API_KEY)

### Database and Storage
- **ChromaDB**: Vector database for persistent storage of document embeddings and similarity search
- **Local File System**: Document storage in uploads directory

### Document Processing Libraries
- **PyPDF2**: PDF document text extraction and parsing
- **python-docx**: Microsoft Word document processing
- **ReportLab**: PDF generation for chat session exports

### Web Framework and UI
- **Flask**: Python web framework for backend API and routing
- **Tailwind CSS**: Modern utility-first CSS framework via CDN for rapid UI development
- **Bootstrap**: Frontend styling framework coexisting with Tailwind for specific components
- **Google Fonts**: Orbitron, Exo 2, and Inter for professional typography
- **Font Awesome**: Icon library for user interface elements
- **Werkzeug**: File upload security and utilities

### UI/UX Design System (November 2025)
- **Color Palette**: Dark gradients using Tailwind slate-900, blue-950, and slate-800
- **Glassmorphism**: Translucent backgrounds with backdrop-blur-xl and rgba opacity
- **Typography Hierarchy**:
  - Headings: Orbitron font with glow effects for emphasis
  - Subheadings: Exo 2 font with medium weight
  - Body: Inter font for optimal readability
- **AI Section Styling**: Glowing text animations and special emphasis for AI-powered features
- **Interactive Elements**: Hover effects with scale transforms and gradient shifts
- **Responsive Design**: Mobile-first approach with responsive breakpoints
- **Updated Templates**: All major pages transformed with consistent dark theme
  - Homepage: Dashboard with user stats and quick actions
  - Citation Detail: Glassmorphic cards with glowing AI Summary and Headnotes
  - Search Results: Dark cards with gradient hover effects
  - Upload Multi-PDF: Glassmorphic upload area with progress indicators
  - AI Analysis: Futuristic dark theme matching dashboard
  - Case Analyzer: Three-column results layout with dark glassmorphic cards

### Development and Deployment (November 2025)
- **Backend**: Flask as pure REST API backend (no templates)
- **Frontend**: React + Vite SPA served from Flask
- **Build Process**: `npm run build` creates production build in `frontend/dist`
- **Development**: Vite dev server (port 5173) with proxy to Flask (port 5000)
- **Production**: Flask serves React build directly from `frontend/dist`
- **Migration Complete**: All Flask templates migrated to React components