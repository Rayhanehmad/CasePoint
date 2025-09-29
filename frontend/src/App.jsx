import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Navbar from './components/Navbar'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import Dashboard from './pages/Dashboard'
import SearchPage from './pages/SearchPage'
import DocumentsPage from './pages/DocumentsPage'
import AdminPage from './pages/AdminPage'
import SubscriptionPage from './pages/SubscriptionPage'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  const { user, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          {/* Public routes */}
          <Route 
            path="/login" 
            element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />} 
          />
          <Route 
            path="/register" 
            element={user ? <Navigate to="/dashboard" replace /> : <RegisterPage />} 
          />
          
          {/* Protected routes */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/search" 
            element={
              <ProtectedRoute>
                <SearchPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/documents" 
            element={
              <ProtectedRoute>
                <DocumentsPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute requireAdmin>
                <AdminPage />
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
          
          {/* Default redirect */}
          <Route 
            path="/" 
            element={<Navigate to={user ? "/dashboard" : "/login"} replace />} 
          />
        </Routes>
      </main>
    </div>
  )
}

export default App