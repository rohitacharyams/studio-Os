import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '@/lib/api'
import type { User, Studio } from '@/types'

interface AuthState {
  user: User | null
  studio: Studio | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  fetchCurrentUser: () => Promise<void>
  updateUser: (data: Partial<User>) => Promise<void>
}

interface RegisterData {
  email: string
  password: string
  name: string
  user_type: 'studio_owner' | 'customer'
  studio_name?: string
  phone?: string
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      studio: null,
      token: null,
      isAuthenticated: false,
      isLoading: true,

      login: async (email: string, password: string) => {
        const response = await api.post('/auth/login', { email, password })
        const { access_token, user } = response.data
        
        localStorage.setItem('token', access_token)
        
        set({
          user,
          studio: user.studio,
          token: access_token,
          isAuthenticated: true,
          isLoading: false,
        })
      },

      register: async (data: RegisterData) => {
        const response = await api.post('/auth/register', data)
        const { access_token, user } = response.data
        
        localStorage.setItem('token', access_token)
        
        set({
          user,
          studio: user.studio,
          token: access_token,
          isAuthenticated: true,
          isLoading: false,
        })
      },

      logout: () => {
        localStorage.removeItem('token')
        set({
          user: null,
          studio: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        })
      },

      fetchCurrentUser: async () => {
        const token = localStorage.getItem('token')
        
        if (!token) {
          set({ isLoading: false, isAuthenticated: false })
          return
        }
        
        try {
          const response = await api.get('/auth/me')
          const { user } = response.data
          
          set({
            user,
            studio: user.studio,
            token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch {
          localStorage.removeItem('token')
          set({
            user: null,
            studio: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      },

      updateUser: async (data: Partial<User>) => {
        const response = await api.put('/auth/me', data)
        const { user } = response.data
        
        set({
          user,
          studio: user.studio,
        })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
      onRehydrateStorage: () => (state) => {
        state?.fetchCurrentUser()
      },
    }
  )
)
