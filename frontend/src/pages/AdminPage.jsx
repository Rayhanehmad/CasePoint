import React, { useState, useEffect } from 'react'
import { 
  Users, 
  FileText, 
  BarChart3, 
  Search,
  TrendingUp,
  TrendingDown,
  Clock
} from 'lucide-react'
import api from '../services/api'

const AdminPage = () => {
  const [stats, setStats] = useState({
    total_users: 0,
    total_documents: 0,
    total_searches: 0,
    active_subscriptions: 0,
    documents_processed_today: 0,
    searches_today: 0
  })
  const [users, setUsers] = useState([])
  const [documents, setDocuments] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchAdminData()
  }, [])

  const fetchAdminData = async () => {
    try {
      // Mock data for now - will be replaced with real API calls
      setStats({
        total_users: 1247,
        total_documents: 8934,
        total_searches: 15678,
        active_subscriptions: 324,
        documents_processed_today: 47,
        searches_today: 892
      })

      setUsers([
        {
          id: '1',
          email: 'lawyer@example.com',
          full_name: 'John Smith',
          subscription_tier: 'premium',
          created_at: '2024-01-15',
          last_search: '2 hours ago'
        },
        {
          id: '2',
          email: 'legal@firm.com',
          full_name: 'Sarah Johnson',
          subscription_tier: 'basic',
          created_at: '2024-02-20',
          last_search: '1 day ago'
        }
      ])

      setDocuments([
        {
          id: '1',
          title: 'Supreme Court Case 2024',
          document_type: 'pdf',
          is_processed: true,
          file_size: 2457600,
          created_at: '2024-03-01'
        },
        {
          id: '2',
          title: 'High Court Judgment',
          document_type: 'pdf',
          is_processed: false,
          file_size: 1843200,
          created_at: '2024-03-02'
        }
      ])
    } catch (error) {
      console.error('Failed to fetch admin data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const formatFileSize = (bytes) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    if (bytes === 0) return '0 Bytes'
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const StatCard = ({ title, value, icon: Icon, trend, trendValue, color = 'blue' }) => (
    <div className="card">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg bg-${color}-100`}>
          <Icon className={`h-6 w-6 text-${color}-600`} />
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value.toLocaleString()}</p>
          {trend && (
            <div className="flex items-center mt-1">
              {trend === 'up' ? (
                <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
              )}
              <span className={`text-sm ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                {trendValue}% from last month
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Manage users, documents, and monitor system performance
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          title="Total Users"
          value={stats.total_users}
          icon={Users}
          trend="up"
          trendValue={12}
          color="blue"
        />
        <StatCard
          title="Documents"
          value={stats.total_documents}
          icon={FileText}
          trend="up"
          trendValue={8}
          color="green"
        />
        <StatCard
          title="Searches"
          value={stats.total_searches}
          icon={Search}
          trend="up"
          trendValue={15}
          color="purple"
        />
        <StatCard
          title="Active Subs"
          value={stats.active_subscriptions}
          icon={BarChart3}
          trend="up"
          trendValue={5}
          color="yellow"
        />
        <StatCard
          title="Docs Today"
          value={stats.documents_processed_today}
          icon={FileText}
          color="gray"
        />
        <StatCard
          title="Searches Today"
          value={stats.searches_today}
          icon={Search}
          color="gray"
        />
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview' },
            { id: 'users', name: 'Users' },
            { id: 'documents', name: 'Documents' },
            { id: 'analytics', name: 'Analytics' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <Clock className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-900">New document uploaded</p>
                  <p className="text-xs text-gray-500">Supreme Court Case 2024 • 5 minutes ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <Clock className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-900">User registered</p>
                  <p className="text-xs text-gray-500">lawyer@example.com • 1 hour ago</p>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">API Response Time</span>
                <span className="text-sm font-medium text-green-600">142ms</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Database Health</span>
                <span className="text-sm font-medium text-green-600">Healthy</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">OCR Processing</span>
                <span className="text-sm font-medium text-yellow-600">3 pending</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'users' && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Users Management</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Subscription
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Joined
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Active
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{user.full_name}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.subscription_tier === 'premium' 
                          ? 'bg-purple-100 text-purple-800' 
                          : user.subscription_tier === 'basic'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {user.subscription_tier}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.last_search}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button className="text-primary-600 hover:text-primary-900 mr-3">
                        Edit
                      </button>
                      <button className="text-red-600 hover:text-red-900">
                        Disable
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'documents' && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Management</h3>
          <div className="space-y-4">
            {documents.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <FileText className="h-8 w-8 text-blue-500" />
                  <div>
                    <h4 className="font-medium text-gray-900">{doc.title}</h4>
                    <p className="text-sm text-gray-600">
                      {doc.document_type.toUpperCase()} • {formatFileSize(doc.file_size)} • 
                      {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      doc.is_processed 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {doc.is_processed ? 'Processed' : 'Processing...'}
                    </span>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button className="btn-secondary text-sm">View</button>
                  <button className="btn-secondary text-sm">Reprocess</button>
                  <button className="text-red-600 hover:text-red-700 text-sm">Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminPage