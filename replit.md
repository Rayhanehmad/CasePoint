# KanoonPK - Multi-Tenant SaaS Legal Research Platform

## Overview

KanoonPK has been transformed into a comprehensive multi-tenant SaaS platform specifically designed for Pakistan law research. The platform provides intelligent legal research capabilities for law firms, legal departments, and legal professionals. Each organization gets their own isolated workspace with advanced AI-powered research tools, document management, team collaboration, and usage analytics. The system combines OpenAI's GPT models with ChromaDB vector search to deliver contextually relevant legal information with proper citations and precedent analysis.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Multi-Tenant SaaS Architecture
- **Tenant Isolation**: Schema-per-tenant approach for strict data separation
- **Subdomain Routing**: Automatic tenant detection via subdomain (tenant.kanoonpk.com)
- **Resource Isolation**: Each tenant gets isolated database schema and document storage
- **Plan-Based Access**: Feature and usage limits based on subscription tiers

### Authentication & Authorization System
- **JWT Authentication**: Secure token-based authentication with tenant context
- **Role-Based Access**: Owner, Admin, Member, Viewer roles with granular permissions
- **Multi-User Support**: Team collaboration within organizations
- **Session Management**: Secure session handling with tenant isolation

### Frontend Architecture
- **Modern UI**: Bootstrap-based responsive dashboard with dark theme
- **Multi-Tab Interface**: Dashboard, Research, Documents, Workspaces, Analytics
- **Real-Time Chat**: Enhanced legal research chat with advanced filters
- **Collaborative Tools**: Shared workspaces and team research features
- **Usage Monitoring**: Real-time display of plan limits and current usage

### Backend Architecture
- **Modular Design**: Separate blueprints for auth, API, admin, and main routes
- **RESTful APIs**: Comprehensive API for all platform functionality
- **Middleware Stack**: Tenant resolution, authentication, and authorization layers
- **Error Handling**: Comprehensive error handling with proper HTTP status codes

### Enhanced Legal Research Engine
- **Pakistan Law Filters**: Jurisdiction, legal area, document type, court level filtering
- **Advanced Search**: Vector similarity search with metadata filtering
- **Citation Extraction**: Automatic Pakistan legal citation recognition (PLD, SCMR, CLR, etc.)
- **Precedent Analysis**: AI-powered similar case and precedent identification
- **Confidence Scoring**: Relevance confidence scores for search results

### Multi-Tenant Data Architecture
- **Public Schema**: Shared tenant, user, subscription, and usage data
- **Tenant Schemas**: Isolated legal documents, queries, and workspaces per tenant
- **PostgreSQL Database**: Full ACID compliance with advanced indexing
- **Vector Storage**: Tenant-isolated ChromaDB collections for document embeddings

### Subscription & Usage Management
- **Multiple Plans**: Free, Lawyer, Firm, Enterprise tiers with different limits
- **Usage Tracking**: Real-time monitoring of queries, documents, storage, users
- **Billing Integration**: Stripe-ready subscription management infrastructure
- **Limit Enforcement**: Automatic enforcement of plan-based usage limits

### Document Management System
- **Multi-Format Processing**: Enhanced PDF, DOCX, TXT processing with metadata extraction
- **Legal Classification**: Automatic document type and legal area classification
- **Jurisdiction Detection**: Pakistan court and jurisdiction identification
- **Advanced Chunking**: Optimized text segmentation for better search results

### Collaboration Features
- **Legal Workspaces**: Shared research environments for teams
- **Query Sharing**: Save and share research queries across team members
- **Document Bookmarking**: Collaborative document organization and annotation
- **Team Analytics**: Usage patterns and research insights for teams

### Security & Compliance
- **Data Isolation**: Complete separation between tenant data
- **Secure Authentication**: JWT tokens with tenant claims and role validation
- **File Security**: Secure upload handling with virus scanning capabilities
- **Audit Logging**: Comprehensive audit trails for all user actions

## External Dependencies

### AI Services
- **OpenAI API**: GPT-5 model for legal question answering and text-embedding-3-small for document vectorization
- **API Key Management**: Environment variable-based secure authentication

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