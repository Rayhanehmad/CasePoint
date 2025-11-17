import React from 'react'
import { Search, Upload, Sparkles, FileText, BookOpen, Users, CheckCircle } from 'lucide-react'
import { Link } from 'react-router-dom'

function HowToUsePage() {
  const features = [
    {
      icon: Search,
      title: 'Advanced Search',
      description: 'Search across thousands of legal citations using keywords, citation formats, or advanced filters.',
      steps: [
        'Choose your search type (Keyword, Citation, or Advanced)',
        'Enter your search query with relevant filters',
        'Review highlighted results with AI-powered insights',
        'Access full citation details with one click'
      ]
    },
    {
      icon: Sparkles,
      title: 'AI-Powered Analysis',
      description: 'Get instant AI summaries, headnotes, and legal analysis for any citation.',
      steps: [
        'Navigate to any citation detail page',
        'Click "Generate AI Summary" for instant analysis',
        'Review AI-generated headnotes and key points',
        'Use AI Case Analyzer for counter arguments'
      ]
    },
    {
      icon: Upload,
      title: 'Document Upload',
      description: 'Upload your legal documents and citations for automated processing.',
      steps: [
        'Go to Upload Citation or Bulk Upload',
        'Select PDF or DOCX files',
        'Fill in metadata (citation, court, year, etc.)',
        'Submit for automatic text extraction and indexing'
      ]
    },
    {
      icon: FileText,
      title: 'Citation Generator',
      description: 'Generate properly formatted legal citations using AI.',
      steps: [
        'Provide case details (parties, court, date, etc.)',
        'Click "Generate Citation"',
        'Review AI-generated citation in multiple formats',
        'Copy or save for your legal documents'
      ]
    }
  ]

  const journals = [
    { code: 'PLD', name: 'Pakistan Legal Decisions' },
    { code: 'SCMR', name: 'Supreme Court Monthly Review' },
    { code: 'MLD', name: 'Monthly Law Digest' },
    { code: 'YLR', name: 'Yearly Law Reports' },
    { code: 'CLC', name: 'Current Law Cases' },
    { code: 'PCrLJ', name: 'Pakistan Criminal Law Journal' }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-800 py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">How to Use CasePoint</h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Your comprehensive guide to navigating Pakistan's modern legal research platform
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-6 hover:bg-white/15 transition-all"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                  <feature.icon className="w-6 h-6 text-green-400" />
                </div>
                <h3 className="text-xl font-bold text-white">{feature.title}</h3>
              </div>
              <p className="text-gray-300 mb-4">{feature.description}</p>
              <div className="space-y-2">
                {feature.steps.map((step, stepIndex) => (
                  <div key={stepIndex} className="flex items-start gap-2">
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-gray-200">{step}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Supported Journals */}
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-8 mb-16">
          <div className="flex items-center gap-3 mb-6">
            <BookOpen className="w-8 h-8 text-blue-400" />
            <h2 className="text-2xl font-bold text-white">Supported Legal Journals</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {journals.map((journal, index) => (
              <div
                key={index}
                className="bg-white/5 border border-white/20 rounded-lg p-4 text-center"
              >
                <div className="text-lg font-bold text-green-400 mb-1">{journal.code}</div>
                <div className="text-sm text-gray-300">{journal.name}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Getting Started */}
        <div className="bg-gradient-to-r from-blue-600 to-green-600 rounded-2xl p-8 text-center">
          <Users className="w-16 h-16 text-white mx-auto mb-4" />
          <h2 className="text-3xl font-bold text-white mb-4">Ready to Get Started?</h2>
          <p className="text-blue-100 mb-6 max-w-2xl mx-auto">
            Join thousands of legal professionals using CasePoint for faster, smarter legal research.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link
              to="/register"
              className="px-8 py-3 bg-white text-blue-600 rounded-lg font-medium hover:bg-gray-100 transition-colors"
            >
              Create Free Account
            </Link>
            <Link
              to="/search"
              className="px-8 py-3 bg-white/20 text-white border border-white/30 rounded-lg font-medium hover:bg-white/30 transition-colors"
            >
              Start Searching
            </Link>
          </div>
        </div>

        {/* Tips */}
        <div className="mt-16 bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-white mb-6">Pro Tips</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-green-400 mb-2">Search Tips</h3>
              <ul className="space-y-2 text-gray-300 text-sm">
                <li>• Use quotation marks for exact phrase matching</li>
                <li>• Filter by year range for recent cases</li>
                <li>• Use legal area filters to narrow results</li>
                <li>• Keywords are highlighted in yellow for easy scanning</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-green-400 mb-2">AI Features</h3>
              <ul className="space-y-2 text-gray-300 text-sm">
                <li>• AI summaries are cached for instant access</li>
                <li>• Generate headnotes automatically from full text</li>
                <li>• Use Case Analyzer for counter arguments</li>
                <li>• Citation Generator supports multiple formats</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HowToUsePage
