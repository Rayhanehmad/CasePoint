import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Search, MapPin, FileText, Scale, Eye } from 'lucide-react'
import api from '../../services/api'

const KeywordSearchPanel = () => {
  const [keyword, setKeyword] = useState('')
  const [location, setLocation] = useState('')
  const [timeFilter, setTimeFilter] = useState('all')
  const [results, setResults] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    
    if (!keyword.trim() && !location.trim()) {
      toast.error('Please enter a keyword or location to search')
      return
    }

    setLoading(true)
    setResults([])
    setTotal(0)

    try {
      // Build query params
      const params = new URLSearchParams()
      if (keyword.trim()) params.append('q', keyword.trim())
      if (location.trim()) params.append('location', location.trim())
      if (timeFilter !== 'all') params.append('years', timeFilter)
      
      const res = await api.get(`/search/keyword?${params.toString()}`)
      setResults(res.data.results || [])
      setTotal(res.data.total || 0)
      
      if (res.data.total > 0) {
        toast.success(`Found ${res.data.total} results`)
      } else {
        toast.info('No results found')
      }
    } catch (err) {
      console.error('Search error:', err)
      toast.error(err.response?.data?.detail || 'Search failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setKeyword('')
    setLocation('')
    setTimeFilter('all')
    setResults([])
    setTotal(0)
  }

  return (
    <div>
      {/* Search Icon Header */}
      <div className="flex items-center gap-2 mb-4">
        <Search className="w-5 h-5 text-gray-700" />
        <h2 className="text-lg font-semibold text-gray-900">Case Law Search</h2>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          {/* Keyword Input */}
          <div className="md:col-span-5">
            <input
              type="text"
              placeholder="Enter Keyword"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              disabled={loading}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          {/* Location/Court Input */}
          <div className="md:col-span-3">
            <input
              type="text"
              placeholder="KARACHI-HIGH-COURT-SINDH"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              disabled={loading}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent uppercase"
            />
          </div>

          {/* Time Filter Dropdown */}
          <div className="md:col-span-2">
            <select
              value={timeFilter}
              onChange={(e) => setTimeFilter(e.target.value)}
              disabled={loading}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white"
            >
              <option value="5">Last 5 Year</option>
              <option value="10">Last 10 Year</option>
              <option value="15">Last 15 Year</option>
              <option value="20">Last 20 Year</option>
              <option value="all">All</option>
            </select>
          </div>

          {/* Search Button */}
          <div className="md:col-span-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-md font-medium transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>
      </form>

      {/* Result Count */}
      {total > 0 && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            Your Search returned total <span className="font-bold">{total}</span> records from 0 - {Math.min(50, total)}
          </p>
        </div>
      )}

      {/* Search Results - Card Format with Highlighting */}
      {results.length > 0 && (
        <div className="space-y-4">
          {results.map((result) => (
            <div key={result.id} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
              {/* Citation and Metadata */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="w-5 h-5 text-blue-600" />
                    <h3 className="text-lg font-semibold text-gray-900">
                      {result.citation}
                    </h3>
                  </div>
                  
                  {/* Party Line */}
                  {result.party_line && (
                    <p className="text-sm text-gray-600 mb-2">{result.party_line}</p>
                  )}
                  
                  {/* Court and Year */}
                  <div className="flex items-center gap-3 text-sm text-gray-500">
                    {result.court && (
                      <span className="flex items-center gap-1">
                        <Scale className="w-4 h-4" />
                        {result.court}
                      </span>
                    )}
                    {result.year && (
                      <span className="bg-gray-100 px-2 py-1 rounded">
                        {result.year}
                      </span>
                    )}
                    {result.journal && (
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        {result.journal}
                      </span>
                    )}
                  </div>
                </div>
                
                <Link
                  to={`/cases/${result.id}`}
                  className="ml-4 inline-flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md font-medium gap-2 transition-colors"
                >
                  <Eye className="w-4 h-4" />
                  View
                </Link>
              </div>

              {/* Preview with Highlighted Keywords */}
              {result.summary_preview && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-700 leading-relaxed keyword-highlight"
                     dangerouslySetInnerHTML={{ __html: result.summary_preview }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      
      {/* CSS for Keyword Highlighting */}
      <style>{`
        .keyword-highlight mark,
        .keyword-highlight .highlight {
          background-color: #fef3c7;
          color: #b91c1c;
          font-weight: 600;
          padding: 2px 4px;
          border-radius: 2px;
        }
      `}</style>

      {/* Empty State */}
      {!loading && results.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <Search className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No results yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Enter search criteria above to find legal cases
          </p>
        </div>
      )}
    </div>
  )
}

export default KeywordSearchPanel
