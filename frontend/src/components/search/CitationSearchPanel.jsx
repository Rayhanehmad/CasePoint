import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Search, FileText, Calendar, Hash, Scale, Eye } from 'lucide-react'
import api from '../../services/api'

const CitationSearchPanel = () => {
  const [searchResults, setSearchResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const { register, handleSubmit, reset } = useForm()

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
    <div>
      {/* Search Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="mb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
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
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
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
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
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
              placeholder="e.g., 453"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Search Button */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={isLoading}
            className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-md font-medium transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Searching...
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                Search
              </>
            )}
          </button>
          <button
            type="button"
            onClick={() => {
              reset()
              setSearchResults([])
            }}
            className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-6 py-2 rounded-md font-medium transition-colors"
          >
            Clear
          </button>
        </div>
      </form>

      {/* Search Results - Table Format */}
      {searchResults.length > 0 && (
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
              {searchResults.map((result) => (
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
      {!isLoading && searchResults.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No results yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Enter search criteria above to find legal citations
          </p>
        </div>
      )}
    </div>
  )
}

export default CitationSearchPanel
