import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { 
  Search, 
  FileText, 
  BarChart3, 
  Settings, 
  LogOut, 
  Scale,
  KeyRound,
  Brain
} from 'lucide-react'

const Navbar = () => {
  const { user, logout } = useAuthStore()
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: BarChart3 },
    { name: 'Search', href: '/search', icon: Search },
    { name: 'Keyword Search', href: '/keyword-search', icon: KeyRound },
    { name: 'Case Analyzer', href: '/case-analyzer', icon: Brain },
    { name: 'Documents', href: '/documents', icon: FileText },
    { name: 'Subscription', href: '/subscription', icon: Settings },
  ]

  if (user?.subscription_tier === 'admin') {
    navigation.push({ name: 'Admin', href: '/admin', icon: Settings })
  }

  const handleLogout = () => {
    logout()
  }

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            {/* Logo */}
            <div className="flex-shrink-0 flex items-center">
              <Link to="/" className="flex items-center space-x-2">
                <Scale className="h-8 w-8 text-primary-600" />
                <span className="text-2xl font-bold text-gray-900">
                  Case<span className="text-primary-600">Point</span>
                </span>
              </Link>
            </div>

            {/* Navigation links */}
            {user && (
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {navigation.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname === item.href
                  
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`${
                        isActive
                          ? 'border-primary-500 text-gray-900'
                          : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                      } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors duration-200`}
                    >
                      <Icon className="h-4 w-4 mr-2" />
                      {item.name}
                    </Link>
                  )
                })}
              </div>
            )}
          </div>

          {/* User menu */}
          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <div className="hidden sm:block">
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-700">
                      Welcome, {user.full_name}
                    </span>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      user.subscription_tier === 'free' 
                        ? 'bg-gray-100 text-gray-800' 
                        : user.subscription_tier === 'admin'
                        ? 'bg-purple-100 text-purple-800'
                        : 'bg-primary-100 text-primary-800'
                    }`}>
                      {user.subscription_tier.toUpperCase()}
                    </span>
                  </div>
                </div>
                
                <button
                  onClick={handleLogout}
                  className="flex items-center px-3 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors duration-200"
                >
                  <LogOut className="h-4 w-4 mr-1" />
                  Logout
                </button>
              </>
            ) : (
              <div className="flex items-center space-x-4">
                <Link
                  to="/login"
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="btn-primary text-sm"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar