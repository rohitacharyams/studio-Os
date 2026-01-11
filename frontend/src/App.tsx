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
import CalendarPage from '@/pages/CalendarPage'
import CheckoutPage from '@/pages/CheckoutPage'
import MyBookingsPage from '@/pages/MyBookingsPage'
import PublicBookingPage from '@/pages/PublicBookingPage'
import ExplorePage from '@/pages/ExplorePage'
import AdminLoginPage from '@/pages/AdminLoginPage'
import AdminDashboardPage from '@/pages/AdminDashboardPage'

function StudioPrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, user, studio } = useAuthStore()
  
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
  
  // Redirect customers to explore page
  if (user?.user_type === 'customer') {
    return <Navigate to="/explore" replace />
  }
  
  // Redirect studio owners to onboarding if not completed
  if (user?.user_type === 'studio_owner' && studio && !studio.onboarding_completed) {
    return <Navigate to="/onboarding" replace />
  }
  
  return <>{children}</>
}

function CustomerPrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, user } = useAuthStore()
  
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
  
  // Redirect studio owners to their dashboard
  if (user?.user_type === 'studio_owner') {
    return <Navigate to="/inbox" replace />
  }
  
  return <>{children}</>
}

function OnboardingRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, user, studio } = useAuthStore()
  
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
  
  // Customers don't need onboarding
  if (user?.user_type === 'customer') {
    return <Navigate to="/explore" replace />
  }
  
  // If already completed onboarding, go to dashboard
  if (studio?.onboarding_completed) {
    return <Navigate to="/inbox" replace />
  }
  
  return <>{children}</>
}

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Admin routes */}
      <Route path="/admin/login" element={<AdminLoginPage />} />
      <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
      
      {/* Public booking pages */}
      <Route path="/book/:studioSlug" element={<PublicBookingPage />} />
      <Route path="/book/:studioSlug/:classId" element={<PublicBookingPage />} />
      
      {/* Onboarding for studio owners */}
      <Route path="/onboarding" element={
        <OnboardingRoute>
          <OnboardingPage />
        </OnboardingRoute>
      } />
      
      {/* Customer routes */}
      <Route path="/explore" element={
        <CustomerPrivateRoute>
          <ExplorePage />
        </CustomerPrivateRoute>
      } />
      <Route path="/customer/bookings" element={
        <CustomerPrivateRoute>
          <MyBookingsPage />
        </CustomerPrivateRoute>
      } />
      
      {/* Studio owner dashboard routes */}
      <Route path="/" element={
        <StudioPrivateRoute>
          <Layout />
        </StudioPrivateRoute>
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
        <Route path="calendar" element={<CalendarPage />} />
        <Route path="checkout" element={<CheckoutPage />} />
        <Route path="my-bookings" element={<MyBookingsPage />} />
      </Route>
    </Routes>
  )
}

export default App
