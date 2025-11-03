import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Scale, FileText, Sparkles } from 'lucide-react'

export default function LandingPage() {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`)
    }
  }

  return (
    <div className="bg-white">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-br from-navy-900 via-royal-800 to-cyan-900">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-5xl font-bold text-white sm:text-6xl lg:text-7xl">
              KanoonPK
            </h1>
            <p className="mt-6 text-xl text-gray-200 max-w-3xl mx-auto">
              Professional Legal Research Platform for Pakistan Law
            </p>
            <p className="mt-2 text-lg text-gray-300 max-w-2xl mx-auto">
              AI-Powered Citation Search, Document Analysis, and Case Comparison
            </p>

            {/* Search Bar */}
            <form onSubmit={handleSearch} className="mt-10 max-w-2xl mx-auto">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search cases, acts, statutes, and rules..."
                  className="flex-1 px-6 py-4 text-lg rounded-lg border-2 border-transparent focus:border-cyan-400 focus:ring-2 focus:ring-cyan-300 focus:outline-none"
                />
                <button
                  type="submit"
                  className="px-8 py-4 bg-cyan-500 hover:bg-cyan-600 text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
                >
                  <Search className="w-5 h-5" />
                  Search
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-navy-900 text-center mb-12">
            Powerful Legal Research Tools
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white p-8 rounded-xl shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-royal-100 rounded-lg">
                  <Scale className="w-6 h-6 text-royal-600" />
                </div>
                <h3 className="text-xl font-semibold text-navy-900">
                  Case Search
                </h3>
              </div>
              <p className="text-gray-600">
                Search through thousands of Pakistan law cases with advanced filtering by court, year, and legal area.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white p-8 rounded-xl shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-cyan-100 rounded-lg">
                  <FileText className="w-6 h-6 text-cyan-600" />
                </div>
                <h3 className="text-xl font-semibold text-navy-900">
                  Acts & Statutes
                </h3>
              </div>
              <p className="text-gray-600">
                Access comprehensive collection of Pakistan acts, statutes, and rules with full-text search.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white p-8 rounded-xl shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-royal-100 rounded-lg">
                  <Sparkles className="w-6 h-6 text-royal-600" />
                </div>
                <h3 className="text-xl font-semibold text-navy-900">
                  AI Analysis
                </h3>
              </div>
              <p className="text-gray-600">
                Get AI-powered legal analysis and relevant case citations using advanced semantic search.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="py-16 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <button
              onClick={() => navigate('/search?category=cases')}
              className="p-6 bg-navy-900 hover:bg-navy-800 text-white rounded-lg transition-colors text-left"
            >
              <h3 className="text-lg font-semibold mb-2">Browse Cases</h3>
              <p className="text-sm text-gray-300">Supreme Court, High Courts</p>
            </button>

            <button
              onClick={() => navigate('/acts')}
              className="p-6 bg-royal-600 hover:bg-royal-700 text-white rounded-lg transition-colors text-left"
            >
              <h3 className="text-lg font-semibold mb-2">Acts & Statutes</h3>
              <p className="text-sm text-gray-200">Federal & Provincial</p>
            </button>

            <button
              onClick={() => navigate('/compare')}
              className="p-6 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors text-left"
            >
              <h3 className="text-lg font-semibold mb-2">Compare Cases</h3>
              <p className="text-sm text-gray-200">Side-by-side analysis</p>
            </button>

            <button
              onClick={() => navigate('/ai-analysis')}
              className="p-6 bg-navy-700 hover:bg-navy-600 text-white rounded-lg transition-colors text-left"
            >
              <h3 className="text-lg font-semibold mb-2">AI Legal Analysis</h3>
              <p className="text-sm text-gray-200">Powered by OpenAI</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
