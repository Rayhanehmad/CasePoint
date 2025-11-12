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
  Hash,
  Eye,
  HelpCircle
} from 'lucide-react'
import api from '../../services/api'

const AdvancedSearchPanel = () => {
  const [searchResults, setSearchResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const { register, watch } = useForm()

  // Watch all form fields for changes
  const watchedFields = watch()

  // Debounced search on field changes
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      performSearch()
    }, 800) // 800ms debounce

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
    <div>
      {/* Search Icon Header */}
      <div className="flex items-center gap-2 mb-4">
        <Search className="w-5 h-5 text-gray-700" />
        <h2 className="text-lg font-semibold text-gray-900">Advanced Search</h2>
        <HelpCircle className="w-4 h-4 text-gray-400 ml-auto" />
      </div>

      {/* Search Form */}
      <div className="mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          {/* Row 1 */}
          <div>
            <input
              type="text"
              {...register('court')}
              placeholder="Enter Court Name"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent placeholder-gray-400"
            />
          </div>

          <div>
            <input
              type="text"
              {...register('judge')}
              placeholder="Enter Judge Name"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent placeholder-gray-400"
            />
          </div>

          <div>
            <input
              type="text"
              {...register('lawyer')}
              placeholder="Enter Lawyer Name"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent placeholder-gray-400"
            />
          </div>

          <div>
            <input
              type="text"
              {...register('parties')}
              placeholder="Enter Appellant/Opponent"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent placeholder-gray-400"
            />
          </div>

          {/* Row 2 */}
          <div className="md:col-span-2">
            <input
              type="text"
              {...register('keywords')}
              placeholder="Enter Keyword"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent placeholder-gray-400"
            />
          </div>

          <div className="md:col-span-2">
            <input
              type="text"
              {...register('rules')}
              placeholder="Enter Rule"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent placeholder-gray-400"
            />
          </div>

          {/* Row 3 */}
          <div className="md:col-span-2">
            <input
              type="text"
              {...register('acts')}
              placeholder="Enter Act/Ordinance"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent placeholder-gray-400"
            />
          </div>

          <div className="md:col-span-2">
            <input
              type="text"
              {...register('section')}
              placeholder="Enter Section"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent placeholder-gray-400"
            />
          </div>

          {/* Another Act/Section Row */}
          <div className="md:col-span-2">
            <input
              type="text"
              {...register('acts2')}
              placeholder="Enter another Act/Ordinance"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent placeholder-gray-400"
            />
          </div>

          <div className="md:col-span-2">
            <input
              type="text"
              {...register('section2')}
              placeholder="Enter another Section"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent placeholder-gray-400"
            />
          </div>
        </div>

        {/* Help Text */}
        <p className="text-sm text-green-600 mb-4">
          * Please enter at least one-search criteria, and you may add as many for more precise results.
        </p>

        {/* Search Button */}
        <div className="flex justify-center">
          <button
            type="button"
            onClick={handleSearchClick}
            disabled={isLoading}
            className="bg-green-600 hover:bg-green-700 text-white px-8 py-2 rounded-md font-medium transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
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
        </div>
      </div>

      {/* Loading Indicator */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto"></div>
          <p className="text-gray-600 mt-2">Searching...</p>
        </div>
      )}

      {/* Search Results - Table Format */}
      {!isLoading && searchResults.length > 0 && (
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

export default AdvancedSearchPanel
