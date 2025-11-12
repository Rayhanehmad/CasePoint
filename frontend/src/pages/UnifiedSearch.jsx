import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, FileText, Brain } from 'lucide-react'
import CitationSearchPanel from '../components/search/CitationSearchPanel'
import KeywordSearchPanel from '../components/search/KeywordSearchPanel'
import AdvancedSearchPanel from '../components/search/AdvancedSearchPanel'

const UnifiedSearch = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'citation')

  // Sync URL with tab state
  useEffect(() => {
    const tabFromUrl = searchParams.get('tab')
    if (tabFromUrl && ['citation', 'keyword', 'advanced'].includes(tabFromUrl)) {
      setActiveTab(tabFromUrl)
    }
  }, [searchParams])

  const handleTabChange = (tab) => {
    setActiveTab(tab)
    setSearchParams({ tab })
  }

  const tabs = [
    { id: 'citation', label: 'Citation Search', icon: FileText },
    { id: 'keyword', label: 'Keyword Search', icon: Search },
    { id: 'advanced', label: 'Advanced Search', icon: Brain }
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Legal Search</h1>
        <p className="text-gray-600">
          Search Pakistan legal database using citation metadata, keywords, or advanced filters
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-md mb-8">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px" aria-label="Tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`
                    flex-1 py-4 px-1 text-center border-b-2 font-medium text-sm
                    transition-colors duration-200
                    ${isActive
                      ? 'border-green-500 text-green-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <div className="flex items-center justify-center gap-2">
                    <Icon className="w-5 h-5" />
                    <span>{tab.label}</span>
                  </div>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'citation' && <CitationSearchPanel />}
          {activeTab === 'keyword' && <KeywordSearchPanel />}
          {activeTab === 'advanced' && <AdvancedSearchPanel />}
        </div>
      </div>
    </div>
  )
}

export default UnifiedSearch
