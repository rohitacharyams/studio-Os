import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/api'
import { Building, User, Mail, Phone, Save, Instagram, ExternalLink, CheckCircle, AlertCircle, CreditCard, Copy, Link, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'studio' | 'profile' | 'payment' | 'email' | 'whatsapp' | 'instagram'>('studio')

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500">Manage your studio and connect your channels</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6 overflow-x-auto">
        <nav className="flex gap-2">
          {[
            { id: 'studio', label: 'Studio', icon: Building },
            { id: 'profile', label: 'Profile', icon: User },
            { id: 'payment', label: 'Payment', icon: CreditCard },
            { id: 'email', label: 'Email', icon: Mail },
            { id: 'whatsapp', label: 'WhatsApp', icon: Phone },
            { id: 'instagram', label: 'Instagram', icon: Instagram },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id as typeof activeTab)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                activeTab === id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      {activeTab === 'studio' && <StudioSettings />}
      {activeTab === 'profile' && <ProfileSettings />}
      {activeTab === 'payment' && <PaymentSettings />}
      {activeTab === 'email' && <EmailSettings />}
      {activeTab === 'whatsapp' && <WhatsAppSettings />}
      {activeTab === 'instagram' && <InstagramSettings />}
    </div>
  )
}

function StudioSettings() {
  const queryClient = useQueryClient()
  const { studio } = useAuthStore()
  const [formData, setFormData] = useState({
    name: studio?.name || '',
    email: studio?.email || '',
    phone: studio?.phone || '',
    address: studio?.address || '',
    timezone: studio?.timezone || 'America/New_York',
  })

  const mutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await api.put('/studio', data)
      return response.data.studio
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studio'] })
      toast.success('Studio settings saved')
    },
    onError: () => {
      toast.error('Failed to save settings')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Studio Information</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Studio Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Contact Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Phone</label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Address</label>
            <textarea
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              rows={2}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Timezone</label>
            <select
              value={formData.timezone}
              onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="America/New_York">Eastern Time (ET)</option>
              <option value="America/Chicago">Central Time (CT)</option>
              <option value="America/Denver">Mountain Time (MT)</option>
              <option value="America/Los_Angeles">Pacific Time (PT)</option>
              <option value="America/Phoenix">Arizona Time</option>
              <option value="America/Anchorage">Alaska Time</option>
              <option value="Pacific/Honolulu">Hawaii Time</option>
              <option value="Asia/Kolkata">India Standard Time (IST)</option>
              <option value="Europe/London">London (GMT/BST)</option>
              <option value="Asia/Dubai">Dubai (GST)</option>
              <option value="Asia/Singapore">Singapore (SGT)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Studio Public Link Section */}
      <StudioLinkCard />

      <button
        type="submit"
        disabled={mutation.isPending}
        className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
      >
        <Save className="w-4 h-4" />
        {mutation.isPending ? 'Saving...' : 'Save Changes'}
      </button>
    </form>
  )
}

function StudioLinkCard() {
  const { studio } = useAuthStore()
  const baseUrl = window.location.origin
  const studioUrl = studio?.slug ? `${baseUrl}/book/${studio.slug}` : ''
  
  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    toast.success(`${label} copied to clipboard!`)
  }

  if (!studio?.slug) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-center gap-2 text-amber-800">
          <AlertCircle className="w-5 h-5" />
          <span>Complete your studio setup to get your public booking link.</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
        <Link className="w-5 h-5 text-primary-600" />
        Your Studio Booking Link
      </h3>
      
      <p className="text-sm text-gray-600 mb-4">
        Share this link with your students to let them book classes directly from your studio page.
      </p>
      
      <div className="flex items-center gap-2">
        <div className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
          <code className="text-sm text-primary-600 break-all">{studioUrl}</code>
        </div>
        <button
          onClick={() => copyToClipboard(studioUrl, 'Studio link')}
          className="flex items-center gap-2 px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Copy className="w-4 h-4" />
          Copy
        </button>
        <a
          href={studioUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <ExternalLink className="w-4 h-4" />
          Preview
        </a>
      </div>
      
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>Tip:</strong> Add this link to your Instagram bio, WhatsApp status, or share it in your dance community groups!
        </p>
      </div>
    </div>
  )
}

function ProfileSettings() {
  const { user, updateUser } = useAuthStore()
  const [formData, setFormData] = useState({
    name: user?.name || '',
    password: '',
  })
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      await updateUser(formData)
      setFormData({ ...formData, password: '' })
      toast.success('Profile updated')
    } catch {
      toast.error('Failed to update profile')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Your Profile</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={user?.email || ''}
              disabled
              className="mt-1 block w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              New Password <span className="text-gray-400">(leave blank to keep current)</span>
            </label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="••••••••"
            />
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
      >
        <Save className="w-4 h-4" />
        {isLoading ? 'Saving...' : 'Update Profile'}
      </button>
    </form>
  )
}

function PaymentSettings() {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    payment_method: 'upi',
    upi_id: '',
    upi_name: '',
    bank_name: '',
    account_number: '',
    ifsc_code: '',
    account_holder_name: '',
    razorpay_key_id: '',
    razorpay_key_secret: '',
    stripe_publishable_key: '',
    stripe_secret_key: '',
  })

  // Fetch current payment settings
  const { data, isLoading: loadingSettings } = useQuery({
    queryKey: ['payment-settings'],
    queryFn: async () => {
      try {
        const response = await api.get('/studio/settings/payment')
        return response.data.settings
      } catch {
        return null
      }
    },
  })

  // Update form when data loads
  useState(() => {
    if (data) {
      setFormData(prev => ({ ...prev, ...data }))
    }
  })

  const mutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await api.put('/studio/settings/payment', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payment-settings'] })
      toast.success('Payment settings saved')
    },
    onError: () => {
      toast.error('Failed to save payment settings')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  if (loadingSettings) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
      {/* Payment Method Selection */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Payment Method</h3>
        <p className="text-sm text-gray-500 mb-4">Choose how you want to receive payments from your students</p>
        
        <div className="grid grid-cols-3 gap-3">
          {[
            { id: 'upi', label: 'UPI', desc: 'GPay, PhonePe, Paytm' },
            { id: 'bank', label: 'Bank Transfer', desc: 'Direct bank deposit' },
            { id: 'gateway', label: 'Payment Gateway', desc: 'Razorpay / Stripe' },
          ].map(({ id, label, desc }) => (
            <button
              key={id}
              type="button"
              onClick={() => setFormData({ ...formData, payment_method: id })}
              className={`p-4 rounded-lg border-2 text-left transition-colors ${
                formData.payment_method === id
                  ? 'border-primary-600 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="font-medium text-gray-900">{label}</div>
              <div className="text-xs text-gray-500 mt-1">{desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* UPI Settings */}
      {formData.payment_method === 'upi' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">UPI Details</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">UPI ID</label>
              <input
                type="text"
                value={formData.upi_id}
                onChange={(e) => setFormData({ ...formData, upi_id: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="yourname@upi or 9876543210@paytm"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Name on UPI</label>
              <input
                type="text"
                value={formData.upi_name}
                onChange={(e) => setFormData({ ...formData, upi_name: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="Your name as registered on UPI"
              />
            </div>
          </div>
          
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">
              <strong>Tip:</strong> Students will be able to pay you directly via UPI when booking classes. Make sure your UPI ID is verified and active.
            </p>
          </div>
        </div>
      )}

      {/* Bank Transfer Settings */}
      {formData.payment_method === 'bank' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Bank Account Details</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Bank Name</label>
              <input
                type="text"
                value={formData.bank_name}
                onChange={(e) => setFormData({ ...formData, bank_name: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="e.g., HDFC Bank, SBI, ICICI"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Account Holder Name</label>
              <input
                type="text"
                value={formData.account_holder_name}
                onChange={(e) => setFormData({ ...formData, account_holder_name: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="Name as per bank records"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Account Number</label>
              <input
                type="text"
                value={formData.account_number}
                onChange={(e) => setFormData({ ...formData, account_number: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="Your bank account number"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">IFSC Code</label>
              <input
                type="text"
                value={formData.ifsc_code}
                onChange={(e) => setFormData({ ...formData, ifsc_code: e.target.value.toUpperCase() })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="e.g., HDFC0001234"
              />
            </div>
          </div>
          
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> Bank details will be shown to students for manual transfer. You'll need to manually verify payments.
            </p>
          </div>
        </div>
      )}

      {/* Payment Gateway Settings */}
      {formData.payment_method === 'gateway' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Payment Gateway</h3>
          
          {/* Razorpay */}
          <div className="mb-6">
            <h4 className="font-medium text-gray-800 mb-3 flex items-center gap-2">
              <img src="https://razorpay.com/favicon.ico" alt="Razorpay" className="w-4 h-4" />
              Razorpay (Recommended for India)
            </h4>
            <div className="space-y-4 pl-6 border-l-2 border-gray-200">
              <div>
                <label className="block text-sm font-medium text-gray-700">Key ID</label>
                <input
                  type="text"
                  value={formData.razorpay_key_id}
                  onChange={(e) => setFormData({ ...formData, razorpay_key_id: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  placeholder="rzp_live_xxxxx or rzp_test_xxxxx"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Key Secret</label>
                <input
                  type="password"
                  value={formData.razorpay_key_secret}
                  onChange={(e) => setFormData({ ...formData, razorpay_key_secret: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  placeholder="••••••••"
                />
              </div>
            </div>
          </div>
          
          {/* Stripe */}
          <div>
            <h4 className="font-medium text-gray-800 mb-3 flex items-center gap-2">
              <img src="https://stripe.com/favicon.ico" alt="Stripe" className="w-4 h-4" />
              Stripe (International)
            </h4>
            <div className="space-y-4 pl-6 border-l-2 border-gray-200">
              <div>
                <label className="block text-sm font-medium text-gray-700">Publishable Key</label>
                <input
                  type="text"
                  value={formData.stripe_publishable_key}
                  onChange={(e) => setFormData({ ...formData, stripe_publishable_key: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  placeholder="pk_live_xxxxx or pk_test_xxxxx"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Secret Key</label>
                <input
                  type="password"
                  value={formData.stripe_secret_key}
                  onChange={(e) => setFormData({ ...formData, stripe_secret_key: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  placeholder="••••••••"
                />
              </div>
            </div>
          </div>
          
          <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
            <p className="text-sm text-purple-800">
              <strong>Setup Guide:</strong> Create a free account on{' '}
              <a href="https://dashboard.razorpay.com" target="_blank" rel="noopener noreferrer" className="underline">Razorpay</a> or{' '}
              <a href="https://dashboard.stripe.com" target="_blank" rel="noopener noreferrer" className="underline">Stripe</a>{' '}
              to get your API keys. Use test keys for development.
            </p>
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
      >
        <Save className="w-4 h-4" />
        {mutation.isPending ? 'Saving...' : 'Save Payment Settings'}
      </button>
    </form>
  )
}

function EmailSettings() {
  const queryClient = useQueryClient()
  const [showGmailForm, setShowGmailForm] = useState(false)
  const [showCustomForm, setShowCustomForm] = useState(false)
  const [gmailForm, setGmailForm] = useState({ email: '', app_password: '' })
  const [customForm, setCustomForm] = useState({
    smtp_host: '',
    smtp_port: '587',
    email: '',
    password: '',
    imap_host: '',
    imap_port: '993'
  })

  // Fetch email status
  const { data: status, isLoading } = useQuery({
    queryKey: ['email-status'],
    queryFn: async () => {
      const response = await api.get('/email/status')
      return response.data
    },
  })

  // Connect demo mode
  const connectDemo = useMutation({
    mutationFn: async () => {
      const response = await api.post('/email/connect/demo')
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['email-status'] })
      toast.success(data.message || 'Demo mode enabled!')
    },
    onError: () => {
      toast.error('Failed to enable demo mode')
    },
  })

  // Connect Gmail
  const connectGmail = useMutation({
    mutationFn: async (data: { email: string; app_password: string }) => {
      const response = await api.post('/email/connect/gmail', data)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['email-status'] })
      toast.success(data.message || 'Gmail connected!')
      setShowGmailForm(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to connect Gmail')
    },
  })

  // Connect custom SMTP
  const connectCustom = useMutation({
    mutationFn: async (data: typeof customForm) => {
      const response = await api.post('/email/connect/smtp', data)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['email-status'] })
      toast.success(data.message || 'Email connected!')
      setShowCustomForm(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to connect')
    },
  })

  // Disconnect
  const disconnect = useMutation({
    mutationFn: async () => {
      const response = await api.post('/email/disconnect')
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-status'] })
      toast.success('Email disconnected')
    },
  })

  // Test email
  const testEmail = useMutation({
    mutationFn: async () => {
      const response = await api.post('/email/test')
      return response.data
    },
    onSuccess: (data) => {
      toast.success(data.message || 'Test email sent!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to send test email')
    },
  })

  if (isLoading) {
    return <div className="flex justify-center py-8"><Loader2 className="w-8 h-8 animate-spin text-primary-500" /></div>
  }

  const isConnected = status?.connected

  return (
    <div className="max-w-2xl space-y-6">
      {/* Connection Status */}
      <div className={`rounded-lg border p-6 ${isConnected ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-full ${isConnected ? 'bg-green-100' : 'bg-gray-200'}`}>
              <Mail className={`w-6 h-6 ${isConnected ? 'text-green-600' : 'text-gray-500'}`} />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">
                {isConnected ? 'Email Connected' : 'Email Not Connected'}
              </h3>
              <p className="text-sm text-gray-600">
                {isConnected ? (
                  <>
                    {status?.email} 
                    {status?.demo_mode && <span className="ml-2 px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs">Demo Mode</span>}
                  </>
                ) : 'Connect your email to send and receive messages'}
              </p>
            </div>
          </div>
          {isConnected && (
            <div className="flex gap-2">
              <button
                onClick={() => testEmail.mutate()}
                disabled={testEmail.isPending}
                className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                {testEmail.isPending ? 'Sending...' : 'Send Test'}
              </button>
              <button
                onClick={() => disconnect.mutate()}
                className="px-3 py-1.5 text-sm text-red-600 bg-white border border-red-200 rounded-lg hover:bg-red-50"
              >
                Disconnect
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Connection Options - Show only if not connected */}
      {!isConnected && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Choose how to connect</h3>
          
          {/* Demo Mode - Recommended */}
          <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-purple-900">🎮 Demo Mode</h4>
                  <span className="px-2 py-0.5 bg-purple-200 text-purple-800 rounded text-xs font-medium">Recommended for Testing</span>
                </div>
                <p className="text-sm text-purple-800 mt-1">
                  Test all email features instantly without any setup. Perfect for demos and testing.
                </p>
              </div>
              <button
                onClick={() => connectDemo.mutate()}
                disabled={connectDemo.isPending}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 whitespace-nowrap"
              >
                {connectDemo.isPending ? 'Enabling...' : 'Enable Demo'}
              </button>
            </div>
          </div>

          {/* Gmail Connection */}
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-gray-900">📧 Gmail with App Password</h4>
                  <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">Easy - 5 mins</span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Connect your Gmail account using a secure App Password.
                </p>
              </div>
              <button
                onClick={() => { setShowGmailForm(!showGmailForm); setShowCustomForm(false) }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                {showGmailForm ? 'Cancel' : 'Connect Gmail'}
              </button>
            </div>
            
            {showGmailForm && (
              <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
                  <h5 className="font-medium text-blue-900 mb-2">How to get an App Password:</h5>
                  <ol className="list-decimal list-inside space-y-1 text-blue-800">
                    <li>Go to <a href="https://myaccount.google.com/security" target="_blank" rel="noopener noreferrer" className="underline">Google Account Security</a></li>
                    <li>Enable 2-Factor Authentication if not already enabled</li>
                    <li>Go to <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="underline">App Passwords</a></li>
                    <li>Select "Mail" and your device, click "Generate"</li>
                    <li>Copy the 16-character password (no spaces)</li>
                  </ol>
                </div>
                
                <div className="grid grid-cols-1 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Gmail Address</label>
                    <input
                      type="email"
                      value={gmailForm.email}
                      onChange={(e) => setGmailForm({ ...gmailForm, email: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      placeholder="youremail@gmail.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">App Password</label>
                    <input
                      type="password"
                      value={gmailForm.app_password}
                      onChange={(e) => setGmailForm({ ...gmailForm, app_password: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      placeholder="16-character app password"
                    />
                  </div>
                </div>
                
                <button
                  onClick={() => connectGmail.mutate(gmailForm)}
                  disabled={connectGmail.isPending || !gmailForm.email || !gmailForm.app_password}
                  className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {connectGmail.isPending ? 'Connecting...' : 'Connect Gmail'}
                </button>
              </div>
            )}
          </div>

          {/* Custom SMTP */}
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-semibold text-gray-900">⚙️ Custom SMTP Server</h4>
                <p className="text-sm text-gray-600 mt-1">
                  Advanced: Connect any email provider using SMTP settings.
                </p>
              </div>
              <button
                onClick={() => { setShowCustomForm(!showCustomForm); setShowGmailForm(false) }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                {showCustomForm ? 'Cancel' : 'Configure'}
              </button>
            </div>
            
            {showCustomForm && (
              <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">SMTP Host</label>
                    <input
                      type="text"
                      value={customForm.smtp_host}
                      onChange={(e) => setCustomForm({ ...customForm, smtp_host: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="smtp.example.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">SMTP Port</label>
                    <input
                      type="text"
                      value={customForm.smtp_port}
                      onChange={(e) => setCustomForm({ ...customForm, smtp_port: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="587"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <input
                      type="email"
                      value={customForm.email}
                      onChange={(e) => setCustomForm({ ...customForm, email: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Password</label>
                    <input
                      type="password"
                      value={customForm.password}
                      onChange={(e) => setCustomForm({ ...customForm, password: e.target.value })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>
                
                <button
                  onClick={() => connectCustom.mutate(customForm)}
                  disabled={connectCustom.isPending}
                  className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {connectCustom.isPending ? 'Connecting...' : 'Connect'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function WhatsAppSettings() {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    phone_number: '',
    account_sid: '',
    auth_token: '',
  })

  // Fetch current settings
  useQuery({
    queryKey: ['whatsapp-settings'],
    queryFn: async () => {
      const response = await api.get('/studio/settings/whatsapp')
      return response.data.settings
    },
  })

  const mutation = useMutation({
    mutationFn: async (settings: typeof formData) => {
      const response = await api.put('/studio/settings/whatsapp', settings)
      return response.data.settings
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['whatsapp-settings'] })
      toast.success('WhatsApp settings saved')
    },
    onError: () => {
      toast.error('Failed to save settings')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
      {/* Setup Guide */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-green-900 mb-3 flex items-center gap-2">
          <Phone className="w-5 h-5" />
          How to Connect WhatsApp
        </h3>
        <div className="space-y-3 text-sm text-green-800">
          <div className="flex items-start gap-2">
            <span className="bg-green-200 text-green-800 rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 text-xs font-bold">1</span>
            <span>Create a <a href="https://www.twilio.com/try-twilio" target="_blank" rel="noopener noreferrer" className="text-green-600 underline font-medium">Twilio account</a> (free trial available)</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="bg-green-200 text-green-800 rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 text-xs font-bold">2</span>
            <span>Go to <a href="https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn" target="_blank" rel="noopener noreferrer" className="text-green-600 underline font-medium">Twilio WhatsApp Sandbox</a> and follow setup instructions</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="bg-green-200 text-green-800 rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 text-xs font-bold">3</span>
            <span>Copy your Account SID and Auth Token from the <a href="https://console.twilio.com" target="_blank" rel="noopener noreferrer" className="text-green-600 underline font-medium">Twilio Console</a></span>
          </div>
          <div className="flex items-start gap-2">
            <span className="bg-green-200 text-green-800 rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 text-xs font-bold">4</span>
            <span>For production: Apply for a WhatsApp Business API number through Twilio</span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">WhatsApp Integration (Twilio)</h3>
        <p className="text-sm text-gray-500 mb-4">
          Connect Twilio to send and receive WhatsApp messages from your students.
        </p>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">WhatsApp Number</label>
            <input
              type="text"
              value={formData.phone_number}
              onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="+1234567890"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Twilio Account SID</label>
            <input
              type="text"
              value={formData.account_sid}
              onChange={(e) => setFormData({ ...formData, account_sid: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Twilio Auth Token</label>
            <input
              type="password"
              value={formData.auth_token}
              onChange={(e) => setFormData({ ...formData, auth_token: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-amber-800">
            <strong>Webhook Configuration:</strong> Set your Twilio webhook URL to:
            <code className="block bg-amber-100 px-2 py-1 rounded mt-1 text-xs break-all">
              https://your-domain.com/api/webhooks/whatsapp/twilio
            </code>
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
      >
        <Save className="w-4 h-4" />
        {mutation.isPending ? 'Saving...' : 'Save Settings'}
      </button>
    </form>
  )
}

function InstagramSettings() {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    instagram_username: '',
    access_token: '',
    business_account_id: '',
  })
  const [isConnected, setIsConnected] = useState(false)

  // Fetch current settings
  useQuery({
    queryKey: ['instagram-settings'],
    queryFn: async () => {
      try {
        const response = await api.get('/studio/settings')
        const settings = response.data.settings?.instagram_settings || {}
        if (settings.access_token) {
          setIsConnected(true)
        }
        return settings
      } catch {
        return {}
      }
    },
  })

  const mutation = useMutation({
    mutationFn: async (settings: typeof formData) => {
      const response = await api.put('/studio/settings', {
        instagram_settings: settings
      })
      return response.data.settings
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instagram-settings'] })
      setIsConnected(true)
      toast.success('Instagram settings saved')
    },
    onError: () => {
      toast.error('Failed to save settings')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
      {/* Setup Guide */}
      <div className="bg-gradient-to-r from-pink-50 to-purple-50 border border-pink-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-pink-900 mb-3 flex items-center gap-2">
          <Instagram className="w-5 h-5" />
          How to Connect Instagram
        </h3>
        <div className="space-y-3 text-sm text-pink-800">
          <div className="flex items-start gap-2">
            <span className="bg-pink-200 text-pink-800 rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 text-xs font-bold">1</span>
            <span>Convert your Instagram account to a <strong>Business Account</strong> or <strong>Creator Account</strong></span>
          </div>
          <div className="flex items-start gap-2">
            <span className="bg-pink-200 text-pink-800 rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 text-xs font-bold">2</span>
            <span>Connect your Instagram to a <a href="https://business.facebook.com" target="_blank" rel="noopener noreferrer" className="text-pink-600 underline font-medium">Facebook Business Page</a></span>
          </div>
          <div className="flex items-start gap-2">
            <span className="bg-pink-200 text-pink-800 rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 text-xs font-bold">3</span>
            <span>Create a <a href="https://developers.facebook.com/apps/" target="_blank" rel="noopener noreferrer" className="text-pink-600 underline font-medium">Meta App</a> with Instagram Graph API permissions</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="bg-pink-200 text-pink-800 rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 text-xs font-bold">4</span>
            <span>Generate a long-lived access token and get your Business Account ID</span>
          </div>
        </div>
        <a 
          href="https://developers.facebook.com/docs/instagram-api/getting-started" 
          target="_blank" 
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 mt-4 text-sm text-pink-700 hover:text-pink-900 font-medium"
        >
          View full documentation <ExternalLink className="w-4 h-4" />
        </a>
      </div>

      {isConnected && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
          <CheckCircle className="w-6 h-6 text-green-600" />
          <div>
            <p className="font-medium text-green-800">Instagram Connected</p>
            <p className="text-sm text-green-600">Your Instagram account is connected and ready to receive messages</p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Instagram Integration</h3>
        <p className="text-sm text-gray-500 mb-4">
          Connect your Instagram Business account to receive and respond to DMs from the inbox.
        </p>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Instagram Username</label>
            <div className="mt-1 flex">
              <span className="inline-flex items-center px-3 rounded-l-lg border border-r-0 border-gray-300 bg-gray-50 text-gray-500 text-sm">
                @
              </span>
              <input
                type="text"
                value={formData.instagram_username}
                onChange={(e) => setFormData({ ...formData, instagram_username: e.target.value })}
                className="flex-1 block w-full px-3 py-2 border border-gray-300 rounded-r-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="yourstudio"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Business Account ID</label>
            <input
              type="text"
              value={formData.business_account_id}
              onChange={(e) => setFormData({ ...formData, business_account_id: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="17841400..."
            />
            <p className="mt-1 text-xs text-gray-500">Find this in Meta Business Suite under your connected Instagram account</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Access Token</label>
            <input
              type="password"
              value={formData.access_token}
              onChange={(e) => setFormData({ ...formData, access_token: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="••••••••"
            />
            <p className="mt-1 text-xs text-gray-500">Use a long-lived access token (valid for 60 days)</p>
          </div>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-amber-800">
            <strong>Webhook Configuration:</strong> Set your Meta App webhook callback URL to:
            <code className="block bg-amber-100 px-2 py-1 rounded mt-1 text-xs break-all">
              https://your-domain.com/api/webhooks/instagram
            </code>
            <p className="mt-2">Subscribe to: <code className="bg-amber-100 px-1 rounded">messages</code>, <code className="bg-amber-100 px-1 rounded">messaging_postbacks</code></p>
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
      >
        <Save className="w-4 h-4" />
        {mutation.isPending ? 'Saving...' : 'Save Settings'}
      </button>
    </form>
  )
}
