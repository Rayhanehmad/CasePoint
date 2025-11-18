import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, UploadCloud, Sparkles, Menu, Brain, Wand2 } from "lucide-react";

export default function LandingPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [aiQuery, setAiQuery] = useState("");

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query)}`);
    }
  };

  const handleAISearch = () => {
    if (aiQuery.trim()) {
      navigate(`/ai-analysis?q=${encodeURIComponent(aiQuery)}`);
    }
  };

  const aiTools = [
    {
      name: "AI Legal Analysis",
      description: "Get AI-powered insights and analysis on Pakistan law with relevant citations",
      icon: Sparkles,
      href: "/ai-analysis",
      gradient: "from-purple-500 to-pink-500"
    },
    {
      name: "Case Analyzer",
      description: "Generate AI counter-arguments and detect applicable laws from legal narratives",
      icon: Brain,
      href: "/case-analyzer",
      gradient: "from-blue-500 to-cyan-500"
    },
    {
      name: "Citation Generator",
      description: "Create properly formatted legal citations using AI for Pakistan legal standards",
      icon: Wand2,
      href: "/citation-generator",
      gradient: "from-green-500 to-emerald-500"
    }
  ];

  const journals = [
    { code: "PLD", name: "Pakistan Legal Decisions" },
    { code: "MLD", name: "Monthly Law Digest" },
    { code: "SCMR", name: "Supreme Court Monthly Review" },
    { code: "YLR", name: "Yearly Law Reports" },
    { code: "CLC", name: "Civil Law Cases" },
    { code: "CLD", name: "Civil Law Digest" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100 flex flex-col items-center py-10">
      {/* Header */}
      <div className="w-full max-w-4xl flex justify-between items-center px-6 mb-6">
        <div className="flex items-center gap-2">
          <div className="h-10 w-10 bg-gradient-to-br from-blue-600 to-blue-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xl">CP</span>
          </div>
          <h1 className="text-2xl font-bold text-blue-700">CasePoint</h1>
        </div>
        <button 
          onClick={() => navigate('/search')}
          className="p-2 rounded-full bg-white shadow hover:bg-blue-50 transition"
        >
          <Menu className="w-6 h-6 text-blue-600" />
        </button>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="w-full max-w-3xl bg-white/60 backdrop-blur-md rounded-2xl shadow-lg border border-blue-100 p-4 flex items-center gap-3">
        <input
          type="text"
          placeholder="Search by citation, title, or keyword..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 bg-transparent outline-none text-gray-700 text-base placeholder-gray-500"
        />
        <button 
          type="submit"
          className="bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white px-6 py-3 rounded-xl transition flex items-center gap-2"
        >
          <Search className="w-5 h-5" />
          <span>Search</span>
        </button>
      </form>

      {/* AI Search Box */}
      <div className="w-full max-w-3xl mt-10 bg-white/80 backdrop-blur-md border border-blue-100 rounded-3xl p-6 shadow-lg">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="text-blue-500" />
          <h2 className="text-lg font-semibold text-blue-700">AI Search</h2>
        </div>
        <textarea
          value={aiQuery}
          onChange={(e) => setAiQuery(e.target.value)}
          className="w-full h-28 border rounded-xl p-3 text-gray-700 focus:ring-2 focus:ring-blue-400 focus:outline-none resize-none"
          placeholder="Explain a concept, case, or section..."
        ></textarea>

        <div className="mt-4 flex justify-between items-center">
          <label className="flex items-center gap-2 text-blue-600 cursor-pointer hover:underline">
            <UploadCloud className="w-4 h-4" />
            <span className="text-sm">Attach document (PDF, DOCX, TXT)</span>
            <input type="file" hidden accept=".pdf,.docx,.txt" />
          </label>

          <button 
            onClick={handleAISearch}
            className="bg-gradient-to-r from-blue-600 to-blue-500 text-white px-6 py-2 rounded-xl shadow hover:from-blue-700 hover:to-blue-600 transition"
          >
            Search
          </button>
        </div>
      </div>

      {/* AI-Powered Tools */}
      <div className="w-full max-w-4xl mt-10 px-6">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-6 h-6 text-purple-600" />
          <h3 className="text-xl font-semibold text-gray-800">AI-Powered Legal Tools</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {aiTools.map((tool, i) => {
            const Icon = tool.icon;
            return (
              <button
                key={i}
                onClick={() => navigate(tool.href)}
                className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 text-left group overflow-hidden"
              >
                <div className="p-6">
                  <div className={`inline-flex p-3 bg-gradient-to-br ${tool.gradient} rounded-xl text-white mb-4 group-hover:scale-110 transition-transform duration-300`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-purple-600 transition-colors">
                    {tool.name}
                  </h4>
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {tool.description}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Citation Explorer */}
      <div className="w-full max-w-4xl mt-10 px-6">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Citation Explorer</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {journals.map((journal, i) => (
            <button
              key={i}
              onClick={() => navigate(`/search?journal=${journal.code}`)}
              className="bg-white/80 backdrop-blur-sm p-4 rounded-2xl shadow hover:shadow-md transition border border-gray-100 text-left group"
            >
              <h4 className="text-blue-700 font-semibold mb-1 group-hover:text-blue-800 transition">
                {journal.code}
              </h4>
              <p className="text-gray-500 text-sm">
                Explore {journal.name}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="w-full max-w-4xl mt-10 px-6">
        <div className="bg-gradient-to-r from-blue-600 to-blue-500 rounded-3xl p-8 text-white shadow-lg">
          <h3 className="text-2xl font-bold mb-4">Powered by AI & Advanced Search</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold mb-1">10,000+</div>
              <div className="text-blue-100 text-sm">Legal Citations</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold mb-1">AI-Powered</div>
              <div className="text-blue-100 text-sm">Smart Search</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold mb-1">Real-time</div>
              <div className="text-blue-100 text-sm">Document Analysis</div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="w-full max-w-4xl mt-10 px-6 text-center text-gray-500 text-sm">
        <p>© 2025 CasePoint - Professional Legal Research Platform for Pakistan Law</p>
      </div>
    </div>
  );
}
