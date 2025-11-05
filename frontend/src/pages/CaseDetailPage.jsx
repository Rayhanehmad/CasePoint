import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Calendar, Gavel, MapPin, FileText } from 'lucide-react'
import axios from 'axios'
import ShareButtons from '../components/ShareButtons'

export default function CaseDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [caseData, setCaseData] = useState(null)
  const [relatedCases, setRelatedCases] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCaseDetail()
  }, [id])

  const fetchCaseDetail = async () => {
    try {
      const response = await axios.get(`/cases/api/cases/${id}`)
      setCaseData(response.data.case)
      setRelatedCases(response.data.related_cases || [])
    } catch (error) {
      console.error('Error fetching case:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-royal-600"></div>
      </div>
    )
  }

  if (!caseData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">Case not found</h2>
          <button
            onClick={() => navigate('/search')}
            className="mt-4 text-royal-600 hover:text-royal-700"
          >
            Back to search
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-royal-600 hover:text-royal-700 mb-6"
        >
          <ArrowLeft className="w-5 h-5" />
          Back
        </button>

        <div className="bg-white rounded-lg shadow-md p-8 mb-6">
          {/* Case Title */}
          <h1 className="text-3xl font-bold text-navy-900 mb-4">
            {caseData.title}
          </h1>

          {/* Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="flex items-center gap-2 text-gray-600">
              <FileText className="w-5 h-5 text-royal-600" />
              <div>
                <div className="text-sm text-gray-500">Citation</div>
                <div className="font-semibold">{caseData.citation}</div>
              </div>
            </div>

            <div className="flex items-center gap-2 text-gray-600">
              <Gavel className="w-5 h-5 text-royal-600" />
              <div>
                <div className="text-sm text-gray-500">Court</div>
                <div className="font-semibold">{caseData.court || 'N/A'}</div>
              </div>
            </div>

            <div className="flex items-center gap-2 text-gray-600">
              <Calendar className="w-5 h-5 text-royal-600" />
              <div>
                <div className="text-sm text-gray-500">Year</div>
                <div className="font-semibold">{caseData.year || 'N/A'}</div>
              </div>
            </div>

            <div className="flex items-center gap-2 text-gray-600">
              <MapPin className="w-5 h-5 text-royal-600" />
              <div>
                <div className="text-sm text-gray-500">Legal Area</div>
                <div className="font-semibold">{caseData.legal_area || 'N/A'}</div>
              </div>
            </div>
          </div>

          {/* Summary */}
          {caseData.summary && (
            <div className="mb-6">
              <h2 className="text-xl font-bold text-navy-900 mb-3">Summary</h2>
              <p className="text-gray-700 leading-relaxed">{caseData.summary}</p>
            </div>
          )}

          {/* Share Buttons */}
          <div className="border-t pt-6">
            <h2 className="text-xl font-bold text-navy-900 mb-3">Share This Citation</h2>
            <ShareButtons caseId={caseData.id} citation={caseData.citation} summary={caseData.summary} />
          </div>

          {/* Full Text */}
          {caseData.full_text && (
            <div className="mb-6">
              <h2 className="text-xl font-bold text-navy-900 mb-3">Full Text</h2>
              <div className="prose max-w-none">
                <pre className="whitespace-pre-wrap text-gray-700 font-sans">
                  {caseData.full_text}
                </pre>
              </div>
            </div>
          )}

          {/* Keywords */}
          {caseData.keywords && (
            <div className="mb-6">
              <h2 className="text-xl font-bold text-navy-900 mb-3">Keywords</h2>
              <div className="flex flex-wrap gap-2">
                {caseData.keywords.split(',').map((keyword, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-cyan-100 text-cyan-800 rounded-full text-sm"
                  >
                    {keyword.trim()}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Related Cases */}
        {relatedCases.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-8">
            <h2 className="text-2xl font-bold text-navy-900 mb-4">Related Cases</h2>
            <div className="space-y-4">
              {relatedCases.map((relatedCase) => (
                <div
                  key={relatedCase.id}
                  onClick={() => navigate(`/cases/${relatedCase.id}`)}
                  className="p-4 border border-gray-200 rounded-lg hover:border-royal-500 hover:shadow-md transition-all cursor-pointer"
                >
                  <h3 className="font-semibold text-navy-900 mb-1">
                    {relatedCase.title}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {relatedCase.citation} • {relatedCase.court} • {relatedCase.year}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
