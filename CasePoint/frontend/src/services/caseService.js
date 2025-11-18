/**
 * CaseService - API calls for legal case/citation operations
 * Connects React frontend with Flask backend REST API
 */

import api from './api'

const caseService = {
  /**
   * Search for cases with filters
   * @param {Object} params - Search parameters (q, category, year, court, legal_area, page, per_page)
   * @returns {Promise} - API response with cases
   */
  searchCases: async (params = {}) => {
    const response = await api.get('/search', { params })
    return response.data
  },

  /**
   * Get single case details by ID
   * @param {number} caseId - Case ID
   * @returns {Promise} - API response with case details
   */
  getCaseById: async (caseId) => {
    const response = await api.get(`/case/${caseId}`)
    return response.data
  },

  /**
   * List all cases with pagination
   * @param {Object} params - Query parameters
   * @returns {Promise} - API response with paginated cases
   */
  listCases: async (params = {}) => {
    const response = await api.get('/cases', { params })
    return response.data
  },

  /**
   * List all acts and statutes
   * @param {Object} params - Query parameters (q, page, per_page)
   * @returns {Promise} - API response with acts
   */
  listActs: async (params = {}) => {
    const response = await api.get('/acts', { params })
    return response.data
  },

  /**
   * Upload a legal document
   * @param {File} file - Document file (PDF, DOCX, TXT)
   * @param {Object} metadata - Document metadata (document_type, title)
   * @returns {Promise} - API response with uploaded citation
   */
  uploadDocument: async (file, metadata = {}) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', metadata.document_type || 'case')
    formData.append('title', metadata.title || file.name)

    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Get dashboard statistics
   * @returns {Promise} - API response with stats
   */
  getDashboardStats: async () => {
    const response = await api.get('/dashboard/stats')
    return response.data
  },

  /**
   * Get recent uploaded items
   * @param {number} limit - Number of items to fetch
   * @returns {Promise} - API response with recent items
   */
  getRecentItems: async (limit = 10) => {
    const response = await api.get('/dashboard/recent', {
      params: { limit },
    })
    return response.data
  },

  /**
   * Get filter options - courts
   * @returns {Promise} - List of unique courts
   */
  getCourts: async () => {
    const response = await api.get('/filters/courts')
    return response.data
  },

  /**
   * Get filter options - legal areas
   * @returns {Promise} - List of legal areas
   */
  getLegalAreas: async () => {
    const response = await api.get('/filters/legal-areas')
    return response.data
  },

  /**
   * Get filter options - years
   * @returns {Promise} - List of years
   */
  getYears: async () => {
    const response = await api.get('/filters/years')
    return response.data
  },

  /**
   * AI-powered legal analysis
   * @param {string} query - Legal question
   * @param {Array} filters - Legal filters (jurisdiction, legal_area, etc.)
   * @returns {Promise} - AI analysis response
   */
  aiAnalysis: async (query, filters = {}) => {
    const response = await api.post('/ai/analyze', {
      query,
      filters,
    })
    return response.data
  },
}

export default caseService
