# KanoonPK - AI Legal Research Assistant

## Overview

KanoonPK is an AI-powered legal research assistant specifically designed for Pakistan law. The application provides an intelligent chat interface where users can ask legal questions and receive answers based on Pakistani laws, case references, and uploaded legal documents. The system combines OpenAI's GPT models with ChromaDB vector search to deliver contextually relevant legal information with proper citations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Web Interface**: Bootstrap-based responsive design with dark theme
- **Chat System**: Real-time messaging interface with JavaScript for dynamic interactions
- **File Management**: Document upload interface for legal document ingestion
- **History Tracking**: Search history display with previous queries and responses
- **PDF Generation**: Client-side PDF download functionality for chat sessions

### Backend Architecture
- **Framework**: Flask web application with RESTful API design
- **Route Structure**: Modular routing for chat, admin, and history functionalities
- **Session Management**: Flask sessions for user state management
- **File Processing**: Multi-format document parser supporting PDF and DOCX files
- **Error Handling**: Comprehensive logging and error management system

### AI Integration
- **Language Model**: OpenAI GPT-5 for natural language processing and legal query responses
- **Embedding Model**: OpenAI text-embedding-3-small for document vectorization
- **Prompt Engineering**: Specialized legal system prompt for Pakistan law focus
- **Context Retrieval**: Similarity search for relevant document chunks

### Data Storage Solutions
- **Vector Database**: ChromaDB persistent storage for document embeddings and semantic search
- **File Storage**: Local filesystem storage for uploaded legal documents
- **Collection Management**: Single "kanoonpk" collection for all legal document vectors
- **Document Chunking**: Text segmentation for optimal retrieval and context management

### Document Processing Pipeline
- **Multi-format Support**: PDF and DOCX document parsing capabilities
- **Text Extraction**: PyPDF2 and python-docx libraries for content extraction
- **Chunking Strategy**: Document segmentation for embedding storage
- **Metadata Handling**: File information and source tracking for citations

### Security and Configuration
- **Environment Variables**: Secure API key management for OpenAI integration
- **File Upload Limits**: 16MB maximum file size restriction
- **Secure Filenames**: Werkzeug secure filename handling
- **Session Security**: Flask secret key configuration for session protection

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