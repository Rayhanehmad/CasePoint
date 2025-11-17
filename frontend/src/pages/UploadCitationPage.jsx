import React, { useState } from 'react'
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function UploadCitationPage() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    citation: '',
    court: '',
    year: '',
    journal: '',
    page_no: '',
    party_line: '',
    legal_area: '',
    summary: '',
    headnotes: '',
    keywords: ''
  })
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile && (selectedFile.type === 'application/pdf' || selectedFile.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')) {
      setFile(selectedFile)
      setError('')
    } else {
      setError('Please select a PDF or DOCX file')
      setFile(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess(false)

    const submitData = new FormData()
    Object.keys(formData).forEach(key => {
      if (formData[key]) submitData.append(key, formData[key])
    })
    if (file) submitData.append('file', file)

    try {
      const response = await fetch('/api/upload_citation', {
        method: 'POST',
        body: submitData
      })

      const data = await response.json()

      if (response.ok && data.success) {
        setSuccess(true)
        setTimeout(() => {
          if (data.citation_id) {
            navigate(`/cases/${data.citation_id}`)
          } else {
            navigate('/search')
          }
        }, 1500)
      } else {
        setError(data.error || 'Upload failed. Please try again.')
      }
    } catch (err) {
      setError('Network error. Please check your connection.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-800 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl p-8">
          <div className="flex items-center gap-3 mb-6">
            <Upload className="w-8 h-8 text-green-400" />
            <h1 className="text-3xl font-bold text-white">Upload Legal Citation</h1>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-red-200">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-6 p-4 bg-green-500/20 border border-green-500/50 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
              <p className="text-green-200">Citation uploaded successfully! Redirecting...</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* File Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">
                Upload Document (PDF or DOCX)
              </label>
              <div className="relative">
                <input
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleFileChange}
                  className="block w-full text-sm text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-600 file:text-white hover:file:bg-green-700 cursor-pointer"
                />
              </div>
              {file && (
                <p className="mt-2 text-sm text-green-400 flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  {file.name}
                </p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Citation */}
              <div>
                <label className="block text-sm font-medium text-gray-200 mb-2">
                  Citation <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  name="citation"
                  value={formData.citation}
                  onChange={handleChange}
                  required
                  placeholder="e.g., 2020 PLD 365"
                  className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              {/* Court */}
              <div>
                <label className="block text-sm font-medium text-gray-200 mb-2">
                  Court
                </label>
                <input
                  type="text"
                  name="court"
                  value={formData.court}
                  onChange={handleChange}
                  placeholder="e.g., Supreme Court"
                  className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              {/* Year */}
              <div>
                <label className="block text-sm font-medium text-gray-200 mb-2">
                  Year
                </label>
                <input
                  type="number"
                  name="year"
                  value={formData.year}
                  onChange={handleChange}
                  placeholder="2020"
                  className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              {/* Journal */}
              <div>
                <label className="block text-sm font-medium text-gray-200 mb-2">
                  Journal
                </label>
                <select
                  name="journal"
                  value={formData.journal}
                  onChange={handleChange}
                  className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="">Select Journal</option>
                  <option value="PLD">PLD</option>
                  <option value="SCMR">SCMR</option>
                  <option value="MLD">MLD</option>
                  <option value="YLR">YLR</option>
                  <option value="CLC">CLC</option>
                  <option value="CLD">CLD</option>
                  <option value="PCrLJ">PCrLJ</option>
                  <option value="PTD">PTD</option>
                  <option value="PLC">PLC</option>
                </select>
              </div>

              {/* Page Number */}
              <div>
                <label className="block text-sm font-medium text-gray-200 mb-2">
                  Page Number
                </label>
                <input
                  type="text"
                  name="page_no"
                  value={formData.page_no}
                  onChange={handleChange}
                  placeholder="365"
                  className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              {/* Legal Area */}
              <div>
                <label className="block text-sm font-medium text-gray-200 mb-2">
                  Legal Area
                </label>
                <input
                  type="text"
                  name="legal_area"
                  value={formData.legal_area}
                  onChange={handleChange}
                  placeholder="e.g., Criminal Law"
                  className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
            </div>

            {/* Party Line */}
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">
                Parties
              </label>
              <input
                type="text"
                name="party_line"
                value={formData.party_line}
                onChange={handleChange}
                placeholder="Petitioner v. Respondent"
                className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>

            {/* Summary */}
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">
                Summary
              </label>
              <textarea
                name="summary"
                value={formData.summary}
                onChange={handleChange}
                rows="4"
                placeholder="Brief summary of the case..."
                className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>

            {/* Headnotes */}
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">
                Headnotes
              </label>
              <textarea
                name="headnotes"
                value={formData.headnotes}
                onChange={handleChange}
                rows="3"
                placeholder="Key legal points..."
                className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>

            {/* Keywords */}
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">
                Keywords
              </label>
              <input
                type="text"
                name="keywords"
                value={formData.keywords}
                onChange={handleChange}
                placeholder="keyword1, keyword2, keyword3"
                className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>

            {/* Submit Button */}
            <div className="flex gap-4">
              <button
                type="submit"
                disabled={loading || !formData.citation}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" />
                    Upload Citation
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => navigate('/search')}
                className="px-6 py-3 border border-white/20 text-white rounded-lg font-medium hover:bg-white/10 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default UploadCitationPage
