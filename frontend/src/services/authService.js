/**
 * AuthService - Authentication API calls
 * Handles login, register, logout for Flask session-based auth
 */

import axios from 'axios'

// Use axios directly (not the API instance) for auth to avoid interceptor loops
const authAPI = axios.create({
  baseURL: '/auth',
  timeout: 10000,
  withCredentials: true,
})

const authService = {
  /**
   * User login (JSON API)
   * @param {string} username - Username or email
   * @param {string} password - Password
   * @returns {Promise} - Login response
   */
  login: async (username, password) => {
    const response = await authAPI.post('/login', {
      username,
      password,
    })
    return response.data
  },

  /**
   * User registration (JSON API)
   * @param {Object} userData - User data (username, email, password)
   * @returns {Promise} - Registration response
   */
  register: async (userData) => {
    const response = await authAPI.post('/register', userData)
    return response.data
  },

  /**
   * User logout (JSON API)
   * @returns {Promise} - Logout response
   */
  logout: async () => {
    const response = await authAPI.post('/logout')
    return response.data
  },

  /**
   * Check session status
   * @returns {Promise} - Session status
   */
  checkSession: async () => {
    const response = await authAPI.get('/session')
    return response.data
  },
}

export default authService
