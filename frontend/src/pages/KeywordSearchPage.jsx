import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Search, FileText } from 'lucide-react'
import api from '../services/api'

const KeywordSearchPage = () => {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    
    if (!query.trim()) {
      toast.error('Please enter a keyword to search')
      return
    }

    setLoading(true)
    setResults([])
    setTotal(0)

    try {
      const res = await api.get(`/search/keyword?q=${encodeURIComponent(query)}`)
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

  const handleCaseClick = (caseId) => {
    navigate(`/cases/${caseId}`)
  }

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="card">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Keyword Search</h1>
        <p className="text-gray-600 mb-6">
          Search across all case citations, summaries, and full text with highlighted results
        </p>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by keyword (e.g., contract, criminal act, constitution...)"
              className="input-field"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="btn-primary flex items-center px-6"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Searching...
              </>
            ) : (
              <>
                <Search className="h-4 w-4 mr-2" />
                Search
              </>
            )}
          </button>
        </form>
      </div>

      {/* Total Results */}
      {total > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-gray-800">
            Your search returned <span className="font-bold text-blue-700">{total}</span> record{total !== 1 ? 's' : ''}.
          </p>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          {results.map((item) => (
            <div 
              key={item.id} 
              className="card hover:shadow-lg transition-shadow duration-200 cursor-pointer"
              onClick={() => handleCaseClick(item.id)}
            >
              {/* Citation Title */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h2 className="text-lg font-bold text-blue-700 hover:text-blue-800">
                    {item.citation}
                  </h2>
                  
                  {/* Party Names */}
                  {item.party_line && (
                    <p className="text-sm text-gray-800 font-medium mt-1">
                      {item.party_line}
                    </p>
                  )}
                  
                  {/* Court and Journal Info */}
                  <div className="flex flex-wrap gap-3 mt-2 text-sm text-gray-600">
                    {item.court && (
                      <span className="flex items-center">
                        <FileText className="h-3 w-3 mr-1" />
                        {item.court}
                      </span>
                    )}
                    {item.journal && (
                      <span className="px-2 py-0.5 bg-gray-100 text-gray-800 rounded-full text-xs font-medium">
                        {item.journal}
                      </span>
                    )}
                    {item.year && (
                      <span className="text-gray-500">
                        Year: {item.year}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Highlighted Preview (HTML safe) */}
              {item.summary_preview && (
                <div
                  className="mt-3 text-gray-800 leading-relaxed text-sm"
                  dangerouslySetInnerHTML={{ __html: item.summary_preview }}
                />
              )}
            </div>
          ))}
        </div>
      )}

      {/* No Results */}
      {!loading && results.length === 0 && query && total === 0 && (
        <div className="text-center py-12 card">
          <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p className="text-gray-600">
            Try different keywords or check your spelling.
          </p>
        </div>
      )}
    </div>
  )
}

export default KeywordSearchPage
