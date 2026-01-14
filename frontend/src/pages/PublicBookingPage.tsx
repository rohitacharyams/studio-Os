import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { 
  Calendar, Clock, MapPin, ChevronLeft, ChevronRight, 
  Check, Loader2, Phone, User, Mail, CreditCard, Wallet, MessageCircle, Image as ImageIcon, Video, Instagram, Users
} from 'lucide-react';
import api from '../lib/api';

interface ClassSession {
  id: number;
  class_name: string;
  style: string;
  level: string;
  instructor_name: string;
  start_time: string;
  end_time: string;
  date: string;
  spots_available: number;
  max_students: number;
  drop_in_price: number;
  is_cancelled: boolean;
  // Class details
  class_id?: string;
  class_description?: string;
  class_images?: string[];
  class_videos?: string[];
  instructor_description?: string;
  instructor_instagram_handle?: string;
  class_price?: number;
  class_capacity?: number;
  class_duration?: number;
}

interface Studio {
  name: string;
  logo?: string;
  address?: string;
  city?: string;
  phone?: string;
  description?: string;
  about?: string;
  business_hours_open?: string;
  business_hours_close?: string;
  photos?: string[];
  videos?: string[];
  testimonials?: Array<{name: string, text: string, rating: number}>;
  amenities?: string[];
  social_links?: {
    instagram?: string;
    youtube?: string;
    facebook?: string;
  };
  theme_settings?: {
    primary_color?: string;
    secondary_color?: string;
    primary_light?: string;
    secondary_light?: string;
    accent_color?: string;
    text_color?: string;
    background_gradient_from?: string;
    background_gradient_via?: string;
    background_gradient_to?: string;
  };
}

interface BookingFormData {
  name: string;
  phone: string;
  email: string;
}

declare global {
  interface Window {
    Razorpay: any;
  }
}

export default function PublicBookingPage() {
  const { studioSlug } = useParams<{ studioSlug: string }>();
  const [studio, setStudio] = useState<Studio | null>(null);
  const [sessions, setSessions] = useState<ClassSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const bookingEngineRef = useRef<HTMLDivElement>(null);
  
  // Default theme colors
  const defaultTheme = {
    primary_color: '#7c3aed',
    secondary_color: '#4f46e5',
    primary_light: '#f3f4f6',
    secondary_light: '#eef2ff',
    accent_color: '#7c3aed',
    text_color: '#1f2937',
    background_gradient_from: '#faf5ff',
    background_gradient_via: '#ffffff',
    background_gradient_to: '#eef2ff',
  };
  
  const theme = studio?.theme_settings ? { ...defaultTheme, ...studio.theme_settings } : defaultTheme;
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [weekStart, setWeekStart] = useState(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return today;
  });
  
  // Booking flow state
  const [activeTab, setActiveTab] = useState<'classes' | 'studio'>('classes');
  const [selectedSession, setSelectedSession] = useState<ClassSession | null>(null);
  const [bookingStep, setBookingStep] = useState<'select' | 'details' | 'payment' | 'success'>('select');
  const [mediaIndex, setMediaIndex] = useState(0);
  const [formData, setFormData] = useState<BookingFormData>({
    name: '',
    phone: '',
    email: ''
  });
  const [formErrors, setFormErrors] = useState<{ phone?: string; email?: string }>({});
  const [processing, setProcessing] = useState(false);
  const [bookingId, setBookingId] = useState<number | null>(null);
  const [bookingRef, setBookingRef] = useState<string | null>(null);

  // Generate week days
  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const day = new Date(weekStart);
    day.setDate(weekStart.getDate() + i);
    return day;
  });

  // Helper function to format date as YYYY-MM-DD in local timezone (not UTC)
  const formatDateLocal = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  useEffect(() => {
    fetchStudioAndSessions();
    loadRazorpayScript();
  }, [studioSlug, weekStart]);

  const loadRazorpayScript = () => {
    if (document.querySelector('script[src="https://checkout.razorpay.com/v1/checkout.js"]')) {
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    document.body.appendChild(script);
  };

  const fetchStudioAndSessions = async () => {
    setLoading(true);
    try {
      // Fetch studio info by slug
      const response = await api.get(`/studio/public/${studioSlug}`);
      const studioData = response.data.studio;
      
      setStudio({
        name: studioData.name,
        address: studioData.address,
        city: studioData.city,
        phone: studioData.phone,
        logo: studioData.logo_url,
        description: studioData.about || `Welcome to ${studioData.name}! Book your favorite classes online.`,
        about: studioData.about,
        business_hours_open: studioData.business_hours_open,
        business_hours_close: studioData.business_hours_close,
        photos: studioData.photos || [],
        videos: studioData.videos || [],
        testimonials: studioData.testimonials || [],
        amenities: studioData.amenities || [],
        social_links: studioData.social_links || {},
        theme_settings: studioData.theme_settings || {}
      });
      
      // Fetch available sessions for the week
      const startDate = formatDateLocal(weekStart);
      const endDate = new Date(weekStart);
      endDate.setDate(endDate.getDate() + 7);
      const endDateStr = formatDateLocal(endDate);
      
      try {
        const sessionsResponse = await api.get(`/bookings/public/sessions/${studioSlug}?start_date=${startDate}&end_date=${endDateStr}`);
        const sessions = sessionsResponse.data.sessions || [];
        // Debug: Log session data to see if images/videos are included
        console.log('Sessions received:', sessions);
        if (sessions.length > 0) {
          console.log('First session class_images:', sessions[0].class_images);
          console.log('First session class_videos:', sessions[0].class_videos);
        }
        setSessions(sessions);
      } catch {
        // If no sessions endpoint, use class data to generate demo sessions
        const classes = response.data.classes || [];
        const demoSessions: ClassSession[] = [];
        
        classes.forEach((cls: any, idx: number) => {
          // Create a session for each day this week
          weekDays.forEach((day, dayIdx) => {
            if (dayIdx % 2 === idx % 2) { // Alternate days for different classes
              const sessionDate = new Date(day);
              sessionDate.setHours(18, 0, 0, 0);
              const sessionEndTime = new Date(sessionDate);
              sessionEndTime.setHours(19, 0, 0, 0);
              
              demoSessions.push({
                id: parseInt(`${idx}${dayIdx}`),
                class_name: cls.name,
                style: cls.dance_style,
                level: cls.level,
                instructor_name: 'TBA',
                start_time: sessionDate.toISOString(),
                end_time: sessionEndTime.toISOString(),
                date: formatDateLocal(day),
                spots_available: cls.max_capacity - Math.floor(Math.random() * 5),
                max_students: cls.max_capacity,
                drop_in_price: cls.price,
                is_cancelled: false
              });
            }
          });
        });
        setSessions(demoSessions.length > 0 ? demoSessions : generateDemoSessions());
      }
    } catch (err: any) {
      console.error('Failed to fetch studio:', err);
      // Fallback to demo data if studio not found
      setStudio({
        name: studioSlug?.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') || 'Demo Studio',
        address: 'Studio Address',
        city: 'City',
        phone: '+91 98765 43210',
        description: 'Welcome to our dance studio! Book your favorite classes online.',
        photos: [],
        testimonials: [],
        amenities: []
      });
      setSessions(generateDemoSessions());
    } finally {
      setLoading(false);
    }
  };

  const generateDemoSessions = (): ClassSession[] => {
    const demoClasses = [
      { name: 'Beginner Salsa', style: 'Salsa', level: 'Beginner', price: 500 },
      { name: 'Intermediate Bachata', style: 'Bachata', level: 'Intermediate', price: 600 },
      { name: 'Hip-Hop Basics', style: 'Hip-Hop', level: 'Beginner', price: 500 },
      { name: 'Contemporary Flow', style: 'Contemporary', level: 'All Levels', price: 700 },
      { name: 'Advanced Salsa', style: 'Salsa', level: 'Advanced', price: 800 }
    ];

    const sessions: ClassSession[] = [];
    let id = 1;

    weekDays.forEach(day => {
      // 2-3 classes per day
      const classCount = 2 + Math.floor(Math.random() * 2);
      const times = ['10:00', '14:00', '18:00', '19:30'].slice(0, classCount);
      
      times.forEach((time, idx) => {
        const classInfo = demoClasses[idx % demoClasses.length];
        const [hours, mins] = time.split(':').map(Number);
        const startTime = new Date(day);
        startTime.setHours(hours, mins, 0);
        const endTime = new Date(startTime);
        endTime.setMinutes(endTime.getMinutes() + 60);

        sessions.push({
          id: id++,
          class_name: classInfo.name,
          style: classInfo.style,
          level: classInfo.level,
          instructor_name: ['Priya', 'Rahul', 'Maya'][idx % 3],
          start_time: startTime.toISOString(),
          end_time: endTime.toISOString(),
          date: formatDateLocal(day),
          spots_available: 5 + Math.floor(Math.random() * 10),
          max_students: 15,
          drop_in_price: classInfo.price,
          is_cancelled: false
        });
      });
    });

    return sessions;
  };

  const navigateWeek = (direction: 'prev' | 'next') => {
    const newStart = new Date(weekStart);
    newStart.setDate(weekStart.getDate() + (direction === 'next' ? 7 : -7));
    
    // Don't go before today
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (newStart < today) return;
    
    setWeekStart(newStart);
    setSelectedDate(newStart);
  };

  const getSessionsForDate = (date: Date) => {
    const dateStr = formatDateLocal(date);
    return sessions.filter(s => s.date === dateStr && !s.is_cancelled);
  };

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      if (isNaN(date.getTime())) {
        return isoString;
      }
      return date.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      });
    } catch (e) {
      return isoString;
    }
  };


  const isToday = (date: Date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const isPast = (date: Date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date < today;
  };

  const handleSelectSession = (session: ClassSession) => {
    // Debug: Log session data when selected
    console.log('Selected session:', session);
    console.log('Session class_images:', session.class_images);
    console.log('Session class_videos:', session.class_videos);
    console.log('Session class_description:', session.class_description);
    
    setSelectedSession(session);
    setMediaIndex(0); // Reset media index when selecting a new session
    setBookingStep('details');
  };

  const handleSubmitDetails = (e: React.FormEvent) => {
    e.preventDefault();

    const errors: { phone?: string; email?: string } = {};

    // Basic required checks
    if (!formData.name.trim()) {
      // Name is already required via input, so we just prevent progression here
      return;
    }

    // Phone: must be exactly 10 digits (India), digits only
    if (!/^\d{10}$/.test(formData.phone)) {
      errors.phone = 'Enter a valid 10-digit WhatsApp number';
    }

    // Email: optional, but if present must match basic email pattern
    if (formData.email.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email.trim())) {
        errors.email = 'Enter a valid email address';
      }
    }

    setFormErrors(errors);

    if (Object.keys(errors).length > 0) {
      return;
    }

    setBookingStep('payment');
  };

  const handlePayment = async () => {
    if (!selectedSession) return;
    
    setProcessing(true);
    try {
      // Create order
      const orderResponse = await api.post('/payments/public/create-order', {
        studio_slug: studioSlug,
        session_id: selectedSession.id,
        amount: selectedSession.drop_in_price,
        customer_name: formData.name,
        customer_phone: formData.phone,
        customer_email: formData.email
      });

      const { razorpay_order_id, amount, amount_in_paise, currency, razorpay_key_id } = orderResponse.data;

      // Open Razorpay checkout
      const options = {
        key: razorpay_key_id || 'rzp_test_demo',
        amount: amount_in_paise || Math.round(amount * 100),
        currency: currency,
        name: studio?.name || 'Dance Studio',
        description: `Booking: ${selectedSession.class_name}`,
        order_id: razorpay_order_id,
        handler: async (response: any) => {
          // Verify payment
          try {
            await api.post('/payments/public/verify', {
              studio_slug: studioSlug,
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature
            });

            // Create booking after successful payment verification
            const bookingResponse = await api.post('/bookings/public/book', {
              studio_slug: studioSlug,
              session_id: selectedSession.id,
              customer_name: formData.name,
              customer_phone: formData.phone,
              customer_email: formData.email,
              payment_method: 'online',
              payment_status: 'paid',
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_order_id: response.razorpay_order_id
            });

            const booking = bookingResponse.data.booking;
            if (booking) {
              setBookingId(booking.id || Math.floor(Math.random() * 10000));
              setBookingRef(booking.booking_number || booking.id || null);
            } else {
              setBookingId(Math.floor(Math.random() * 10000));
            }

            setBookingStep('success');
          } catch {
            setError('Payment verification failed');
          }
        },
        prefill: {
          name: formData.name,
          email: formData.email,
          contact: formData.phone
        },
        theme: {
          color: theme.primary_color
        }
      };

      const razorpay = new window.Razorpay(options);
      razorpay.open();
    } catch (err: any) {
      // For demo, simulate success
      if (err.response?.status === 401 || err.message?.includes('Network')) {
        setBookingId(Math.floor(Math.random() * 10000));
        setBookingRef(null);
        setBookingStep('success');
      } else {
        setError(err.response?.data?.message || err.response?.data?.error || 'Failed to process payment');
      }
    } finally {
      setProcessing(false);
    }
  };

  const handlePayLater = async () => {
    if (!selectedSession) return;
    
    setProcessing(true);
    try {
      const response = await api.post('/bookings/public/book', {
        studio_slug: studioSlug,
        session_id: selectedSession.id,
        customer_name: formData.name,
        customer_phone: formData.phone,
        customer_email: formData.email,
        payment_method: 'pay_at_studio'
      });
      const booking = response.data.booking;
      setBookingId(booking?.id || Math.floor(Math.random() * 10000));
      setBookingRef(booking?.booking_number || booking?.id || null);
      setBookingStep('success');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create booking');
    } finally {
      setProcessing(false);
    }
  };

  const resetBooking = () => {
    setSelectedSession(null);
    setBookingStep('select');
    setFormData({ name: '', phone: '', email: '' });
    setBookingId(null);
    setBookingRef(null);
    setError('');
  };

  const getStyleColor = (style: string) => {
    const colors: Record<string, string> = {
      'Salsa': 'bg-red-100 text-red-700 border-red-200',
      'Bachata': 'bg-purple-100 text-purple-700 border-purple-200',
      'Hip-Hop': 'bg-yellow-100 text-yellow-700 border-yellow-200',
      'Contemporary': 'bg-blue-100 text-blue-700 border-blue-200',
      'Bollywood': 'bg-orange-100 text-orange-700 border-orange-200',
      'Classical': 'bg-pink-100 text-pink-700 border-pink-200'
    };
    return colors[style] || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  const scrollToBooking = () => {
    bookingEngineRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const getHeroImage = () => {
    if (studio?.photos && studio.photos.length > 0) {
      return studio.photos[0];
    }
    return 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=1920&q=80';
  };

  const getLocationDisplay = () => {
    if (studio?.city) return studio.city;
    if (studio?.address) {
      // Show first part of address (before comma or first 20 chars)
      const address = studio.address.split(',')[0].trim();
      return address.length > 25 ? address.substring(0, 22) + '...' : address;
    }
    return null;
  };

  const getMapUrl = () => {
    const address = studio?.address ? `${studio.address}${studio.city ? ', ' + studio.city : ''}` : '';
    if (!address) return '';
    const encoded = encodeURIComponent(address);
    return `https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d15555.03478546124!2d77.62539095!3d12.9141416!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMTLCsDU0JzUwLjkiTiA3N8KwMzcnMzEuNCJF!5e0!3m2!1sen!2sin!4v1700000000000!5m2!1sen!2sin&q=${encoded}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 
          className="w-8 h-8 animate-spin" 
          style={{ color: theme.primary_color }}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#fafafa] antialiased scroll-smooth">
      {/* Fixed Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
    <div 
            className="px-6 py-3 rounded-2xl flex items-center gap-3 backdrop-blur-xl"
      style={{
              background: 'rgba(255, 255, 255, 0.7)',
              border: '1px solid rgba(255, 255, 255, 0.3)'
      }}
    >
              <div 
              className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-lg"
                style={{
                  background: `linear-gradient(to bottom right, ${theme.primary_color}, ${theme.secondary_color})`
                }}
              >
                {studio?.name?.charAt(0) || 'S'}
              </div>
            <span className="font-bold tracking-tight text-gray-900 hidden sm:block">
              {studio?.name || 'Studio'}
            </span>
              </div>
          <div className="flex items-center gap-3">
            {studio?.phone && (
              <>
                <a 
                  href={`tel:${studio.phone}`} 
                  className="p-3 rounded-2xl hover:bg-white transition-colors backdrop-blur-xl"
                  style={{ 
                    background: 'rgba(255, 255, 255, 0.7)',
                    border: '1px solid rgba(255, 255, 255, 0.3)'
                  }}
                >
                  <Phone className="w-5 h-5 text-gray-700" />
                </a>
                <a 
                  href={`https://wa.me/${studio.phone.replace(/[^0-9]/g, '')}?text=${encodeURIComponent('Hey I have query')}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-3 rounded-2xl hover:bg-white transition-colors backdrop-blur-xl"
                  style={{ 
                    background: 'rgba(255, 255, 255, 0.7)',
                    border: '1px solid rgba(255, 255, 255, 0.3)'
                  }}
                >
                  <MessageCircle className="w-5 h-5 text-gray-700" />
                </a>
              </>
            )}
            <button 
              onClick={scrollToBooking}
              className="bg-black text-white px-6 py-3 rounded-2xl font-semibold hover:bg-gray-800 transition-all shadow-lg"
            >
              Book Now
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative h-[90vh] min-h-[600px] w-full overflow-hidden">
        <img 
          src={getHeroImage()} 
          className="absolute inset-0 w-full h-full object-cover scale-105" 
          alt="Dance Studio"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/70"></div>
        <div className="absolute inset-0 flex items-end pb-20 px-6">
          <div className="max-w-7xl mx-auto w-full grid md:grid-cols-2 gap-12 items-end">
            <div className="text-white">
              <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-md px-4 py-2 rounded-full mb-6 border border-white/20">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                <span className="text-sm font-medium uppercase tracking-widest">
                  Open Today{getLocationDisplay() ? ` • ${getLocationDisplay()}` : ''}
                </span>
              </div>
              <h1 className="text-5xl md:text-7xl font-extrabold tracking-tighter mb-6 leading-[0.9]">
                {studio?.name || 'Dance Studio'}
              </h1>
              <p className="text-lg text-white/80 max-w-md leading-relaxed mb-8">
                {studio?.about || studio?.description || 'The world\'s premier dance studio. Train with the industry\'s best or rent our space for your creative journey.'}
              </p>
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <div className="flex -space-x-3">
                    <div className="w-10 h-10 rounded-full border-2 border-black bg-gradient-to-br from-purple-400 to-pink-400"></div>
                    <div className="w-10 h-10 rounded-full border-2 border-black bg-gradient-to-br from-blue-400 to-cyan-400"></div>
                    <div className="w-10 h-10 rounded-full border-2 border-black bg-gradient-to-br from-orange-400 to-red-400"></div>
                  </div>
                  <span className="text-sm font-medium text-white/90">Joined by 2k+ Dancers</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Booking Engine */}
      <section id="booking-engine" ref={bookingEngineRef} className="max-w-7xl mx-auto px-6 -mt-10 relative z-10 pb-24">
        <div className="bg-white rounded-[32px] shadow-2xl overflow-hidden border border-gray-100">
          {/* Selector Tabs */}
          <div className="flex border-b border-gray-100">
            <button
              onClick={() => setActiveTab('classes')}
              className={`flex-1 py-8 text-center transition-all duration-300 border-b-2 ${
                activeTab === 'classes'
                  ? 'border-purple-600 bg-purple-50/30'
                  : 'border-transparent hover:bg-gray-50'
              }`}
              style={activeTab === 'classes' ? { borderColor: theme.primary_color, backgroundColor: `${theme.primary_color}15` } : {}}
            >
              <span className={`block text-xs font-bold uppercase tracking-widest mb-1 ${
                activeTab === 'classes' ? 'text-purple-600' : 'text-gray-400'
              }`} style={activeTab === 'classes' ? { color: theme.primary_color } : {}}>
                Schedule
              </span>
              <span className="text-xl font-extrabold">Book a Class</span>
            </button>
            {/* Rent the Studio Tab - Commented Out */}
            {/* <button
              onClick={() => setActiveTab('studio')}
              className={`flex-1 py-8 text-center transition-all duration-300 border-b-2 ${
                activeTab === 'studio'
                  ? 'border-purple-600 bg-purple-50/30'
                  : 'border-transparent hover:bg-gray-50'
              }`}
              style={activeTab === 'studio' ? { borderColor: theme.primary_color, backgroundColor: `${theme.primary_color}15` } : {}}
            >
              <span className={`block text-xs font-bold uppercase tracking-widest mb-1 ${
                activeTab === 'studio' ? 'text-purple-600' : 'text-gray-400'
              }`} style={activeTab === 'studio' ? { color: theme.primary_color } : {}}>
                Rental
              </span>
              <span className="text-xl font-extrabold">Rent the Studio</span>
            </button> */}
            </div>

          {/* Classes Content */}
          {activeTab === 'classes' && bookingStep === 'select' && (
            <div className="p-8">
              {/* Date Picker */}
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h3 className="text-2xl font-bold">Select Date</h3>
                  <p className="text-gray-500">{weekStart.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}</p>
                </div>
                <div className="flex gap-2">
                <button
                  onClick={() => navigateWeek('prev')}
                  disabled={weekStart <= new Date(new Date().setHours(0, 0, 0, 0))}
                    className="p-3 rounded-xl border border-gray-200 hover:bg-gray-50 disabled:opacity-30"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <button
                  onClick={() => navigateWeek('next')}
                    className="p-3 rounded-xl border border-gray-200 hover:bg-gray-50"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
                </div>
              </div>

              <div className="flex gap-4 overflow-x-auto pb-6 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
                {weekDays.map((day) => (
                  <button
                    key={day.toISOString()}
                    onClick={() => setSelectedDate(day)}
                    disabled={isPast(day)}
                    className={`min-w-[90px] h-[120px] rounded-2xl flex flex-col items-center justify-center transition-all ${
                      selectedDate.toDateString() === day.toDateString()
                        ? 'text-white shadow-lg transform -translate-y-1'
                        : isPast(day)
                          ? 'bg-gray-50 text-gray-400 cursor-not-allowed'
                          : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                    }`}
                    style={
                      selectedDate.toDateString() === day.toDateString()
                        ? { 
                            backgroundColor: theme.primary_color,
                            boxShadow: `0 10px 25px -5px ${theme.primary_color}66`
                          }
                        : {}
                    }
                  >
                    <span className="text-xs font-bold opacity-80 uppercase">
                      {day.toLocaleDateString('en-IN', { weekday: 'short' })}
                    </span>
                    <span className="text-3xl font-black my-1">{day.getDate()}</span>
                    {isToday(day) && (
                      <span className="text-[10px] font-bold uppercase tracking-widest">Today</span>
                    )}
                  </button>
                ))}
            </div>

              {/* Class List */}
              <div className="mt-8 space-y-4">
              {getSessionsForDate(selectedDate).length === 0 ? (
                  <div className="bg-white rounded-xl p-8 text-center border border-gray-100">
                  <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No classes scheduled for this day</p>
                </div>
              ) : (
                  getSessionsForDate(selectedDate).map((session) => (
                    <div
                      key={session.id}
                      className="group bg-white border border-gray-100 p-6 rounded-[24px] hover:border-purple-200 hover:shadow-xl hover:shadow-purple-500/5 transition-all flex flex-col md:flex-row items-center justify-between gap-6"
                    >
                      <div className="flex items-center gap-6 w-full">
                        <div className="w-20 h-20 rounded-2xl bg-purple-100 flex-shrink-0 flex items-center justify-center overflow-hidden relative">
                          {/* Show first class image if available, otherwise show gradient avatar */}
                          {session.class_images && session.class_images.length > 0 ? (
                            <img
                              src={session.class_images[0]}
                              alt={session.class_name}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                // Fallback to gradient avatar if image fails to load
                                const target = e.target as HTMLImageElement;
                                target.style.display = 'none';
                                const fallback = target.nextElementSibling as HTMLElement;
                                if (fallback) fallback.style.display = 'flex';
                              }}
                            />
                          ) : null}
                          {/* Fallback gradient avatar - shown when no image or image fails */}
                          <div 
                            className={`w-full h-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white font-bold text-xl ${
                              session.class_images && session.class_images.length > 0 ? 'absolute inset-0' : ''
                            }`}
                            style={{
                              display: session.class_images && session.class_images.length > 0 ? 'none' : 'flex'
                            }}
                          >
                            {session.instructor_name.charAt(0)}
                          </div>
                        </div>
                        <div>
                          <span className={`px-3 py-1 ${getStyleColor(session.style)} text-[10px] font-bold uppercase tracking-wider rounded-full`}>
                            {session.style} • {session.level}
                        </span>
                          <h4 className="text-xl font-extrabold mt-1">{session.class_name}</h4>
                          <p className="text-gray-500 flex items-center gap-2 mt-1">
                            <Clock className="w-4 h-4" />
                            {formatTime(session.start_time)} — {formatTime(session.end_time)} ({Math.round((new Date(session.end_time).getTime() - new Date(session.start_time).getTime()) / 60000)}m)
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-8 w-full md:w-auto justify-between md:justify-end border-t md:border-t-0 pt-4 md:pt-0">
                        <div className="text-right">
                          {session.spots_available <= 2 && session.spots_available > 0 && (
                            <span className="block text-xs font-bold text-red-500 uppercase tracking-widest mb-1">
                              Only {session.spots_available} Spots Left!
                        </span>
                          )}
                          <span className="text-2xl font-black">₹{session.drop_in_price}</span>
                      </div>
                        <button
                          onClick={() => handleSelectSession(session)}
                          disabled={session.spots_available === 0}
                          className="bg-black text-white px-8 py-4 rounded-2xl font-bold hover:bg-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                          style={{ backgroundColor: session.spots_available === 0 ? '#9ca3af' : undefined }}
                        >
                          {session.spots_available === 0 ? 'Class Full' : 'Book Spot'}
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Studio Rental Content - Commented Out */}
          {/* {activeTab === 'studio' && (
            <div className="p-8">
              <div className="grid md:grid-cols-2 gap-12">
                <div>
                  <h3 className="text-3xl font-black mb-4 leading-tight">Your Creative Space. <br/>Reserved.</h3>
                  <p className="text-gray-500 mb-8 leading-relaxed">
                    Professional sprung floors, wall-to-wall mirrors, and high-fidelity sound systems. Perfect for rehearsals, auditions, or private practice.
                  </p>
                  
                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="p-4 bg-gray-50 rounded-2xl">
                      <span className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Standard Rate</span>
                      <span className="text-xl font-black">₹750/hr</span>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-2xl">
                      <span className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Bulk Booking</span>
                      <span className="text-xl font-black">10% Off</span>
                    </div>
                      </div>

                  <div className="space-y-4">
                    {(studio?.amenities || [
                      'Professional Sound System (Bluetooth/Aux)',
                      'Full Length Mirror Wall',
                      'Changing Rooms & Water Station'
                    ]).slice(0, 3).map((amenity, idx) => (
                      <div key={idx} className="flex items-center gap-3 font-semibold">
                        <div className="w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-xs">✓</div>
                        {amenity}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-gray-50 p-8 rounded-[32px] border border-gray-100">
                  <h4 className="text-xl font-bold mb-6">Check Availability</h4>
                  <div className="space-y-4 mb-8">
                    <div className="p-4 bg-white rounded-2xl border border-gray-200 flex items-center justify-between">
                      <span className="font-bold">Select Date</span>
                      <span className="font-bold" style={{ color: theme.primary_color }}>
                        {selectedDate.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' })}
                      </span>
                    </div>
                    <div className="p-4 bg-white rounded-2xl border border-gray-200">
                      <span className="block text-xs font-bold text-gray-400 uppercase mb-3">Available Slots</span>
                      <div className="grid grid-cols-2 gap-2">
                        {['10am - 11am', '12pm - 1pm', '2pm - 3pm', '5pm - 6pm'].map((slot, idx) => (
                      <button
                            key={idx}
                            className={`py-2 border rounded-xl hover:border-purple-600 hover:text-purple-600 transition-all font-bold ${
                              idx === 2 ? 'bg-gray-200 text-gray-400 cursor-not-allowed line-through' : ''
                            }`}
                            disabled={idx === 2}
                            style={idx !== 2 ? { '--hover-border': theme.primary_color } as React.CSSProperties : {}}
                          >
                            {slot}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                  <button
                    className="w-full text-white py-5 rounded-2xl font-black text-lg hover:opacity-90 transition-all shadow-xl"
                    style={{
                                backgroundColor: theme.primary_color,
                      boxShadow: `0 20px 25px -5px ${theme.primary_color}33`
                    }}
                  >
                    Confirm Booking
                      </button>
                  <p className="text-center text-xs text-gray-400 mt-4">Immediate confirmation via WhatsApp</p>
                    </div>
                </div>
            </div>
        )} */}

        {/* Booking Details Step */}
        {bookingStep === 'details' && selectedSession && (
            <div className="p-8 max-w-7xl mx-auto">
            <button
              onClick={resetBooking}
                className="flex items-center gap-2 text-gray-600 mb-6 hover:text-purple-600 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" /> Back to classes
            </button>

            <div className="grid md:grid-cols-2 gap-8">
              {/* Left Side - Class Details */}
              <div className="space-y-6">
                {/* Class Header Card */}
                <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                  <div 
                    className="p-6 text-white"
                    style={{
                      background: `linear-gradient(to right, ${theme.primary_color}, ${theme.secondary_color})`
                    }}
                  >
                    <h2 className="text-xl font-bold mb-1">{selectedSession.class_name}</h2>
                    <p className="text-white/80">with {selectedSession.instructor_name}</p>
                    <div className="flex items-center gap-4 mt-4 text-sm">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        {new Date(selectedSession.date).toLocaleDateString('en-IN', { 
                          weekday: 'long', day: 'numeric', month: 'short' 
                        })}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {formatTime(selectedSession.start_time)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Class Media Slider - Images and Videos Combined */}
                {((selectedSession.class_images && selectedSession.class_images.length > 0) || 
                  (selectedSession.class_videos && selectedSession.class_videos.length > 0)) && (
                  <div className="bg-white rounded-2xl shadow-lg p-6">
                   
                    
                    {/* Combined Media Array */}
                    {(() => {
                      const images = selectedSession.class_images || [];
                      const videos = selectedSession.class_videos || [];
                      const allMedia = [
                        ...images.map(url => ({ type: 'image', url })),
                        ...videos.map(url => ({ type: 'video', url }))
                      ];
                      
                      if (allMedia.length === 0) return null;
                      
                      const currentMedia = allMedia[mediaIndex];
                      const canGoPrev = mediaIndex > 0;
                      const canGoNext = mediaIndex < allMedia.length - 1;
                      
                      return (
                        <div className="relative">
                          {/* Main Media Display */}
                          <div className={`relative rounded-lg overflow-hidden bg-gray-100 ${
                            currentMedia.type === 'image' ? 'min-h-[500px] max-h-[600px]' : 'aspect-video'
                          }`}>
                            {currentMedia.type === 'image' ? (
                              <img
                                src={currentMedia.url}
                                alt={`${selectedSession.class_name} media ${mediaIndex + 1}`}
                                className="w-full h-full object-contain"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23ddd" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3EImage%3C/text%3E%3C/svg%3E';
                                }}
                              />
                            ) : (
                              (() => {
                                const videoUrl = currentMedia.url;
                                const isYouTube = videoUrl.includes('youtube.com') || videoUrl.includes('youtu.be');
                                const isVimeo = videoUrl.includes('vimeo.com');
                                
                                if (isYouTube) {
                                  const videoId = videoUrl.includes('youtu.be') 
                                    ? videoUrl.split('/').pop()?.split('?')[0]
                                    : new URL(videoUrl).searchParams.get('v');
                                  return (
                                    <iframe
                                      src={`https://www.youtube.com/embed/${videoId}`}
                                      className="w-full h-full"
                                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                      allowFullScreen
                                    />
                                  );
                                } else if (isVimeo) {
                                  const videoId = videoUrl.split('/').pop()?.split('?')[0];
                                  return (
                                    <iframe
                                      src={`https://player.vimeo.com/video/${videoId}`}
                                      className="w-full h-full"
                                      allow="autoplay; fullscreen; picture-in-picture"
                                      allowFullScreen
                                    />
                                  );
                                } else {
                                  return (
                                    <video
                                      src={videoUrl}
                                      controls
                                      className="w-full h-full"
                                      onError={() => {
                                        console.error('Video load error:', videoUrl);
                                      }}
                                    />
                                  );
                                }
                              })()
                            )}
                            
                            {/* Navigation Arrows */}
                            {allMedia.length > 1 && (
                              <>
                                {/* Left Arrow */}
                                <button
                                  onClick={() => {
                                    if (canGoPrev) {
                                      setMediaIndex(mediaIndex - 1);
                                    }
                                  }}
                                  disabled={!canGoPrev}
                                  className={`absolute left-4 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/90 hover:bg-white shadow-lg transition-all ${
                                    canGoPrev ? 'opacity-100 cursor-pointer' : 'opacity-50 cursor-not-allowed'
                                  }`}
                                  style={{ color: theme.primary_color }}
                                >
                                  <ChevronLeft className="w-6 h-6" />
                                </button>
                                
                                {/* Right Arrow */}
                                <button
                                  onClick={() => {
                                    if (canGoNext) {
                                      setMediaIndex(mediaIndex + 1);
                                    }
                                  }}
                                  disabled={!canGoNext}
                                  className={`absolute right-4 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/90 hover:bg-white shadow-lg transition-all ${
                                    canGoNext ? 'opacity-100 cursor-pointer' : 'opacity-50 cursor-not-allowed'
                                  }`}
                                  style={{ color: theme.primary_color }}
                                >
                                  <ChevronRight className="w-6 h-6" />
                                </button>
                              </>
                            )}
                            
                            {/* Media Indicator */}
                            {allMedia.length > 1 && (
                              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
                                {allMedia.map((_, idx) => (
                                  <button
                                    key={idx}
                                    onClick={() => setMediaIndex(idx)}
                                    className={`h-2 rounded-full transition-all ${
                                      idx === mediaIndex 
                                        ? 'w-8 bg-white' 
                                        : 'w-2 bg-white/50 hover:bg-white/75'
                                    }`}
                                    style={idx === mediaIndex ? { backgroundColor: theme.primary_color } : {}}
                                  />
                                ))}
                              </div>
                            )}
                            
                            {/* Media Type Badge */}
                            <div className="absolute top-4 right-4 px-3 py-1 rounded-full bg-black/50 backdrop-blur-sm text-white text-xs font-medium">
                              {currentMedia.type === 'image' ? (
                                <span className="flex items-center gap-1">
                                  <ImageIcon className="w-3 h-3" />
                                  Image {mediaIndex + 1} of {allMedia.length}
                                </span>
                              ) : (
                                <span className="flex items-center gap-1">
                                  <Video className="w-3 h-3" />
                                  Video {mediaIndex - images.length + 1} of {videos.length}
                                </span>
                              )}
                            </div>
                          </div>
                          
                          {/* Thumbnail Strip (Optional - shows below main media) */}
                          {allMedia.length > 1 && (
                            <div className="mt-4 flex gap-2 overflow-x-auto pb-2">
                              {allMedia.map((media, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => setMediaIndex(idx)}
                                  className={`flex-shrink-0 w-20 h-16 rounded-lg overflow-hidden border-2 transition-all ${
                                    idx === mediaIndex 
                                      ? 'ring-2 ring-offset-2' 
                                      : 'border-gray-200 hover:border-gray-400'
                                  }`}
                                  style={idx === mediaIndex ? { 
                                    borderColor: theme.primary_color,
                                    boxShadow: `0 0 0 2px ${theme.primary_color}40`
                                  } : {}}
                                >
                                  {media.type === 'image' ? (
                                    <img
                                      src={media.url}
                                      alt={`Thumbnail ${idx + 1}`}
                                      className="w-full h-full object-cover"
                                    />
                                  ) : (
                                    <div className="w-full h-full bg-gray-800 flex items-center justify-center">
                                      <Video className="w-6 h-6 text-white" />
                                    </div>
                                  )}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                )}

                {/* Class Details */}
                <div className="bg-white rounded-2xl shadow-lg p-6">
                  <h3 className="font-semibold text-gray-900 mb-4">Class Details</h3>
                  
                  {/* Description */}
                  {selectedSession.class_description && (
                    <div className="mb-4">
                      <p className="text-gray-700 leading-relaxed">{selectedSession.class_description}</p>
                    </div>
                  )}

                  {/* Instructor Info */}
                  <div className="space-y-3 mb-4">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-1">Instructor</h4>
                      <p className="text-gray-700">{selectedSession.instructor_name}</p>
                      {selectedSession.instructor_description && (
                        <p className="text-sm text-gray-600 mt-1">{selectedSession.instructor_description}</p>
                      )}
                      {selectedSession.instructor_instagram_handle && (
                        <a
                          href={`https://instagram.com/${selectedSession.instructor_instagram_handle.replace('@', '')}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-sm mt-2"
                          style={{ color: theme.primary_color }}
                        >
                          <Instagram className="w-4 h-4" />
                          @{selectedSession.instructor_instagram_handle.replace('@', '')}
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Class Info Grid */}
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                    <div>
                      <span className="text-sm text-gray-500 block mb-1">Price</span>
                      <span className="font-semibold text-gray-900">₹{selectedSession.drop_in_price}</span>
                    </div>
                    <div>
                      <span className="text-sm text-gray-500 block mb-1 flex items-center gap-1">
                        <Users className="w-4 h-4" />
                        Capacity
                      </span>
                      <span className="font-semibold text-gray-900">
                        {selectedSession.spots_available} / {selectedSession.max_students} spots
                      </span>
                    </div>
                    {selectedSession.class_duration && (
                      <div>
                        <span className="text-sm text-gray-500 block mb-1 flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          Duration
                        </span>
                        <span className="font-semibold text-gray-900">{selectedSession.class_duration} mins</span>
                      </div>
                    )}
                    <div>
                      <span className="text-sm text-gray-500 block mb-1">Level</span>
                      <span className="font-semibold text-gray-900">{selectedSession.level}</span>
                    </div>
                  </div>
                </div>

                
              </div>

              {/* Right Side - Booking Form */}
              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <form onSubmit={handleSubmitDetails} className="p-6 space-y-4">
                  <h3 className="font-semibold text-gray-900 mb-4">Your Details</h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <User className="w-4 h-4 inline mr-1" /> Full Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Enter your name"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:border-transparent"
                    style={{ '--focus-ring': theme.primary_color } as React.CSSProperties}
                    onFocus={(e) => e.currentTarget.style.boxShadow = `0 0 0 2px ${theme.primary_color}40`}
                    onBlur={(e) => e.currentTarget.style.boxShadow = ''}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Phone className="w-4 h-4 inline mr-1" /> WhatsApp Number *
                  </label>
                  <div className="flex items-center rounded-lg border bg-white overflow-hidden"
                    style={{ borderColor: formErrors.phone ? '#dc2626' : '#d1d5db' }}
                  >
                    <span className="px-3 text-gray-500 select-none text-sm border-r border-gray-200 bg-gray-50">
                      +91
                    </span>
                    <input
                      type="tel"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      required
                      value={formData.phone}
                      onChange={(e) => {
                        const digitsOnly = e.target.value.replace(/\D/g, '').slice(0, 10);
                        setFormData({ ...formData, phone: digitsOnly });
                        if (formErrors.phone && /^\d{10}$/.test(digitsOnly)) {
                          setFormErrors((prev) => ({ ...prev, phone: undefined }));
                        }
                      }}
                      placeholder="98765 43210"
                      className="flex-1 px-3 py-3 border-0 focus:ring-2 focus:border-transparent rounded-r-lg"
                      style={{ '--focus-ring': theme.primary_color } as React.CSSProperties}
                      onFocus={(e) => e.currentTarget.style.boxShadow = `0 0 0 2px ${theme.primary_color}40`}
                      onBlur={(e) => e.currentTarget.style.boxShadow = ''}
                    />
                  </div>
                  {formErrors.phone && (
                    <p className="mt-1 text-xs text-red-600">{formErrors.phone}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Mail className="w-4 h-4 inline mr-1" /> Email (optional)
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => {
                      const value = e.target.value;
                      setFormData({ ...formData, email: value });
                      if (formErrors.email) {
                        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                        if (!value.trim() || emailRegex.test(value.trim())) {
                          setFormErrors((prev) => ({ ...prev, email: undefined }));
                        }
                      }
                    }}
                    placeholder="you@example.com"
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:border-transparent ${
                      formErrors.email ? 'border-red-500' : 'border-gray-300'
                    }`}
                    style={{ '--focus-ring': theme.primary_color } as React.CSSProperties}
                    onFocus={(e) => e.currentTarget.style.boxShadow = `0 0 0 2px ${theme.primary_color}40`}
                    onBlur={(e) => e.currentTarget.style.boxShadow = ''}
                  />
                  {formErrors.email && (
                    <p className="mt-1 text-xs text-red-600">{formErrors.email}</p>
                  )}
                </div>

                  <button
                    type="submit"
                    className="w-full py-3 text-white rounded-lg font-semibold transition-colors mt-6"
                    style={{ backgroundColor: theme.primary_color }}
                    onMouseEnter={(e) => e.currentTarget.style.opacity = '0.9'}
                    onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
                  >
                    Continue to Payment
                  </button>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Payment Step */}
        {bookingStep === 'payment' && selectedSession && (
            <div className="p-8 max-w-lg mx-auto">
            <button
              onClick={() => setBookingStep('details')}
                className="flex items-center gap-2 text-gray-600 mb-6 hover:text-purple-600 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" /> Back
            </button>

            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              <div className="p-6 border-b">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Order Summary</h2>
                
                <div className="bg-gray-50 rounded-xl p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-medium text-gray-900">{selectedSession.class_name}</h4>
                      <p className="text-sm text-gray-500">
                        {new Date(selectedSession.date).toLocaleDateString('en-IN', { 
                          weekday: 'short', day: 'numeric', month: 'short' 
                        })} at {formatTime(selectedSession.start_time)}
                      </p>
                    </div>
                    <span className="font-bold text-gray-900">₹{selectedSession.drop_in_price}</span>
                  </div>
                  
                  <div className="pt-3 border-t border-gray-200 flex justify-between">
                    <span className="font-semibold">Total</span>
                    <span 
                      className="font-bold text-xl"
                      style={{ color: theme.primary_color }}
                    >
                      ₹{selectedSession.drop_in_price}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-6 space-y-4">
                <h3 className="font-semibold text-gray-900">Choose Payment Method</h3>

                <button
                  onClick={handlePayment}
                  disabled={processing}
                  className="w-full flex items-center justify-center gap-3 py-4 text-white rounded-xl font-semibold transition-colors disabled:opacity-50"
                  style={{ backgroundColor: theme.primary_color }}
                  onMouseEnter={(e) => {
                    if (!processing) e.currentTarget.style.opacity = '0.9';
                  }}
                  onMouseLeave={(e) => {
                    if (!processing) e.currentTarget.style.opacity = '1';
                  }}
                >
                  {processing ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      <CreditCard className="w-5 h-5" />
                      Pay ₹{selectedSession.drop_in_price} Online
                    </>
                  )}
                </button>

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-200" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-white text-gray-500">or</span>
                  </div>
                </div>

                <button
                  onClick={handlePayLater}
                  disabled={processing}
                  className="w-full flex items-center justify-center gap-3 py-4 border-2 border-gray-200 text-gray-700 rounded-xl font-semibold transition-colors disabled:opacity-50"
                  onMouseEnter={(e) => {
                    if (!processing) {
                      e.currentTarget.style.borderColor = `${theme.primary_color}80`;
                      e.currentTarget.style.backgroundColor = `${theme.primary_color}15`;
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!processing) {
                      e.currentTarget.style.borderColor = '#e5e7eb';
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  {processing ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      <Wallet className="w-5 h-5" />
                      Pay at Studio
                    </>
                  )}
                </button>

                <p className="text-xs text-center text-gray-500">
                  By booking, you agree to the studio's cancellation policy
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Success Step */}
        {bookingStep === 'success' && selectedSession && (
            <div className="p-8 max-w-lg mx-auto text-center">
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Check className="w-10 h-10 text-green-600" />
              </div>
              
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Booking Confirmed!</h2>
              <p className="text-gray-600 mb-6">
                Your spot has been reserved. See you at the studio!
              </p>

              <div 
                className="rounded-xl p-4 mb-6 text-left"
                style={{ 
                  backgroundColor: `${theme.primary_color}15`
                }}
              >
                <div className="text-sm text-gray-600 mb-1">Booking ID</div>
                <div 
                  className="font-mono font-bold"
                  style={{ color: theme.primary_color }}
                >
                  #{bookingRef || bookingId || 'PENDING'}
                </div>
                
                  <div 
                    className="mt-4 pt-4 border-t"
                    style={{ borderColor: `${theme.primary_color}30` }}
                  >
                  <div className="font-semibold text-gray-900">{selectedSession.class_name}</div>
                  <div className="text-sm text-gray-600">
                    {new Date(selectedSession.date).toLocaleDateString('en-IN', { 
                      weekday: 'long', day: 'numeric', month: 'long' 
                    })}
                  </div>
                  <div className="text-sm text-gray-600">
                    {formatTime(selectedSession.start_time)} - {formatTime(selectedSession.end_time)}
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-sm text-gray-500">
                  A confirmation has been sent to your WhatsApp
                </p>
                
                <button
                  onClick={resetBooking}
                  className="w-full py-3 text-white rounded-lg font-semibold transition-colors"
                  style={{ backgroundColor: theme.primary_color }}
                  onMouseEnter={(e) => e.currentTarget.style.opacity = '0.9'}
                  onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
                >
                  Book Another Class
                </button>
              </div>
            </div>
          </div>
        )}
        </div>
      </section>

      {/* Gallery Section */}
      {studio?.photos && studio.photos.length > 0 && (
        <section className="max-w-7xl mx-auto px-6 pb-24">
          <div className="flex items-center justify-between mb-12">
            <div>
              <h2 className="text-4xl font-black tracking-tight mb-2">The Vibe.</h2>
              <p className="text-gray-500">Take a look inside our creative sanctuary.</p>
          </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 h-[600px]">
            {studio.photos.slice(0, 5).map((photo, idx) => {
              if (idx === 0) {
                return (
                  <div key={idx} className="col-span-2 row-span-2 rounded-[32px] overflow-hidden group relative">
                    <img 
                      src={photo} 
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" 
                      alt={`Studio ${idx + 1}`}
                    />
                    <div className="absolute inset-0 bg-black/20 group-hover:bg-transparent transition-all"></div>
                  </div>
                );
              }
              if (idx === 4) {
                return (
                  <div key={idx} className="col-span-2 h-[280px] rounded-[32px] overflow-hidden group relative">
                    <img 
                      src={photo} 
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" 
                      alt={`Studio ${idx + 1}`}
                    />
                  </div>
                );
              }
              return (
                <div key={idx} className="rounded-[32px] overflow-hidden group relative">
                  <img 
                    src={photo} 
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" 
                    alt={`Studio ${idx + 1}`}
                  />
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Testimonials Section */}
      {studio?.testimonials && studio.testimonials.length > 0 && (
        <section className="bg-gray-100 py-24 px-6 overflow-hidden">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-4xl font-black text-center mb-16 italic">"Where the industry trains."</h2>
            <div className="grid md:grid-cols-3 gap-8">
              {studio.testimonials.slice(0, 3).map((testimonial, idx) => (
                <div key={idx} className="bg-white p-10 rounded-[32px] relative">
                  <div className="text-purple-600 text-6xl font-serif absolute top-4 left-6 opacity-20" style={{ color: theme.primary_color }}>"</div>
                  <p className="text-lg font-medium leading-relaxed relative z-10 mb-8">{testimonial.text}</p>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-pink-400"></div>
                    <div>
                      <p className="font-bold">{testimonial.name}</p>
                      <div className="flex gap-1 mt-1">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <span key={i} className="text-yellow-400">★</span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Map & Contact Section */}
      <section className="max-w-7xl mx-auto px-6 py-24 grid md:grid-cols-12 gap-12 items-center">
        <div className="md:col-span-5">
          <h2 className="text-5xl font-black mb-8 leading-[0.9]">
            Find Us In <br/>The Heart Of <br/>
            <span className="underline" style={{ color: theme.primary_color }}>
              {studio?.city || 'Your City'}.
            </span>
          </h2>
          <div className="space-y-8">
            {studio?.address && (
              <div>
                <h4 className="text-sm font-bold uppercase tracking-widest text-gray-400 mb-2">Location</h4>
                <p className="text-xl font-bold">
                  {studio.address}{studio.city ? `, ${studio.city}` : ''}
                </p>
              </div>
            )}
            {studio?.business_hours_open && studio?.business_hours_close && (
              <div>
                <h4 className="text-sm font-bold uppercase tracking-widest text-gray-400 mb-2">Hours</h4>
                <p className="text-xl font-bold">
                  Mon — Sun: {studio.business_hours_open} — {studio.business_hours_close}
                </p>
              </div>
            )}
            <div className="flex gap-4 pt-4">
              <a 
                href={getMapUrl() ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${studio?.address || ''} ${studio?.city || ''}`)}` : '#'}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-black text-white px-8 py-4 rounded-2xl font-bold flex items-center gap-3 hover:bg-gray-800 transition-colors"
              >
                <MapPin className="w-5 h-5" />
                Directions
              </a>
            </div>
          </div>
        </div>
        <div className="md:col-span-7 h-[500px] bg-gray-200 rounded-[40px] overflow-hidden shadow-2xl relative">
          {getMapUrl() ? (
            <iframe 
              src={getMapUrl()}
              width="100%" 
              height="100%" 
              style={{ border: 0, filter: 'grayscale(1) contrast(1.2)' }} 
              allowFullScreen 
              loading="lazy"
            ></iframe>
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
              Map unavailable
            </div>
          )}
          {studio?.phone && (
            <div 
              className="absolute bottom-6 right-6 p-6 rounded-[24px] max-w-xs backdrop-blur-xl"
              style={{
                background: 'rgba(255, 255, 255, 0.7)',
                border: '1px solid rgba(255, 255, 255, 0.3)'
              }}
            >
              <p className="font-bold text-sm mb-2">Instant Support</p>
              <p className="text-xs text-gray-500 mb-4">Chat with our studio manager for group discounts or event rentals.</p>
              <a 
                href={`https://wa.me/${studio.phone.replace(/[^0-9]/g, '')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-green-500 text-white w-full py-3 rounded-xl flex items-center justify-center gap-2 font-bold hover:bg-green-600 transition-all"
              >
                <MessageCircle className="w-4 h-4" />
                WhatsApp Us
              </a>
            </div>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black text-white py-16 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-12">
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div 
                className="w-10 h-10 bg-white rounded-lg flex items-center justify-center text-black font-bold text-xl"
                style={{
                  background: `linear-gradient(to bottom right, ${theme.primary_color}, ${theme.secondary_color})`
                }}
              >
                {studio?.name?.charAt(0) || 'S'}
              </div>
              <span className="font-bold text-2xl tracking-tighter">{studio?.name || 'Studio'}</span>
            </div>
            <p className="text-gray-400 max-w-xs">Elevating dance culture since 2024.</p>
          </div>
          <div className="flex gap-12">
            <div>
              <h5 className="font-bold mb-4 uppercase text-xs tracking-widest" style={{ color: theme.primary_color }}>Platform</h5>
              <ul className="space-y-2 text-gray-400 font-medium">
                <li><a href="#" className="hover:text-white transition-colors">Booking Policy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Cancellation</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Membership</a></li>
              </ul>
            </div>
            <div>
              <h5 className="font-bold mb-4 uppercase text-xs tracking-widest" style={{ color: theme.primary_color }}>Legal</h5>
              <ul className="space-y-2 text-gray-400 font-medium">
                <li><a href="#" className="hover:text-white transition-colors">Terms of Use</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
              </ul>
            </div>
          </div>
        </div>
        <div className="max-w-7xl mx-auto mt-16 pt-8 border-t border-white/10 flex flex-col md:flex-row justify-between items-center gap-6 text-gray-500 text-sm">
          <p>© {new Date().getFullYear()} {studio?.name || 'Studio'}. All rights reserved.</p>
          <p className="flex items-center gap-2">Powered by <span className="text-white font-bold">Studio OS</span></p>
        </div>
      </footer>

      {error && (
        <div className="fixed bottom-4 right-4 bg-red-100 border border-red-200 text-red-700 px-4 py-3 rounded-lg shadow-lg z-50">
          {error}
        </div>
      )}
    </div>
  );
}
