import React, { useState } from 'react'
import toast from 'react-hot-toast'
import { Sparkles, FileText, Copy, Download, Wand2 } from 'lucide-react'
import api from '../services/api'

const CitationGenerator = () => {
  const [caseDetails, setCaseDetails] = useState('')
  const [citationType, setCitationType] = useState('case')
  const [jurisdiction, setJurisdiction] = useState('Pakistan')
  const [generatedCitation, setGeneratedCitation] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleGenerate = async (e) => {
    e.preventDefault()
    
    if (!caseDetails.trim()) {
      toast.error('Please provide case details')
      return
    }

    setIsLoading(true)
    setGeneratedCitation(null)

    try {
      const response = await api.post('/generate_citation', {
        case_details: caseDetails,
        citation_type: citationType,
        jurisdiction: jurisdiction
      })
      
      if (response.data.success) {
        setGeneratedCitation(response.data.citation)
        toast.success('Citation generated successfully!')
      } else {
        toast.error('Failed to generate citation')
      }
    } catch (error) {
      console.error('Citation generation error:', error)
      toast.error(error.response?.data?.error || 'Failed to generate citation')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopy = () => {
    if (generatedCitation) {
      navigator.clipboard.writeText(generatedCitation.formatted_citation)
      toast.success('Citation copied to clipboard!')
    }
  }

  const handleDownload = () => {
    if (generatedCitation) {
      const blob = new Blob([generatedCitation.formatted_citation], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'citation.txt'
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Citation downloaded!')
    }
  }

  const handleClear = () => {
    setCaseDetails('')
    setGeneratedCitation(null)
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8 text-center">
        <div className="flex items-center justify-center gap-3 mb-3">
          <Wand2 className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">AI Citation Generator</h1>
        </div>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Generate properly formatted legal citations using AI. Provide case details, and we'll create a citation following Pakistan legal standards.
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <form onSubmit={handleGenerate}>
          {/* Citation Type Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Citation Type
            </label>
            <div className="flex gap-4">
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  value="case"
                  checked={citationType === 'case'}
                  onChange={(e) => setCitationType(e.target.value)}
                  className="mr-2"
                />
                <span className="text-gray-700">Case Law</span>
              </label>
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  value="statute"
                  checked={citationType === 'statute'}
                  onChange={(e) => setCitationType(e.target.value)}
                  className="mr-2"
                />
                <span className="text-gray-700">Statute/Act</span>
              </label>
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  value="article"
                  checked={citationType === 'article'}
                  onChange={(e) => setCitationType(e.target.value)}
                  className="mr-2"
                />
                <span className="text-gray-700">Constitution Article</span>
              </label>
            </div>
          </div>

          {/* Jurisdiction */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Jurisdiction
            </label>
            <select
              value={jurisdiction}
              onChange={(e) => setJurisdiction(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="Pakistan">Pakistan</option>
              <option value="Federal">Federal</option>
              <option value="Punjab">Punjab</option>
              <option value="Sindh">Sindh</option>
              <option value="KPK">Khyber Pakhtunkhwa</option>
              <option value="Balochistan">Balochistan</option>
            </select>
          </div>

          {/* Case Details Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <FileText className="inline w-4 h-4 mr-1" />
              Case Details
            </label>
            <textarea
              value={caseDetails}
              onChange={(e) => setCaseDetails(e.target.value)}
              placeholder={`Enter case details, for example:
- Parties: Muhammad Ali vs State
- Court: Supreme Court of Pakistan
- Year: 2023
- Decision: Acquittal
- Legal Area: Criminal Law
- Case Type: Criminal Appeal
              
Or describe the legal document you want to cite.`}
              rows={10}
              className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
            />
            <p className="mt-2 text-xs text-gray-500">
              Provide as much detail as possible for accurate citation generation
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-medium transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Generate Citation
                </>
              )}
            </button>
            <button
              type="button"
              onClick={handleClear}
              className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-6 py-2 rounded-md font-medium transition-colors"
            >
              Clear
            </button>
          </div>
        </form>
      </div>

      {/* Generated Citation Output */}
      {generatedCitation && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg shadow-lg p-6 border-2 border-blue-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-600" />
              Generated Citation
            </h2>
            <div className="flex gap-2">
              <button
                onClick={handleCopy}
                className="bg-white hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 border border-gray-300"
              >
                <Copy className="w-4 h-4" />
                Copy
              </button>
              <button
                onClick={handleDownload}
                className="bg-white hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 border border-gray-300"
              >
                <Download className="w-4 h-4" />
                Download
              </button>
            </div>
          </div>

          {/* Formatted Citation */}
          <div className="bg-white rounded-lg p-6 mb-4 border border-blue-100">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Formatted Citation:</h3>
            <p className="text-lg font-mono text-gray-900 break-words">
              {generatedCitation.formatted_citation}
            </p>
          </div>

          {/* Citation Components */}
          {generatedCitation.components && (
            <div className="bg-white rounded-lg p-6 border border-blue-100">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Citation Components:</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                {Object.entries(generatedCitation.components).map(([key, value]) => (
                  <div key={key} className="flex">
                    <span className="font-medium text-gray-600 capitalize min-w-[120px]">
                      {key.replace(/_/g, ' ')}:
                    </span>
                    <span className="text-gray-900">{value || 'N/A'}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Notes */}
          {generatedCitation.notes && (
            <div className="mt-4 p-4 bg-blue-100 rounded-lg">
              <p className="text-sm text-blue-900">
                <strong>Note:</strong> {generatedCitation.notes}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Help Section */}
      <div className="mt-8 bg-gray-50 rounded-lg p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">How to use:</h3>
        <ul className="space-y-2 text-sm text-gray-700">
          <li className="flex items-start">
            <span className="text-blue-600 mr-2">1.</span>
            Select the type of citation you need (Case Law, Statute, or Constitution Article)
          </li>
          <li className="flex items-start">
            <span className="text-blue-600 mr-2">2.</span>
            Choose the appropriate jurisdiction
          </li>
          <li className="flex items-start">
            <span className="text-blue-600 mr-2">3.</span>
            Enter the case details or legal document information in the text area
          </li>
          <li className="flex items-start">
            <span className="text-blue-600 mr-2">4.</span>
            Click "Generate Citation" and AI will format it according to Pakistan legal standards
          </li>
          <li className="flex items-start">
            <span className="text-blue-600 mr-2">5.</span>
            Copy or download the generated citation for your use
          </li>
        </ul>
      </div>
    </div>
  )
}

export default CitationGenerator
