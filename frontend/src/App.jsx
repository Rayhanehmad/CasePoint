import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Navbar from './components/Navbar'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import Dashboard from './pages/Dashboard'
import UnifiedSearch from './pages/UnifiedSearch'
import CaseDetailPage from './pages/CaseDetailPage'
import ActsPage from './pages/ActsPage'
import CompareCasesPage from './pages/CompareCasesPage'
import AIAnalysisPage from './pages/AIAnalysisPage'
import CaseAnalyzerPage from './pages/CaseAnalyzerPage'
import CitationGenerator from './pages/CitationGenerator'
import AdminPage from './pages/AdminPage'
import EmbedView from './pages/EmbedView'
import UploadCitationPage from './pages/UploadCitationPage'
import UploadMultiPDFPage from './pages/UploadMultiPDFPage'
import ProfilePage from './pages/ProfilePage'
import SharedExcerptPage from './pages/SharedExcerptPage'
import HowToUsePage from './pages/HowToUsePage'
import ProtectedRoute from './components/ProtectedRoute'
import DocumentsPage from './pages/DocumentsPage'
import SubscriptionPage from './pages/SubscriptionPage'

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
      {/* Special routes without navbar */}
      <Route path="/embed/:id" element={<EmbedView />} />
      <Route path="/shared/:code" element={<SharedExcerptPage />} />
      
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
              <Route path="/how-to-use" element={<HowToUsePage />} />
              
              {/* Dashboard */}
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              />
              
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
              
              {/* Documents and Subscription */}
              <Route 
                path="/documents" 
                element={
                  <ProtectedRoute>
                    <DocumentsPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/subscription" 
                element={
                  <ProtectedRoute>
                    <SubscriptionPage />
                  </ProtectedRoute>
                } 
              />
              
              {/* Upload routes */}
              <Route 
                path="/upload-citation" 
                element={
                  <ProtectedRoute>
                    <UploadCitationPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/upload-multi-pdf" 
                element={
                  <ProtectedRoute>
                    <UploadMultiPDFPage />
                  </ProtectedRoute>
                } 
              />
              
              {/* User profile route */}
              <Route 
                path="/profile" 
                element={
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                } 
              />
              
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
