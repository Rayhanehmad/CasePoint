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
   * User login
   * @param {string} username - Username or email
   * @param {string} password - Password
   * @param {boolean} remember - Remember me
   * @returns {Promise} - Login response
   */
  login: async (username, password, remember = false) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    if (remember) {
      formData.append('remember', 'on')
    }

    const response = await authAPI.post('/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * User registration
   * @param {Object} userData - User data (username, email, password)
   * @returns {Promise} - Registration response
   */
  register: async (userData) => {
    const formData = new FormData()
    formData.append('username', userData.username)
    formData.append('email', userData.email)
    formData.append('password', userData.password)

    const response = await authAPI.post('/register', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * User logout
   * @returns {Promise} - Logout response
   */
  logout: async () => {
    const response = await authAPI.get('/logout')
    return response.data
  },

  /**
   * API-based login (JSON)
   * @param {string} username - Username or email
   * @param {string} password - Password
   * @returns {Promise} - Login response
   */
  apiLogin: async (username, password) => {
    const response = await authAPI.post('/api/login', {
      username,
      password,
    })
    return response.data
  },

  /**
   * API-based registration (JSON)
   * @param {Object} userData - User data
   * @returns {Promise} - Registration response
   */
  apiRegister: async (userData) => {
    const response = await authAPI.post('/api/register', userData)
    return response.data
  },

  /**
   * Get current user profile
   * @returns {Promise} - User profile
   */
  getProfile: async () => {
    const response = await authAPI.get('/profile')
    return response.data
  },
}

export default authService
