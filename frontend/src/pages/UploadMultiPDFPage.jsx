import React, { useState } from 'react'
import { Upload, FileText, X, AlertCircle, CheckCircle, Loader } from 'lucide-react'

function UploadMultiPDFPage() {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [results, setResults] = useState(null)

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files)
    const pdfFiles = selectedFiles.filter(f => f.type === 'application/pdf')
    
    if (pdfFiles.length !== selectedFiles.length) {
      setError('Only PDF files are allowed')
      return
    }
    
    setFiles(pdfFiles)
    setError('')
  }

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (files.length === 0) {
      setError('Please select at least one PDF file')
      return
    }

    setLoading(true)
    setError('')
    setResults(null)

    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })

    try {
      const response = await fetch('/api/upload_multi_pdf', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (response.ok && data.success) {
        setResults(data.results)
        setFiles([])
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
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl p-8">
          <div className="flex items-center gap-3 mb-6">
            <Upload className="w-8 h-8 text-green-400" />
            <h1 className="text-3xl font-bold text-white">Bulk Upload Legal Citations</h1>
          </div>
          
          <p className="text-gray-300 mb-6">
            Upload multiple PDF files to extract and store legal citations automatically.
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-red-200">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* File Upload Area */}
            <div className="border-2 border-dashed border-white/30 rounded-lg p-8 bg-white/5 hover:bg-white/10 transition-colors">
              <div className="text-center">
                <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <label className="cursor-pointer">
                  <span className="mt-2 block text-sm font-medium text-white">
                    Click to select PDF files or drag and drop
                  </span>
                  <input
                    type="file"
                    multiple
                    accept=".pdf"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>
                <p className="mt-1 text-xs text-gray-400">
                  PDF files only, multiple files supported
                </p>
              </div>
            </div>

            {/* Selected Files List */}
            {files.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-lg font-medium text-white mb-3">
                  Selected Files ({files.length})
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-white/5 border border-white/20 rounded-lg"
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <FileText className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-white truncate">
                            {file.name}
                          </p>
                          <p className="text-xs text-gray-400">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="ml-4 p-1 text-red-400 hover:text-red-300 hover:bg-red-500/20 rounded transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || files.length === 0}
              className="w-full bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Processing {files.length} file(s)...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  Upload and Process Files
                </>
              )}
            </button>
          </form>

          {/* Results */}
          {results && (
            <div className="mt-8 space-y-4">
              <h3 className="text-xl font-bold text-white mb-4">Upload Results</h3>
              
              {results.successful && results.successful.length > 0 && (
                <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-4">
                  <div className="flex items-start gap-3 mb-3">
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-green-200 font-medium">
                        Successfully Uploaded ({results.successful.length})
                      </h4>
                    </div>
                  </div>
                  <ul className="space-y-1 text-sm text-green-100">
                    {results.successful.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {results.failed && results.failed.length > 0 && (
                <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
                  <div className="flex items-start gap-3 mb-3">
                    <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-red-200 font-medium">
                        Failed Uploads ({results.failed.length})
                      </h4>
                    </div>
                  </div>
                  <ul className="space-y-1 text-sm text-red-100">
                    {results.failed.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {results.summary && (
                <div className="bg-blue-500/20 border border-blue-500/50 rounded-lg p-4">
                  <p className="text-blue-200 text-sm">{results.summary}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default UploadMultiPDFPage
