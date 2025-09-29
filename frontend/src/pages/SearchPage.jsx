import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { 
  Search, 
  Filter, 
  Download, 
  Eye,
  Sparkles,
  Calendar,
  MapPin,
  FileText
} from 'lucide-react'
import api from '../services/api'
import { useAuthStore } from '../stores/authStore'

const SearchPage = () => {
  const { user } = useAuthStore()
  const [searchResults, setSearchResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchType, setSearchType] = useState('basic')
  const [showFilters, setShowFilters] = useState(false)
  const [aiResponse, setAiResponse] = useState('')
  
  const { register, handleSubmit, watch } = useForm()
  const query = watch('query')

  const searchTypes = [
    { 
      value: 'basic', 
      label: 'Basic Search', 
      description: 'Search database only',
      available: true 
    },
    { 
      value: 'advanced', 
      label: 'Advanced Search', 
      description: 'Search with filters',
      available: user?.subscription_tier !== 'free'
    },
    { 
      value: 'ai_advanced', 
      label: 'AI Advanced', 
      description: 'AI + database search',
      available: user?.subscription_tier !== 'free'
    }
  ]

  const onSubmit = async (data) => {
    if (!data.query?.trim()) {
      toast.error('Please enter a search query')
      return
    }

    setIsLoading(true)
    setSearchResults([])
    setAiResponse('')

    try {
      const searchData = {
        query: data.query,
        search_type: searchType,
        filters: {
          jurisdiction: data.jurisdiction || null,
          court_level: data.court_level || null,
          legal_area: data.legal_area || null,
          date_from: data.date_from || null,
          date_to: data.date_to || null,
          document_type: data.document_type || null
        }
      }

      const response = await api.post('/search', searchData)
      setSearchResults(response.data.results || [])
      
      if (response.data.ai_response) {
        setAiResponse(response.data.ai_response)
      }

      toast.success(`Found ${response.data.total_results} results`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Search failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = async (documentId) => {
    try {
      const response = await api.get(`/documents/${documentId}/download`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `document-${documentId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      toast.error('Download failed')
    }
  }

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="card">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Legal Research Search</h1>
        
        {/* Search Type Selection */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {searchTypes.map((type) => (
            <div
              key={type.value}
              className={`relative p-4 border rounded-lg cursor-pointer transition-all duration-200 ${
                searchType === type.value
                  ? 'border-primary-500 bg-primary-50'
                  : type.available
                  ? 'border-gray-200 hover:border-gray-300'
                  : 'border-gray-200 bg-gray-50 cursor-not-allowed'
              }`}
              onClick={() => type.available && setSearchType(type.value)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className={`font-medium ${
                    type.available ? 'text-gray-900' : 'text-gray-400'
                  }`}>
                    {type.label}
                  </h3>
                  <p className={`text-sm ${
                    type.available ? 'text-gray-600' : 'text-gray-400'
                  }`}>
                    {type.description}
                  </p>
                </div>
                {type.value === 'ai_advanced' && (
                  <Sparkles className={`h-5 w-5 ${
                    type.available ? 'text-yellow-500' : 'text-gray-400'
                  }`} />
                )}
              </div>
              
              {!type.available && (
                <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 rounded-lg">
                  <span className="text-xs font-medium text-gray-500 bg-white px-2 py-1 rounded border">
                    Upgrade Required
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Search Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="flex space-x-4">
            <div className="flex-1">
              <input
                {...register('query')}
                type="text"
                placeholder="Search legal documents, cases, citations..."
                className="input-field"
              />
            </div>
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className="btn-secondary flex items-center"
              disabled={searchType === 'basic'}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary flex items-center"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              ) : (
                <Search className="h-4 w-4 mr-2" />
              )}
              Search
            </button>
          </div>

          {/* Advanced Filters */}
          {showFilters && searchType !== 'basic' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Jurisdiction
                </label>
                <select {...register('jurisdiction')} className="input-field">
                  <option value="">All Jurisdictions</option>
                  <option value="Supreme Court of Pakistan">Supreme Court of Pakistan</option>
                  <option value="Lahore High Court">Lahore High Court</option>
                  <option value="Karachi High Court">Karachi High Court</option>
                  <option value="Islamabad High Court">Islamabad High Court</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Legal Area
                </label>
                <select {...register('legal_area')} className="input-field">
                  <option value="">All Areas</option>
                  <option value="Constitutional Law">Constitutional Law</option>
                  <option value="Contract Law">Contract Law</option>
                  <option value="Criminal Law">Criminal Law</option>
                  <option value="Family Law">Family Law</option>
                  <option value="Commercial Law">Commercial Law</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Type
                </label>
                <select {...register('document_type')} className="input-field">
                  <option value="">All Types</option>
                  <option value="pdf">PDF</option>
                  <option value="jpeg">Image</option>
                  <option value="txt">Text</option>
                </select>
              </div>
            </div>
          )}
        </form>
      </div>

      {/* AI Response */}
      {aiResponse && (
        <div className="card bg-gradient-to-r from-yellow-50 to-yellow-100 border-yellow-200">
          <div className="flex items-start space-x-3">
            <Sparkles className="h-6 w-6 text-yellow-600 mt-1 flex-shrink-0" />
            <div>
              <h3 className="font-medium text-yellow-900 mb-2">AI Legal Analysis</h3>
              <div className="text-sm text-yellow-800 whitespace-pre-wrap">
                {aiResponse}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Search Results ({searchResults.length})
          </h2>
          
          {searchResults.map((result) => (
            <div key={result.id} className="search-result">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {result.title}
                  </h3>
                  
                  {result.citation && (
                    <p className="text-sm text-primary-600 font-medium mb-2">
                      {result.citation}
                    </p>
                  )}
                  
                  <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-3">
                    {result.jurisdiction && (
                      <span className="flex items-center">
                        <MapPin className="h-3 w-3 mr-1" />
                        {result.jurisdiction}
                      </span>
                    )}
                    {result.legal_area && (
                      <span className="flex items-center">
                        <FileText className="h-3 w-3 mr-1" />
                        {result.legal_area}
                      </span>
                    )}
                    {result.date_decided && (
                      <span className="flex items-center">
                        <Calendar className="h-3 w-3 mr-1" />
                        {new Date(result.date_decided).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  
                  <p className="text-gray-700 text-sm">
                    {result.extracted_text_preview}
                  </p>
                </div>
                
                <div className="ml-4 flex space-x-2">
                  <button
                    onClick={() => handleDownload(result.id)}
                    className="p-2 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors duration-200"
                    title="Download original document"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* No Results */}
      {!isLoading && searchResults.length === 0 && query && (
        <div className="text-center py-12">
          <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p className="text-gray-600">
            Try adjusting your search terms or filters to find more results.
          </p>
        </div>
      )}
    </div>
  )
}

export default SearchPage