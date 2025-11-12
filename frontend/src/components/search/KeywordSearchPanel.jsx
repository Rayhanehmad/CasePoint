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

      {/* Search Results - Table Format */}
      {results.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Citation
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Court
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {results.map((result) => (
                <tr key={result.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <FileText className="w-4 h-4 text-gray-400 mr-2" />
                      <span className="text-sm font-medium text-gray-900">
                        {result.citation}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <Scale className="w-4 h-4 text-gray-400 mr-2" />
                      <span className="text-sm text-gray-900">
                        {result.court || 'N/A'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <Link
                      to={`/cases/${result.id}`}
                      className="inline-flex items-center text-green-600 hover:text-green-700 font-medium gap-1"
                    >
                      <Eye className="w-4 h-4" />
                      View Full Citation
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

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
