import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { 
  Search, 
  FileText, 
  Calendar,
  MapPin,
  User,
  Scale,
  Users,
  Hash
} from 'lucide-react'
import api from '../services/api'

const CitationSearch = () => {
  const [searchResults, setSearchResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm()

  const onSubmit = async (data) => {
    // Check if at least one field is filled
    const hasInput = Object.values(data).some(val => val && val.trim())
    
    if (!hasInput) {
      toast.error('Please fill in at least one search field')
      return
    }

    setIsLoading(true)
    setSearchResults([])

    try {
      const response = await api.post('/search_citations', data)
      
      if (response.data.success) {
        setSearchResults(response.data.results || [])
        toast.success(`Found ${response.data.total} results`)
      } else {
        toast.error('Search failed')
      }
    } catch (error) {
      console.error('Search error:', error)
      toast.error(error.response?.data?.error || 'Search failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Citation Search</h1>
        <p className="text-gray-600">
          Search for legal citations using metadata fields like journal, court, year, and parties
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Journal */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <FileText className="inline w-4 h-4 mr-1" />
                Journal
              </label>
              <input
                type="text"
                {...register('journal')}
                placeholder="e.g., PLD, SCMR, MLD"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="mt-1 text-xs text-gray-500">Legal journal abbreviation</p>
            </div>

            {/* Year */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="inline w-4 h-4 mr-1" />
                Year
              </label>
              <input
                type="text"
                {...register('year')}
                placeholder="e.g., 2023"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="mt-1 text-xs text-gray-500">Publication year</p>
            </div>

            {/* Page Number */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Hash className="inline w-4 h-4 mr-1" />
                Page No.
              </label>
              <input
                type="text"
                {...register('page_no')}
                placeholder="e.g., 123"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="mt-1 text-xs text-gray-500">Page number in citation</p>
            </div>

            {/* Court */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Scale className="inline w-4 h-4 mr-1" />
                Court
              </label>
              <input
                type="text"
                {...register('court')}
                placeholder="e.g., Supreme Court"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="mt-1 text-xs text-gray-500">Court name</p>
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
              <p className="mt-1 text-xs text-gray-500">Judge name</p>
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
              <p className="mt-1 text-xs text-gray-500">Lawyer/Advocate name</p>
            </div>

            {/* Parties */}
            <div className="md:col-span-2">
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
              <p className="mt-1 text-xs text-gray-500">Party names in the case</p>
            </div>
          </div>

          {/* Search Button */}
          <div className="mt-6 flex justify-end">
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-md hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Searching...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5 mr-2" />
                  Search Citations
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Results Section */}
      {searchResults.length > 0 && (
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
                      <Calendar className="w-3 h-3 mr-1" />
                      {result.year}
                    </span>
                  )}
                  {result.legal_area && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      {result.legal_area}
                    </span>
                  )}
                </div>

                {result.summary && (
                  <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                    {result.summary}
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
      {!isLoading && searchResults.length === 0 && (
        <div className="text-center py-12">
          <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">
            Enter search criteria above to find legal citations
          </p>
        </div>
      )}
    </div>
  )
}

export default CitationSearch
