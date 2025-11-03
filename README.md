# KanoonPK - Professional Legal Research Platform

Modern full-stack legal research platform for Pakistan law with AI-powered search, document analysis, and case comparison.

## Architecture

### Backend (Flask)
- **Location**: `backend_flask/`
- **Port**: 5000
- **Features**:
  - Modular blueprint-based routing
  - Flask-Admin dashboard for data management
  - REST API endpoints for React frontend
  - Bulk CSV upload for citations
  - OpenAI AI-powered legal analysis
  - ChromaDB vector search for semantic search
  - OCR document processing (PDF, DOCX, images)

### Frontend (React)
- **Location**: `frontend/`
- **Port**: 3000
- **Features**:
  - Modern UI with Vite + React + TailwindCSS
  - Navy/Royal Blue/Cyan color scheme
  - Pages: Landing, Search, Case Details, Acts & Rules, Compare Cases, AI Analysis, Admin
  - Responsive design for desktop and mobile

## Running the Application

### Option 1: Both Servers Together (Recommended)

```bash
# Terminal 1 - Flask Backend
python run_flask_backend.py

# Terminal 2 - React Frontend
cd frontend && npm run dev
```

Then visit:
- **React Frontend**: http://localhost:3000
- **Flask API**: http://localhost:5000
- **Flask-Admin**: http://localhost:5000/admin

### Option 2: Flask Backend Only (Original Templates)

```bash
python main.py
```

Visit http://localhost:5000

## Features

### 1. Case Search & Management
- Search thousands of Pakistan law cases
- Filter by court, year, legal area, jurisdiction
- View detailed case information with citations
- Compare multiple cases side by side

### 2. Acts, Statutes & Rules
- Comprehensive collection of Pakistan legal documents
- Full-text search across all acts and statutes
- Organized by document type and year

### 3. AI-Powered Legal Analysis
- Ask legal questions in natural language
- Get AI-generated analysis with relevant citations
- Semantic search using ChromaDB vector database
- Powered by OpenAI GPT models

### 4. Admin Panel (Flask-Admin)
- **Single Citation Upload**: Web form for manual entry
- **Document Upload with OCR**: Upload PDF/DOCX/images with automatic text extraction
- **Bulk CSV Upload**: Upload hundreds of citations at once
- **User Management**: View and manage all users
- **Data Management**: Edit, delete, export cases and acts
- **Statistics Dashboard**: View platform analytics

### 5. Bulk CSV Upload Format

Create a CSV file with these columns:
```csv
document_type,title,citation,court,year,legal_area,summary,full_text
case,Federation v. Gul Hassan Khan,PLD 1976 SC 57,Supreme Court,1976,Constitutional Law,Important constitutional case,Full text here...
act,Pakistan Penal Code,Act XLV of 1860,,1860,Criminal Law,Main criminal law statute,Full text...
```

## Technology Stack

### Backend
- Python 3.11
- Flask 3.0
- Flask-SQLAlchemy (PostgreSQL)
- Flask-Admin (Admin dashboard)
- Flask-CORS (API access)
- OpenAI API (AI analysis)
- ChromaDB (Vector search)
- pdfplumber + PyMuPDF (PDF extraction)
- pytesseract (OCR)

### Frontend
- React 18
- Vite (Build tool)
- TailwindCSS (Styling)
- React Router (Routing)
- Axios (API calls)
- Lucide React (Icons)

### Database
- PostgreSQL (Provided by Replit)
- ChromaDB (Vector database)

## API Endpoints

### Authentication
- `POST /auth/api/register` - Register new user
- `POST /auth/api/login` - Login user
- `POST /auth/api/logout` - Logout user
- `GET /auth/api/me` - Get current user

### Cases
- `GET /cases/api/cases` - List all cases (with filters)
- `GET /cases/api/cases/:id` - Get single case with related cases

### Acts
- `GET /acts/api/acts` - List all acts/statutes/rules
- `GET /acts/api/acts/:id` - Get single act

### AI Analysis
- `POST /ai/api/analyze` - Get AI legal analysis
- `GET /ai/api/status` - Check AI service status

### Admin (requires admin role)
- `GET /admin/api/stats` - Get platform statistics
- `GET /admin/api/recent-uploads` - Get recent uploads
- `POST /admin/api/upload-csv` - Bulk upload via CSV

## Environment Variables

Required:
- `DATABASE_URL` - PostgreSQL connection string (auto-provided by Replit)
- `OPENAI_API_KEY` - OpenAI API key for AI analysis
- `SESSION_SECRET` - Flask session secret

## Development

### Install Dependencies

**Backend:**
```bash
cd backend_flask
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### File Structure

```
/kanoonpk/
├── backend_flask/          # Flask backend (NEW)
│   ├── app.py             # Main Flask app
│   ├── config.py          # Configuration
│   ├── admin.py           # Flask-Admin setup
│   ├── models/            # Database models
│   ├── routes/            # Route blueprints
│   ├── services/          # AI, OCR, vector search
│   ├── templates/         # Jinja2 templates
│   └── static/            # Static assets
├── frontend/              # React frontend (NEW)
│   ├── src/
│   │   ├── pages/        # React pages
│   │   ├── components/   # Reusable components
│   │   └── services/     # API services
│   ├── package.json
│   └── vite.config.js
├── main.py               # Original Flask app (still works)
├── models.py             # Original models
├── vector_search.py      # Vector search service
├── ocr_utils.py          # OCR service
└── README.md             # This file
```

## Admin Access

To access the admin panel:
1. Create an admin user in the database (set `role = 'admin'`)
2. Login with admin credentials
3. Visit `/admin` for Flask-Admin dashboard
4. Or use the React Admin page at `/admin` on port 3000

## Future Enhancements

- JWT token-based API authentication
- User bookmarks/favorites
- Document export (PDF/Word)
- Advanced analytics dashboard
- Email notifications
- Real-time collaboration features

## Credits

Built with ❤️ for Pakistan legal community
