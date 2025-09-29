import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../services/api'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      
      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const response = await api.post('/auth/login', { email, password })
          const { access_token, user } = response.data
          
          set({ 
            user, 
            token: access_token, 
            isLoading: false 
          })
          
          // Set token for future API calls
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
          
          return { success: true }
        } catch (error) {
          set({ isLoading: false })
          return { 
            success: false, 
            error: error.response?.data?.detail || 'Login failed' 
          }
        }
      },
      
      register: async (email, password, full_name) => {
        set({ isLoading: true })
        try {
          const response = await api.post('/auth/register', { 
            email, 
            password, 
            full_name 
          })
          const { access_token, user } = response.data
          
          set({ 
            user, 
            token: access_token, 
            isLoading: false 
          })
          
          // Set token for future API calls
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
          
          return { success: true }
        } catch (error) {
          set({ isLoading: false })
          return { 
            success: false, 
            error: error.response?.data?.detail || 'Registration failed' 
          }
        }
      },
      
      logout: () => {
        set({ user: null, token: null })
        delete api.defaults.headers.common['Authorization']
      },
      
      initializeAuth: () => {
        const { token } = get()
        if (token) {
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`
        }
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        token: state.token 
      }),
    }
  )
)

// Initialize auth on app start
useAuthStore.getState().initializeAuth()