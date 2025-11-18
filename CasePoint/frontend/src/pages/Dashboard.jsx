import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Search, 
  FileText, 
  BarChart3, 
  Users, 
  TrendingUp,
  Clock,
  Database
} from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import api from '../services/api'

const Dashboard = () => {
  const { user } = useAuthStore()
  const [stats, setStats] = useState({
    recent_searches: [],
    search_count: 0,
    document_count: 0,
    subscription_status: 'active'
  })
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      // Mock data for now - will be replaced with real API calls
      setStats({
        recent_searches: [
          { query: 'constitutional law', date: '2 hours ago', results: 15 },
          { query: 'contract dispute', date: '1 day ago', results: 8 },
          { query: 'criminal procedure', date: '2 days ago', results: 23 }
        ],
        search_count: 47,
        document_count: 1250,
        subscription_status: 'active'
      })
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const quickActions = [
    {
      name: 'Citation Search',
      description: 'Search by journal, court, year, parties',
      href: '/citation-search',
      icon: Search,
      color: 'bg-blue-500 hover:bg-blue-600'
    },
    {
      name: 'Advanced Search',
      description: 'Multi-field legal research search',
      href: '/advanced-search',
      icon: Search,
      color: 'bg-emerald-500 hover:bg-emerald-600'
    },
    {
      name: 'Upload Documents',
      description: 'Add new legal documents',
      href: '/documents',
      icon: FileText,
      color: 'bg-green-500 hover:bg-green-600'
    },
    {
      name: 'View Analytics',
      description: 'Check usage statistics',
      href: '/analytics',
      icon: BarChart3,
      color: 'bg-purple-500 hover:bg-purple-600'
    }
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg p-6 text-white">
        <h1 className="text-2xl font-bold">Welcome back, {user?.full_name}!</h1>
        <p className="mt-2 text-primary-100">
          Ready to dive into legal research? Access Pakistan's comprehensive legal database.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Search className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Searches</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.search_count}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <Database className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Documents Available</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.document_count.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Plan Status</p>
              <p className="text-2xl font-semibold text-gray-900 capitalize">
                {user?.subscription_tier}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickActions.map((action) => {
            const Icon = action.icon
            return (
              <Link
                key={action.name}
                to={action.href}
                className="group p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors duration-200"
              >
                <div className="flex items-center">
                  <div className={`p-2 ${action.color} rounded-lg text-white transition-colors duration-200`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900 group-hover:text-primary-600">
                      {action.name}
                    </p>
                    <p className="text-xs text-gray-500">{action.description}</p>
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Searches</h2>
          <div className="space-y-3">
            {stats.recent_searches.map((search, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">{search.query}</p>
                  <p className="text-xs text-gray-500">{search.results} results found</p>
                </div>
                <div className="flex items-center text-xs text-gray-500">
                  <Clock className="h-3 w-3 mr-1" />
                  {search.date}
                </div>
              </div>
            ))}
          </div>
          <Link
            to="/search"
            className="mt-4 block text-center text-sm text-primary-600 hover:text-primary-500"
          >
            Start new search →
          </Link>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Subscription Details</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Current Plan</span>
              <span className="text-sm font-medium text-gray-900 capitalize">
                {user?.subscription_tier}
              </span>
            </div>
            
            {user?.subscription_tier === 'free' && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  Upgrade to access advanced search features and unlimited queries.
                </p>
                <Link
                  to="/subscription"
                  className="mt-2 inline-block text-sm font-medium text-yellow-600 hover:text-yellow-500"
                >
                  Upgrade now →
                </Link>
              </div>
            )}
            
            <div className="pt-4 border-t border-gray-200">
              <Link
                to="/subscription"
                className="text-sm text-primary-600 hover:text-primary-500"
              >
                Manage subscription →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard