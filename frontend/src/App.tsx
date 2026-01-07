import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import Layout from '@/components/Layout'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import OnboardingPage from '@/pages/OnboardingPage'
import InboxPage from '@/pages/InboxPage'
import ConversationPage from '@/pages/ConversationPage'
import ContactsPage from '@/pages/ContactsPage'
import AnalyticsPage from '@/pages/AnalyticsPage'
import TemplatesPage from '@/pages/TemplatesPage'
import SettingsPage from '@/pages/SettingsPage'
import KnowledgePage from '@/pages/KnowledgePage'
import BookingPage from '@/pages/BookingPage'
import CheckoutPage from '@/pages/CheckoutPage'
import MyBookingsPage from '@/pages/MyBookingsPage'
import PublicBookingPage from '@/pages/PublicBookingPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthStore()
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/onboarding" element={<OnboardingPage />} />
      <Route path="/book/:studioSlug" element={<PublicBookingPage />} />
      
      <Route path="/" element={
        <PrivateRoute>
          <Layout />
        </PrivateRoute>
      }>
        <Route index element={<Navigate to="/inbox" replace />} />
        <Route path="inbox" element={<InboxPage />} />
        <Route path="inbox/:conversationId" element={<ConversationPage />} />
        <Route path="contacts" element={<ContactsPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="templates" element={<TemplatesPage />} />
        <Route path="knowledge" element={<KnowledgePage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="booking" element={<BookingPage />} />
        <Route path="checkout" element={<CheckoutPage />} />
        <Route path="my-bookings" element={<MyBookingsPage />} />
      </Route>
    </Routes>
  )
}

export default App
