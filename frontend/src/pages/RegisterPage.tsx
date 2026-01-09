import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'
import { Building2, User, ArrowRight, ArrowLeft } from 'lucide-react'

type UserType = 'studio_owner' | 'customer' | null

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuthStore()
  const [userType, setUserType] = useState<UserType>(null)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    studio_name: '',
    phone: '',
  })
  const [isLoading, setIsLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userType) return
    
    setIsLoading(true)

    try {
      await register({ ...formData, user_type: userType })
      toast.success('Account created successfully!')
      
      // Redirect based on user type
      if (userType === 'studio_owner') {
        navigate('/onboarding')
      } else {
        navigate('/explore')  // Customer dashboard
      }
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to create account')
    } finally {
      setIsLoading(false)
    }
  }

  // User type selection screen
  if (!userType) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-lg w-full space-y-8">
          <div>
            <div className="mx-auto w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-xl">S</span>
            </div>
            <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
              Join Studio OS
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              How do you want to use Studio OS?
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {/* Studio Owner Option */}
            <button
              onClick={() => setUserType('studio_owner')}
              className="relative rounded-xl border-2 border-gray-200 bg-white p-6 shadow-sm hover:border-primary-500 hover:shadow-md transition-all duration-200 text-left group"
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center group-hover:bg-primary-200 transition-colors">
                    <Building2 className="w-6 h-6 text-primary-600" />
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">Studio Owner</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    I run a dance studio and want to manage classes, bookings & communications
                  </p>
                </div>
              </div>
              <ArrowRight className="absolute top-6 right-4 w-5 h-5 text-gray-300 group-hover:text-primary-500 transition-colors" />
            </button>

            {/* Customer Option */}
            <button
              onClick={() => setUserType('customer')}
              className="relative rounded-xl border-2 border-gray-200 bg-white p-6 shadow-sm hover:border-primary-500 hover:shadow-md transition-all duration-200 text-left group"
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center group-hover:bg-green-200 transition-colors">
                    <User className="w-6 h-6 text-green-600" />
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">Dance Student</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    I want to find studios, book classes & track my dance journey
                  </p>
                </div>
              </div>
              <ArrowRight className="absolute top-6 right-4 w-5 h-5 text-gray-300 group-hover:text-primary-500 transition-colors" />
            </button>
          </div>

          <p className="text-center text-sm text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    )
  }

  // Registration form
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <button
            onClick={() => setUserType(null)}
            className="flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back
          </button>
          
          <div className="mx-auto w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-xl">S</span>
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            {userType === 'studio_owner' ? 'Create your studio account' : 'Create your account'}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {userType === 'studio_owner' 
              ? 'Set up your studio and start managing bookings'
              : 'Start exploring dance studios and booking classes'}
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            {/* Studio name - only for studio owners */}
            {userType === 'studio_owner' && (
              <div>
                <label htmlFor="studio_name" className="block text-sm font-medium text-gray-700">
                  Studio Name
                </label>
                <input
                  id="studio_name"
                  name="studio_name"
                  type="text"
                  required
                  value={formData.studio_name}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Your Dance Studio"
                />
              </div>
            )}

            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                Your Name
              </label>
              <input
                id="name"
                name="name"
                type="text"
                required
                value={formData.name}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="John Doe"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
                Phone {userType === 'customer' ? '(for booking confirmations)' : '(optional)'}
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                required={userType === 'customer'}
                value={formData.phone}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="+91 98765 43210"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                minLength={6}
                value={formData.password}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : userType === 'studio_owner' ? (
              'Create Studio Account'
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <p className="text-center text-sm text-gray-600">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
