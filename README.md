# CasePoint - Legal Research Platform

**Modern Full-Stack Legal Research Application for Pakistan Law**

CasePoint is a comprehensive legal research platform designed for lawyers, law firms, and legal professionals in Pakistan. Built with a modern tech stack combining Flask (Python) backend and React frontend, the application provides intelligent legal research capabilities, document management, and AI-powered analysis.

---

## 🎯 Overview

CasePoint combines traditional legal research with modern AI capabilities to help legal professionals:
- Search and browse Pakistan legal cases, acts, and statutes
- Upload and process legal documents (PDF, DOCX)
- Get AI-powered legal analysis and case recommendations
- Compare cases side-by-side
- Manage citations and legal research efficiently

---

## 🏗️ Project Structure

```
/casepoint/
├── backend/                    # Flask backend (Python)
│   ├── models/                 # SQLAlchemy database models
│   │   ├── user.py            # User authentication model
│   │   └── case.py            # Legal citation/case model
│   ├── routes/                 # Flask blueprints/routes
│   │   ├── auth_routes.py     # Authentication (login, register)
│   │   ├── case_routes.py     # Case search and details
│   │   ├── act_routes.py      # Acts and statutes
│   │   ├── ai_routes.py       # AI analysis endpoints
│   │   ├── admin_routes.py    # Admin management
│   │   └── api_routes.py      # REST API for React frontend
│   ├── services/               # Business logic layer
│   │   ├── ai_service.py      # OpenAI integration
│   │   ├── ocr_service.py     # Document text extraction
│   │   └── vector_search.py   # ChromaDB semantic search
│   ├── templates/              # Jinja2 HTML templates
│   ├── static/                 # CSS, JS, images
│   ├── app.py                  # Flask application factory
│   ├── config.py               # Configuration settings
│   ├── admin.py                # Flask-Admin setup
│   └── requirements.txt        # Python dependencies
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/         # Reusable React components
│   │   │   ├── Navbar.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   ├── pages/              # Page components
│   │   │   ├── LandingPage.jsx      # Homepage
│   │   │   ├── SearchPage.jsx       # Search results
│   │   │   ├── CaseDetailPage.jsx   # Case details
│   │   │   ├── ActsPage.jsx         # Acts & Statutes
│   │   │   ├── Dashboard.jsx        # User dashboard
│   │   │   ├── LoginPage.jsx        # Authentication
│   │   │   ├── RegisterPage.jsx
│   │   │   ├── AdminPage.jsx        # Admin panel
│   │   │   ├── AIAnalysisPage.jsx   # AI analysis
│   │   │   └── CompareCasesPage.jsx
│   │   ├── services/           # API service layer
│   │   │   ├── api.js          # Axios configuration
│   │   │   ├── authService.js  # Auth API calls
│   │   │   └── caseService.js  # Case/Legal API calls
│   │   ├── stores/             # Zustand state management
│   │   │   └── authStore.js
│   │   ├── App.jsx             # Main app component
│   │   └── main.jsx            # Entry point
│   ├── package.json
│   ├── vite.config.js          # Vite configuration
│   └── tailwind.config.js      # TailwindCSS config
│
├── uploads/                    # Document storage
├── chroma_db/                  # ChromaDB vector database
├── main.py                     # Application entry point
└── README.md                   # This file
```

---

## 🚀 Tech Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: PostgreSQL (via SQLAlchemy ORM)
- **Admin Panel**: Flask-Admin
- **AI/ML**: OpenAI GPT-4 integration, ChromaDB (service implemented, integration pending)
- **Document Processing**: PyPDF2, python-docx, pdfplumber
- **Authentication**: Session-based (Flask sessions with cookies)
- **CORS**: Flask-CORS for React integration

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: TailwindCSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Routing**: React Router DOM
- **Icons**: Lucide React
- **Forms**: React Hook Form
- **Notifications**: React Hot Toast

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ (for React frontend)
- PostgreSQL database
- OpenAI API key (for AI features)

### Backend Setup

1. **Install Python dependencies**:
```bash
pip install -r backend/requirements.txt
```

2. **Set environment variables**:
```bash
export DATABASE_URL="postgresql://user:password@localhost/casepoint"
export OPENAI_API_KEY="your-openai-api-key"
export SESSION_SECRET="your-secret-key-here"
export FLASK_ENV="development"
```

3. **Initialize database**:
Database tables are created automatically on first run.

### Frontend Setup

1. **Install Node.js dependencies**:
```bash
cd frontend
npm install
```

---

## 🏃 Running the Application

### Development Mode

**Terminal 1 (Backend - Flask)**:
```bash
python main.py
# Or with gunicorn:
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

**Terminal 2 (Frontend - React)**:
```bash
cd frontend
npm run dev
```

- **Backend**: `http://localhost:5000`
- **Frontend**: `http://localhost:3000`
- **Admin Panel**: `http://localhost:5000/admin`

### Production Build

1. Build React frontend:
```bash
cd frontend
npm run build
```

2. Run with Gunicorn:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

---

## 🔐 Authentication

### Default Admin Credentials
- Username: `admin`
- Password: `admin123`
- Admin panel: `http://localhost:5000/admin`

---

## 📚 REST API Documentation

### Search Endpoint
```http
GET /api/search?q=constitution&category=cases&year=2020

Response:
{
  "success": true,
  "results": [...],
  "total": 150,
  "pages": 8,
  "current_page": 1
}
```

### Case Details
```http
GET /api/case/123

Response:
{
  "success": true,
  "case": {...},
  "related_cases": [...]
}
```

### Upload Document
```http
POST /api/upload
Content-Type: multipart/form-data

FormData:
  - file: <PDF/DOCX file>
  - document_type: "case"
  - title: "Case Title"
```

### All Available Endpoints
```
/api/search           - Universal search
/api/case/:id         - Get case details
/api/cases            - List cases
/api/acts             - List acts/statutes
/api/upload           - Upload document
/api/dashboard/stats  - Dashboard statistics
/api/dashboard/recent - Recent uploads
/api/filters/courts   - Get courts
/api/filters/legal-areas - Get legal areas
/api/filters/years    - Get years
```

---

## 🎨 Frontend Development

### Available Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
```

### Making API Calls

```javascript
import caseService from '../services/caseService'

// Search cases
const results = await caseService.searchCases({
  q: 'contract law',
  category: 'cases',
  year: 2020
})

// Get case details
const caseData = await caseService.getCaseById(123)

// Upload document
const result = await caseService.uploadDocument(file, {
  document_type: 'case',
  title: 'My Case'
})
```

---

## 📋 Key Features

### Backend (Flask)
- ✅ User authentication (session-based)
- ✅ Case search with database filters (court, year, legal area)
- ✅ Document upload (PDF/DOCX with text extraction)
- ✅ AI-powered legal analysis (OpenAI integration available)
- ✅ Flask-Admin dashboard for data management
- ✅ Complete REST API for React frontend
- ✅ CORS configured for frontend integration
- ⏳ Vector similarity search (ChromaDB service implemented, integration pending)
- ⏳ Automated classification (service available, not yet in API layer)

### Frontend (React)
- ✅ Modern responsive UI (TailwindCSS)
- ✅ Landing page with search
- ✅ Advanced search with filters
- ✅ Case details with related cases
- ✅ Acts & statutes browser
- ✅ User dashboard
- ✅ Authentication (login/register)
- ✅ Admin interface
- ✅ AI analysis page

---

## 🔧 Configuration

### Flask Configuration (`backend/config.py`)
```python
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
SECRET_KEY = os.environ.get('SESSION_SECRET')
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
```

### Vite Proxy (`frontend/vite.config.js`)
Automatically proxies API requests to Flask:
```javascript
proxy: {
  '/api': 'http://localhost:5000',
  '/auth': 'http://localhost:5000',
  '/cases': 'http://localhost:5000',
  '/acts': 'http://localhost:5000',
  '/ai': 'http://localhost:5000'
}
```

---

## 🚀 Deployment

### Production Checklist
1. ✅ Set `FLASK_ENV=production`
2. ✅ Use strong `SESSION_SECRET`
3. ✅ Configure PostgreSQL
4. ✅ Build React: `cd frontend && npm run build`
5. ✅ Use Gunicorn production server
6. ✅ Set up HTTPS/SSL
7. ✅ Configure firewall

### Gunicorn Production
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 main:app
```

---

## 🛠️ Future Enhancements

### Planned Features
- [ ] Celery + Redis for background tasks
- [ ] Dark mode toggle in React UI
- [ ] Advanced citation export (PDF/Word)
- [ ] Multi-language support
- [ ] Email notifications
- [ ] Bookmark/favorite cases
- [ ] Collaborative research features

---

## 📝 Project Notes

### Architecture Decisions
- **Modular Flask Backend**: Organized into blueprints for scalability
- **REST API First**: Complete JSON API for React integration
- **Session-Based Auth**: Flask sessions with secure cookies
- **CORS Enabled**: Configured for local dev and production
- **Vite Proxy**: Seamless API calls during development

### Migration Ready
The codebase is structured for easy future migration:
- Backend routes are self-contained blueprints
- All data is returned as JSON via REST API
- AI/OCR services are modular (can become microservices)
- Clear separation between backend and frontend
- Well-documented endpoints and services

---

## 📞 Support

For questions or issues, contact the development team.

---

**CasePoint** - Modern Legal Research Made Simple 📚⚖️
