import React from "react";
import axios from "axios";

export default function ShareButtons({ caseId, citation, summary }) {
  const baseUrl = window.location.origin;
  const citationLink = `${baseUrl}/cases/${caseId}`;
  const embedLink = `${baseUrl}/embed/${caseId}`;

  const message = `CasePoint Citation: ${citation}\n\n${summary?.slice(0, 200)}...\nRead more: ${citationLink}`;
  const encodedMessage = encodeURIComponent(message);

  const whatsapp = `https://wa.me/?text=${encodedMessage}`;
  const facebook = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(citationLink)}`;

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(citationLink);
      await axios.get(`/api/track_share/${encodeURIComponent(citation)}`);
      alert("🔗 Link copied!");
    } catch {
      alert("Copy failed");
    }
  };

  const embedHTML = `<iframe src="${embedLink}" width="100%" height="450" style="border:none;border-radius:8px;" title="CasePoint - ${citation}"></iframe>`;

  const handleCopyEmbed = async () => {
    try {
      await navigator.clipboard.writeText(embedHTML);
      await axios.get(`/api/track_share/${encodeURIComponent(citation)}`);
      alert("✅ Embed code copied!");
    } catch {
      alert("Failed to copy embed code");
    }
  };

  const handleShare = async (platform) => {
    try {
      await axios.get(`/api/track_share/${encodeURIComponent(citation)}`);
    } catch (error) {
      console.error("Failed to track share:", error);
    }
  };

  return (
    <div className="flex flex-wrap gap-3 mt-6">
      <a
        href={whatsapp}
        target="_blank"
        rel="noopener noreferrer"
        onClick={() => handleShare('whatsapp')}
        className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
      >
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>
        WhatsApp
      </a>

      <a
        href={facebook}
        target="_blank"
        rel="noopener noreferrer"
        onClick={() => handleShare('facebook')}
        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
      >
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
        Facebook
      </a>

      <button
        onClick={handleCopyLink}
        className="bg-gray-700 hover:bg-gray-800 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
        Copy Link
      </button>

      <button
        onClick={handleCopyEmbed}
        className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
        </svg>
        Embed in Website
      </button>
    </div>
  );
}
