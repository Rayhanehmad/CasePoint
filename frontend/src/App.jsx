import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Navbar from './components/Navbar'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import UnifiedSearch from './pages/UnifiedSearch'
import CaseDetailPage from './pages/CaseDetailPage'
import ActsPage from './pages/ActsPage'
import CompareCasesPage from './pages/CompareCasesPage'
import AIAnalysisPage from './pages/AIAnalysisPage'
import CaseAnalyzerPage from './pages/CaseAnalyzerPage'
import CitationGenerator from './pages/CitationGenerator'
import AdminPage from './pages/AdminPage'
import EmbedView from './pages/EmbedView'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  const { user, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-royal-600"></div>
      </div>
    )
  }

  return (
    <Routes>
      {/* Embed route without navbar (for iframe) */}
      <Route path="/embed/:id" element={<EmbedView />} />
      
      {/* Main app with navbar */}
      <Route path="*" element={
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <main>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              
              {/* Legal research routes */}
              <Route path="/search" element={<UnifiedSearch />} />
              
              {/* Legacy search route redirects */}
              <Route path="/keyword-search" element={<Navigate to="/search?tab=keyword" replace />} />
              <Route path="/citation-search" element={<Navigate to="/search?tab=citation" replace />} />
              <Route path="/advanced-search" element={<Navigate to="/search?tab=advanced" replace />} />
              
              <Route path="/cases/:id" element={<CaseDetailPage />} />
              <Route path="/acts" element={<ActsPage />} />
              <Route path="/compare" element={<CompareCasesPage />} />
              <Route path="/ai-analysis" element={<AIAnalysisPage />} />
              <Route path="/case-analyzer" element={<CaseAnalyzerPage />} />
              <Route path="/citation-generator" element={<CitationGenerator />} />
              
              {/* Protected admin route */}
              <Route 
                path="/admin" 
                element={
                  <ProtectedRoute requireAdmin>
                    <AdminPage />
                  </ProtectedRoute>
                } 
              />
            </Routes>
          </main>
        </div>
      } />
    </Routes>
  )
}

export default App
