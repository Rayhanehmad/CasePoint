import React, { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { 
  Search, 
  FileText, 
  Scale,
  User,
  Users,
  BookOpen,
  FileCheck,
  Hash
} from 'lucide-react'
import api from '../services/api'

const AdvancedSearch = () => {
  const [searchResults, setSearchResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const { register, watch } = useForm()

  // Watch all form fields for changes
  const watchedFields = watch()

  // Debounced search on field changes
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      performSearch()
    }, 500) // 500ms debounce

    return () => clearTimeout(delayDebounceFn)
  }, [watchedFields])

  const performSearch = async () => {
    // Check if at least one field is filled
    const hasInput = Object.values(watchedFields).some(val => val && val.trim())
    
    if (!hasInput) {
      setSearchResults([])
      return
    }

    setIsLoading(true)

    try {
      const response = await api.post('/advanced_search', watchedFields)
      
      if (response.data.success) {
        setSearchResults(response.data.results || [])
      } else {
        setSearchResults([])
      }
    } catch (error) {
      console.error('Search error:', error)
      setSearchResults([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearchClick = () => {
    performSearch()
    toast.success('Search updated')
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Advanced Legal Search</h1>
        <p className="text-gray-600">
          Comprehensive search with multiple criteria. Results update automatically as you type.
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Court */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Scale className="inline w-4 h-4 mr-1" />
              Court
            </label>
            <input
              type="text"
              {...register('court')}
              placeholder="e.g., Supreme Court, High Court"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Judge */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <User className="inline w-4 h-4 mr-1" />
              Judge
            </label>
            <input
              type="text"
              {...register('judge')}
              placeholder="e.g., Justice Khan"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Lawyer */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <User className="inline w-4 h-4 mr-1" />
              Lawyer
            </label>
            <input
              type="text"
              {...register('lawyer')}
              placeholder="e.g., Advocate Ali"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Parties */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Users className="inline w-4 h-4 mr-1" />
              Parties
            </label>
            <input
              type="text"
              {...register('parties')}
              placeholder="e.g., Muhammad Khan vs State"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Keywords */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Search className="inline w-4 h-4 mr-1" />
              Keywords
            </label>
            <input
              type="text"
              {...register('keywords')}
              placeholder="e.g., contract dispute, negligence"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="mt-1 text-xs text-gray-500">Search across case content, summary, and keywords</p>
          </div>

          {/* Rules */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <FileCheck className="inline w-4 h-4 mr-1" />
              Rules
            </label>
            <input
              type="text"
              {...register('rules')}
              placeholder="e.g., Rule 3, Order VII"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Acts */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <BookOpen className="inline w-4 h-4 mr-1" />
              Acts
            </label>
            <input
              type="text"
              {...register('acts')}
              placeholder="e.g., Contract Act 1872"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Section */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Hash className="inline w-4 h-4 mr-1" />
              Section
            </label>
            <input
              type="text"
              {...register('section')}
              placeholder="e.g., Section 10, Article 25"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Search Button */}
        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={handleSearchClick}
            disabled={isLoading}
            className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-medium rounded-md hover:from-emerald-600 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Searching...
              </>
            ) : (
              <>
                <Search className="w-5 h-5 mr-2" />
                Search Now
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results Section */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Searching...</p>
        </div>
      )}

      {!isLoading && searchResults.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Search Results ({searchResults.length})
          </h2>
          <div className="grid grid-cols-1 gap-4">
            {searchResults.map((result) => (
              <div
                key={result.id}
                className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {result.citation || 'No Citation'}
                    </h3>
                    {result.title && (
                      <p className="text-gray-700 font-medium mb-2">{result.title}</p>
                    )}
                    {result.party_line && (
                      <p className="text-sm text-gray-600 mb-2">{result.party_line}</p>
                    )}
                  </div>
                </div>

                <div className="flex flex-wrap gap-3 mb-4">
                  {result.court && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      <Scale className="w-3 h-3 mr-1" />
                      {result.court}
                    </span>
                  )}
                  {result.journal && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                      <FileText className="w-3 h-3 mr-1" />
                      {result.journal}
                    </span>
                  )}
                  {result.year && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {result.year}
                    </span>
                  )}
                  {result.legal_area && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      {result.legal_area}
                    </span>
                  )}
                  {result.jurisdiction && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                      {result.jurisdiction}
                    </span>
                  )}
                </div>

                {result.summary && (
                  <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                    {result.summary}
                  </p>
                )}

                {result.preview && (
                  <p className="text-gray-500 text-xs mb-4 italic line-clamp-2">
                    {result.preview}
                  </p>
                )}

                <div className="flex justify-end">
                  <Link
                    to={`/cases/${result.id}`}
                    className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white text-sm font-medium rounded-md hover:from-blue-700 hover:to-blue-800"
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    View Full Text
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {!isLoading && searchResults.length === 0 && Object.values(watchedFields).some(val => val && val.trim()) && (
        <div className="text-center py-12 bg-white rounded-lg shadow-md">
          <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 font-medium">No results found</p>
          <p className="text-gray-500 text-sm mt-2">Try different search criteria</p>
        </div>
      )}

      {/* Initial State */}
      {!isLoading && searchResults.length === 0 && !Object.values(watchedFields).some(val => val && val.trim()) && (
        <div className="text-center py-12">
          <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">
            Enter search criteria above to find legal documents
          </p>
          <p className="text-gray-500 text-sm mt-2">
            Results will appear automatically as you type
          </p>
        </div>
      )}
    </div>
  )
}

export default AdvancedSearch
