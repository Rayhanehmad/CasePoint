import React, { useState } from 'react';
import axios from 'axios';

const CaseAnalyzerPage = () => {
  const [narrative, setNarrative] = useState('');
  const [loading, setLoading] = useState(false);
  const [counterArguments, setCounterArguments] = useState('');
  const [caseLaws, setCaseLaws] = useState([]);
  const [statutes, setStatutes] = useState([]);
  const [applicableLaws, setApplicableLaws] = useState([]);
  const [showLawsModal, setShowLawsModal] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyzeCase = async () => {
    if (!narrative.trim()) {
      setError('Please enter a narrative text');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const [counterArgsRes, analyzeCaseRes] = await Promise.all([
        axios.post('/api/auto_counter_arguments', { text: narrative }),
        axios.post('/api/analyze_case', { text: narrative })
      ]);

      setCounterArguments(counterArgsRes.data.counter_arguments);
      setCaseLaws(analyzeCaseRes.data.citations || []);
      setStatutes(analyzeCaseRes.data.statutes || []);
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.response?.data?.error || 'Failed to analyze case');
    } finally {
      setLoading(false);
    }
  };

  const handleWhichLawsApply = async () => {
    if (!narrative.trim()) {
      setError('Please enter a narrative text');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/which_laws_apply', { text: narrative });
      setApplicableLaws(response.data.laws || []);
      setShowLawsModal(true);
    } catch (err) {
      console.error('Laws detection error:', err);
      setError(err.response?.data?.error || 'Failed to detect applicable laws');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            AI Case Analyzer
          </h1>
          <p className="text-lg text-gray-600">
            Analyze legal narratives with AI-powered counter arguments, related case laws, and applicable statutes
          </p>
        </div>

        {/* Input Section */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Enter Your Legal Narrative
          </label>
          <textarea
            value={narrative}
            onChange={(e) => setNarrative(e.target.value)}
            className="w-full h-48 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            placeholder="Enter the case narrative, facts, allegations, or legal scenario..."
          />
          
          {error && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-4 mt-4">
            <button
              onClick={handleAnalyzeCase}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
            >
              {loading ? 'Analyzing...' : 'Analyze Case'}
            </button>
            <button
              onClick={handleWhichLawsApply}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700 text-white px-6 py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-purple-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
            >
              {loading ? 'Detecting...' : 'Which Laws Apply?'}
            </button>
          </div>
        </div>

        {/* Results Section - 3 Column Layout */}
        {(counterArguments || caseLaws.length > 0 || statutes.length > 0) && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Column 1: Counter Arguments */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h2 className="text-xl font-bold text-gray-900">AI Counter Arguments</h2>
              </div>
              <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
                {counterArguments || 'No counter arguments generated yet'}
              </div>
            </div>

            {/* Column 2: Related Case Laws */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <h2 className="text-xl font-bold text-gray-900">Related Case Laws</h2>
              </div>
              <div className="space-y-3">
                {caseLaws.length > 0 ? (
                  caseLaws.map((law, index) => (
                    <div key={index} className="p-3 bg-green-50 rounded-lg border border-green-200">
                      <div className="font-semibold text-gray-900">{law.text}</div>
                      {law.is_database_item ? (
                        <a
                          href={`/cases/${law.id}`}
                          className="text-blue-600 hover:text-blue-800 text-sm mt-1 inline-block"
                        >
                          View Full Citation →
                        </a>
                      ) : (
                        <div className="text-xs text-gray-500 mt-1">Citation detected (not in database)</div>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-sm">No case laws detected</p>
                )}
              </div>
            </div>

            {/* Column 3: Rules / Acts / Statutes */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                </svg>
                <h2 className="text-xl font-bold text-gray-900">Rules / Acts / Statutes</h2>
              </div>
              <div className="space-y-3">
                {statutes.length > 0 ? (
                  statutes.map((statute, index) => (
                    <div key={index} className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                      <div className="font-semibold text-gray-900">{statute.text}</div>
                      {statute.is_database_item ? (
                        <a
                          href={`/statutes/${statute.id}`}
                          className="text-blue-600 hover:text-blue-800 text-sm mt-1 inline-block"
                        >
                          View Details →
                        </a>
                      ) : (
                        <div className="text-xs text-gray-500 mt-1">Statute detected (will auto-link when added to DB)</div>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-sm">No statutes detected</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Applicable Laws Modal */}
        {showLawsModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
              <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4 flex justify-between items-center">
                <h3 className="text-2xl font-bold text-white">Applicable Laws</h3>
                <button
                  onClick={() => setShowLawsModal(false)}
                  className="text-white hover:text-gray-200 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[calc(80vh-80px)]">
                {applicableLaws.length > 0 ? (
                  <div className="space-y-3">
                    {applicableLaws.map((law, index) => (
                      <div key={index} className="p-4 bg-purple-50 rounded-lg border border-purple-200 hover:bg-purple-100 transition-colors">
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="font-semibold text-gray-900 text-lg">{law.text}</div>
                            <div className="text-sm text-gray-600 mt-1">Type: {law.type}</div>
                          </div>
                          {law.is_database_item && (
                            <a
                              href={`/statutes/${law.id}`}
                              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                            >
                              View →
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    No applicable laws detected in the narrative
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CaseAnalyzerPage;
