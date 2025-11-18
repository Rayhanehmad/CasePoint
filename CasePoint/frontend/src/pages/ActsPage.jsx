import React, { useState, useEffect } from 'react'
import { Search, BookOpen } from 'lucide-react'
import axios from 'axios'

export default function ActsPage() {
  const [acts, setActs] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState('all')

  useEffect(() => {
    fetchActs()
  }, [searchQuery, filterType])

  const fetchActs = async () => {
    try {
      const params = new URLSearchParams()
      if (searchQuery) params.append('q', searchQuery)
      if (filterType !== 'all') params.append('type', filterType)

      const response = await axios.get(`/acts/api/acts?${params}`)
      setActs(response.data.acts || [])
    } catch (error) {
      console.error('Error fetching acts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    fetchActs()
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <h1 className="text-4xl font-bold text-navy-900 mb-8">
          Acts, Statutes & Rules
        </h1>

        {/* Search and Filter */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search acts, statutes, and rules..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-royal-500 focus:border-transparent"
              />
            </div>

            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-royal-500 focus:border-transparent"
            >
              <option value="all">All Types</option>
              <option value="act">Acts</option>
              <option value="statute">Statutes</option>
              <option value="rule">Rules</option>
            </select>

            <button
              type="submit"
              className="px-6 py-2 bg-royal-600 hover:bg-royal-700 text-white font-semibold rounded-lg transition-colors"
            >
              Search
            </button>
          </form>
        </div>

        {/* Results */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-royal-600"></div>
          </div>
        ) : acts.length > 0 ? (
          <div className="grid grid-cols-1 gap-6">
            {acts.map((act) => (
              <div
                key={act.id}
                className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-cyan-100 rounded-lg">
                    <BookOpen className="w-6 h-6 text-cyan-600" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h2 className="text-xl font-bold text-navy-900">
                        {act.title}
                      </h2>
                      <span className="px-3 py-1 bg-royal-100 text-royal-800 text-sm font-medium rounded-full">
                        {act.document_type?.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-gray-600 mb-3">
                      <strong>Citation:</strong> {act.citation}
                      {act.year && ` • ${act.year}`}
                    </p>
                    {act.summary && (
                      <p className="text-gray-700 leading-relaxed">
                        {act.summary}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg">
            <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No results found
            </h3>
            <p className="text-gray-600">
              Try adjusting your search or filter criteria
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
