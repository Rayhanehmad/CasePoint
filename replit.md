# CasePoint - Modern Legal Research Platform

## Overview

CasePoint (formerly KanoonPK) is a full-stack legal research platform for Pakistan law. The application has been restructured into a modern, modular architecture with a Flask backend and React frontend, ready for production deployment. The platform provides intelligent legal research capabilities using AI-powered search, document management, and case analysis. The system combines OpenAI's GPT models with ChromaDB vector search to deliver contextually relevant legal information with proper citations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Architecture
- **Modular Backend**: Flask application organized into blueprints for clean separation of concerns
- **REST API**: Complete JSON API layer for React frontend integration
- **Blueprint Structure**: Separate blueprints for auth, cases, acts, AI, admin, and API routes
- **CORS Enabled**: Configured for seamless React frontend communication

### Authentication & Authorization System
- **Session Authentication**: Secure session-based authentication with Flask sessions
- **Role-Based Access**: Admin and User roles for access control
- **Multi-User Support**: Multiple user accounts with personal dashboards
- **Session Management**: Secure cookie-based session handling

### Frontend Architecture
- **Modern UI**: React 18 + Vite + TailwindCSS for responsive design
- **Component-Based**: Reusable components with clean separation
- **Service Layer**: Dedicated API service files (authService, caseService)
- **State Management**: Zustand for lightweight state management
- **Routing**: React Router DOM for client-side navigation
- **Proxy Configuration**: Vite proxy for seamless API communication during development

### Backend Architecture
- **Blueprint Organization**: 
  - `auth_routes.py` - User authentication (login, register, logout)
  - `case_routes.py` - Case search and details
  - `act_routes.py` - Acts and statutes
  - `ai_routes.py` - AI-powered legal analysis
  - `admin_routes.py` - Admin management endpoints
  - `api_routes.py` - Consolidated REST API for React frontend
- **RESTful APIs**: Complete JSON API endpoints for all platform functionality
- **Flask-Admin**: Integrated admin dashboard at `/admin` route
- **Error Handling**: Comprehensive error handling with proper HTTP status codes
- **CORS Configuration**: Properly configured for React frontend at localhost:3000 and localhost:5173

### Legal Research Features
- **Pakistan Law Filters**: Jurisdiction, legal area, document type, court level, journal filtering via SQL
- **Database Search**: Full-text search across cases, acts, and statutes
- **Journal Auto-Extraction**: Automatic extraction and indexing of legal journals (PLD, MLD, SCMR, YLR, CLC, CLD, PCrLJ, PTD, PLC) from citation text
- **Related Cases**: Find similar cases by legal area
- **AI Analysis**: OpenAI-powered legal question answering (via /ai routes)
- **Usage Analytics**: Built-in tracking for share counts, embed views, and last activity timestamps
- **Services Available**: Vector search (ChromaDB) and classification services implemented but not yet integrated into main API

### Database Architecture
- **PostgreSQL Database**: SQLAlchemy ORM with full ACID compliance
- **User Management**: User accounts with authentication and profiles
- **Legal Citations**: Cases, acts, statutes with metadata and full-text
  - Auto-extracted journal field (indexed for fast filtering)
  - Usage tracking fields: share_count, embed_views, last_shared, last_embedded
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
- **Bootstrap**: Frontend styling framework with dark theme support
- **Font Awesome**: Icon library for user interface elements
- **Werkzeug**: File upload security and utilities

### Development and Deployment
- **Python Environment**: Flask development server with debug mode
- **Static Assets**: CSS and JavaScript files for frontend functionality
- **Template Engine**: Jinja2 templating for dynamic HTML generation