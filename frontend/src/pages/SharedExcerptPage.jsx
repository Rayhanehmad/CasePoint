import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Share2, FileText, Calendar, AlertCircle, ExternalLink } from 'lucide-react'

function SharedExcerptPage() {
  const { code } = useParams()
  const [excerpt, setExcerpt] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchExcerpt = async () => {
      try {
        const response = await fetch(`/api/shared/${code}`)
        const data = await response.json()

        if (response.ok && data.success) {
          setExcerpt(data.excerpt)
        } else {
          setError(data.error || 'Excerpt not found or has expired')
        }
      } catch (err) {
        setError('Failed to load shared excerpt')
      } finally {
        setLoading(false)
      }
    }

    if (code) {
      fetchExcerpt()
    }
  }, [code])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-800 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-400"></div>
      </div>
    )
  }

  if (error || !excerpt) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-800 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-8 text-center">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">Excerpt Not Available</h1>
          <p className="text-gray-300 mb-6">{error}</p>
          <Link
            to="/search"
            className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Go to Search
            <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-800 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-green-600 px-8 py-6">
            <div className="flex items-center gap-3 mb-2">
              <Share2 className="w-6 h-6 text-white" />
              <h1 className="text-2xl font-bold text-white">Shared Legal Excerpt</h1>
            </div>
            <p className="text-blue-100 text-sm">
              Shared from CasePoint Legal Research Platform
            </p>
          </div>

          {/* Citation Info */}
          <div className="bg-white/5 px-8 py-4 border-b border-white/10">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-5 h-5 text-blue-400" />
                  <h2 className="text-xl font-semibold text-white">
                    {excerpt.citation}
                  </h2>
                </div>
                {excerpt.party_line && (
                  <p className="text-gray-300 text-sm mb-2">{excerpt.party_line}</p>
                )}
                <div className="flex items-center gap-4 text-sm text-gray-400">
                  {excerpt.court && <span>{excerpt.court}</span>}
                  {excerpt.year && <span>{excerpt.year}</span>}
                  {excerpt.journal && (
                    <span className="bg-blue-500/20 text-blue-300 px-2 py-1 rounded">
                      {excerpt.journal}
                    </span>
                  )}
                </div>
              </div>
              <Link
                to={`/cases/${excerpt.citation_id}`}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
              >
                View Full Case
                <ExternalLink className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Excerpt Content */}
          <div className="p-8">
            <div className="bg-white/5 border border-white/20 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Excerpt</h3>
              <div className="prose prose-invert max-w-none">
                <p className="text-gray-200 whitespace-pre-wrap leading-relaxed">
                  {excerpt.excerpt_text}
                </p>
              </div>
            </div>

            {/* Metadata */}
            <div className="mt-6 pt-6 border-t border-white/20 flex items-center justify-between text-sm text-gray-400">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <span>
                  Shared on {new Date(excerpt.created_at).toLocaleDateString()}
                </span>
              </div>
              {excerpt.view_count > 0 && (
                <span>{excerpt.view_count} view{excerpt.view_count !== 1 ? 's' : ''}</span>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="bg-white/5 px-8 py-4 border-t border-white/10">
            <p className="text-center text-sm text-gray-400">
              Powered by{' '}
              <Link to="/" className="text-green-400 hover:text-green-300 font-medium">
                CasePoint
              </Link>
              {' '}— Modern Legal Research for Pakistan Law
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SharedExcerptPage
