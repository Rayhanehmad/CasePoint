import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, X } from 'lucide-react'
import axios from 'axios'

export default function CompareCasesPage() {
  const [searchParams] = useSearchParams()
  const [cases, setCases] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const ids = searchParams.getAll('ids')
    if (ids.length > 0) {
      fetchCases(ids)
    }
  }, [searchParams])

  const fetchCases = async (ids) => {
    try {
      const promises = ids.map(id => axios.get(`/cases/api/cases/${id}`))
      const responses = await Promise.all(promises)
      setCases(responses.map(r => r.data.case))
    } catch (error) {
      console.error('Error fetching cases:', error)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim()) return

    setLoading(true)
    try {
      const response = await axios.get(`/cases/api/cases?q=${searchQuery}`)
      setSearchResults(response.data.cases || [])
    } catch (error) {
      console.error('Error searching cases:', error)
    } finally {
      setLoading(false)
    }
  }

  const addCase = (caseData) => {
    if (cases.length < 4 && !cases.find(c => c.id === caseData.id)) {
      setCases([...cases, caseData])
      setSearchResults([])
      setSearchQuery('')
    }
  }

  const removeCase = (caseId) => {
    setCases(cases.filter(c => c.id !== caseId))
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <h1 className="text-4xl font-bold text-navy-900 mb-8">
          Compare Cases
        </h1>

        {/* Add Cases */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-lg font-semibold text-navy-900 mb-4">
            Add Cases to Compare (Max 4)
          </h2>
          
          <form onSubmit={handleSearch} className="flex gap-4 mb-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for cases to add..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-royal-500 focus:border-transparent"
            />
            <button
              type="submit"
              disabled={loading || cases.length >= 4}
              className="px-6 py-2 bg-royal-600 hover:bg-royal-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </form>

          {searchResults.length > 0 && (
            <div className="space-y-2">
              {searchResults.map((result) => (
                <div
                  key={result.id}
                  onClick={() => addCase(result)}
                  className="p-3 border border-gray-200 rounded-lg hover:border-royal-500 hover:bg-gray-50 cursor-pointer"
                >
                  <h3 className="font-semibold text-navy-900">{result.title}</h3>
                  <p className="text-sm text-gray-600">{result.citation}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Comparison Grid */}
        {cases.length > 0 ? (
          <div className={`grid grid-cols-1 ${cases.length > 1 ? 'md:grid-cols-2' : ''} gap-6`}>
            {cases.map((caseData) => (
              <div key={caseData.id} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex justify-between items-start mb-4">
                  <h2 className="text-xl font-bold text-navy-900 flex-1">
                    {caseData.title}
                  </h2>
                  <button
                    onClick={() => removeCase(caseData.id)}
                    className="text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="space-y-3">
                  <div>
                    <span className="font-semibold text-gray-700">Citation:</span>
                    <p className="text-gray-900">{caseData.citation}</p>
                  </div>

                  <div>
                    <span className="font-semibold text-gray-700">Court:</span>
                    <p className="text-gray-900">{caseData.court || 'N/A'}</p>
                  </div>

                  <div>
                    <span className="font-semibold text-gray-700">Year:</span>
                    <p className="text-gray-900">{caseData.year || 'N/A'}</p>
                  </div>

                  <div>
                    <span className="font-semibold text-gray-700">Legal Area:</span>
                    <p className="text-gray-900">{caseData.legal_area || 'N/A'}</p>
                  </div>

                  {caseData.summary && (
                    <div>
                      <span className="font-semibold text-gray-700">Summary:</span>
                      <p className="text-gray-700 text-sm mt-1">{caseData.summary}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg">
            <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No cases added yet
            </h3>
            <p className="text-gray-600">
              Search and add cases to compare them side by side
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
