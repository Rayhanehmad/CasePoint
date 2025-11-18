import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";

export default function EmbedView() {
  const { id } = useParams();
  const [citation, setCitation] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCitationAndTrack();
  }, [id]);

  const fetchCitationAndTrack = async () => {
    try {
      // Fetch citation details
      const response = await axios.get(`/cases/api/cases/${id}`);
      setCitation(response.data.case);
      
      // Track embed view
      if (response.data.case?.citation) {
        await axios.get(`/api/track_embed/${encodeURIComponent(response.data.case.citation)}`);
      }
    } catch (error) {
      console.error("Error fetching citation:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!citation) {
    return (
      <div className="p-4 bg-white text-gray-800">
        <p className="text-center text-gray-600">Citation not found</p>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white text-gray-800 min-h-screen">
      {/* Header */}
      <div className="border-b pb-4 mb-4">
        <h2 className="text-xl font-bold text-blue-700 mb-2">{citation.citation}</h2>
        <div className="flex flex-wrap gap-3 text-sm text-gray-600">
          {citation.journal && (
            <span className="px-2 py-1 bg-gray-100 rounded">
              {citation.journal}
            </span>
          )}
          {citation.year && (
            <span className="px-2 py-1 bg-gray-100 rounded">
              {citation.year}
            </span>
          )}
          {citation.court && (
            <span className="px-2 py-1 bg-gray-100 rounded">
              {citation.court}
            </span>
          )}
        </div>
      </div>

      {/* Summary */}
      {citation.summary && (
        <div className="mb-4">
          <h3 className="font-semibold text-gray-900 mb-2">Summary</h3>
          <p className="text-sm text-gray-700 leading-relaxed">{citation.summary}</p>
        </div>
      )}

      {/* Keywords */}
      {citation.keywords && (
        <div className="mb-4">
          <h3 className="font-semibold text-gray-900 mb-2">Keywords</h3>
          <div className="flex flex-wrap gap-2">
            {citation.keywords.split(',').map((keyword, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs"
              >
                {keyword.trim()}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Legal Area */}
      {citation.legal_area && (
        <div className="mb-4">
          <span className="text-sm text-gray-600">
            <strong>Legal Area:</strong> {citation.legal_area}
          </span>
        </div>
      )}

      {/* Link to full case */}
      <div className="border-t pt-4 mt-6">
        <a
          href={`${window.location.origin}/cases/${citation.id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-800 font-medium text-sm"
        >
          View full case on CasePoint
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>

      {/* CasePoint Branding */}
      <div className="mt-6 pt-4 border-t text-center">
        <p className="text-xs text-gray-500">
          Powered by <strong className="text-blue-600">CasePoint</strong> - Legal Research Platform
        </p>
      </div>
    </div>
  );
}
