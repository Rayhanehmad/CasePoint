
// KeywordSearch.jsx — React Frontend Component

import React, { useState } from "react";
import axios from "axios";

export default function KeywordSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);

    try {
      const res = await axios.get(`/api/search/keyword?q=${encodeURIComponent(query)}`);
      setResults(res.data.results);
      setTotal(res.data.total);
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto mt-10 p-4">

      {/* Search Bar */}
      <div className="flex gap-3 mb-6">
        <input
          type="text"
          placeholder="Search by keyword (e.g., criminal act, constitution...)"
          className="flex-1 border rounded-xl px-4 py-3 shadow-sm focus:ring-2 focus:ring-blue-400"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        <button
          onClick={handleSearch}
          className="bg-blue-600 text-white px-6 py-3 rounded-xl shadow hover:bg-blue-700"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {/* Total Results */}
      {total > 0 && (
        <p className="text-gray-700 mb-4 font-medium">
          Your search returned <span className="text-blue-700 font-semibold">{total}</span> records.
        </p>
      )}

      {/* Results */}
      <div>
        {results.map((item, idx) => (
          <div key={idx} className="mb-6 p-5 border rounded-xl bg-white shadow">

            {/* Citation Title */}
            <h2 className="text-lg font-bold text-blue-700">
              {item.citation}
            </h2>

            {/* Party Names */}
            {item.party_line && (
              <p className="text-sm text-gray-800 font-medium mt-1">
                {item.party_line}
              </p>
            )}

            {/* Court */}
            {item.court && (
              <p className="text-sm text-gray-600 mt-1">
                {item.court}
              </p>
            )}

            {/* Highlighted Preview */}
            <div
              className="mt-3 text-gray-800 leading-relaxed"
              dangerouslySetInnerHTML={{ __html: item.summary_preview }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
