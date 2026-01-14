import { useState, useEffect, useMemo, useRef } from 'react';
import { 
  Calendar as CalendarIcon, Clock, User, Users, ChevronLeft, ChevronRight,
  Plus, X, AlertCircle, Loader2, Repeat, Check, Copy, Link, ExternalLink, Trash2, Edit3, Image as ImageIcon, Video, Upload
} from 'lucide-react';
import api from '../lib/api';
import toast from 'react-hot-toast';

interface ClassSession {
  id: string;
  date: string;
  start_time: string;
  end_time: string;
  class_name: string;
  class_type: string;
  level: string;
  instructor_name: string;
  max_capacity: number;
  booked_count: number;
  available_spots: number;
  is_full: boolean;
}

// Removed Instructor interface - no longer needed

interface CreateClassForm {
  name: string;
  dance_style: string;
  level: string;
  duration_minutes: number;
  max_capacity: number;
  price: number;
  instructor_name: string;
  instructor_description: string;
  instructor_instagram_handle: string;
  room: string;
  start_time: string;
  description: string;
  // Recurring options
  is_recurring: boolean;
  recurrence_type: 'daily' | 'weekly' | 'biweekly' | 'monthly';
  recurrence_days: number[]; // 0-6 for Mon-Sun
  recurrence_end_date: string;
  // Single dates (if not recurring)
  session_dates: string[];
  // Media
  images: string[]; // URLs
  videos: string[]; // URLs
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const FULL_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const DANCE_STYLES = [
  'Bharatanatyam', 'Kathak', 'Hip Hop', 'Contemporary', 'Salsa', 
  'Bachata', 'Ballet', 'Jazz', 'Bollywood', 'Folk', 'Other'
];

const LEVELS = ['Beginner', 'Intermediate', 'Advanced', 'All Levels'];

const styleColors: Record<string, string> = {
  'hip hop': 'bg-orange-500',
  'bharatanatyam': 'bg-pink-500',
  'kathak': 'bg-rose-500',
  'contemporary': 'bg-blue-500',
  'salsa': 'bg-red-500',
  'bachata': 'bg-purple-500',
  'ballet': 'bg-pink-400',
  'jazz': 'bg-yellow-500',
  'bollywood': 'bg-amber-500',
  'folk': 'bg-green-500',
};

interface Booking {
  id: string;
  booking_number?: string;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  status: string;
  payment_method?: string;
  razorpay_payment_id?: string;
  razorpay_order_id?: string;
  booked_at: string;
}

interface StudioInfo {
  slug: string;
  name: string;
}

export default function CalendarPage() {
  const [viewMode, setViewMode] = useState<'week' | 'month'>('week');
  const [currentDate, setCurrentDate] = useState(new Date());
  const [sessions, setSessions] = useState<ClassSession[]>([]);
  // Removed instructors state - no longer needed
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedSession, setSelectedSession] = useState<ClassSession | null>(null);
  const [showBookingsModal, setShowBookingsModal] = useState(false);
  const [sessionBookings, setSessionBookings] = useState<Booking[]>([]);
  const [bookingsLoading, setBookingsLoading] = useState(false);
  const [studioInfo, setStudioInfo] = useState<StudioInfo | null>(null);
  
  // Delete session state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [cancellationReason, setCancellationReason] = useState('');
  const [notifyOnDelete, setNotifyOnDelete] = useState(true);
  
  // Edit session state
  const [showEditModal, setShowEditModal] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [notifyOnEdit, setNotifyOnEdit] = useState(true);
  const [editForm, setEditForm] = useState({
    date: '',
    start_time: '',
    max_capacity: 20,
    instructor_name: '',
    room: '',
    notes: ''
  });
  
  const [createForm, setCreateForm] = useState<CreateClassForm>({
    name: '',
    dance_style: '',
    level: 'All Levels',
    duration_minutes: 60,
    max_capacity: 20,
    price: 500,
    instructor_name: '',
    instructor_description: '',
    instructor_instagram_handle: '',
    room: 'Main Studio',
    start_time: '18:00',
    description: '',
    is_recurring: false,
    recurrence_type: 'weekly',
    recurrence_days: [],
    recurrence_end_date: '',
    session_dates: [],
    images: [],
    videos: [],
  });

  // File upload state
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [videoFiles, setVideoFiles] = useState<File[]>([]);
  const [imageUrls, setImageUrls] = useState<string[]>([]);
  const [videoUrls, setVideoUrls] = useState<string[]>([]);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);

  // Calculate week/month dates
  const weekStart = useMemo(() => {
    const date = new Date(currentDate);
    const day = date.getDay();
    const diff = date.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(date.setDate(diff));
  }, [currentDate]);

  const weekEnd = useMemo(() => {
    const date = new Date(weekStart);
    date.setDate(date.getDate() + 6);
    return date;
  }, [weekStart]);

  const monthStart = useMemo(() => {
    return new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
  }, [currentDate]);

  const monthEnd = useMemo(() => {
    return new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
  }, [currentDate]);

  // Generate calendar days for month view
  const calendarDays = useMemo(() => {
    const days: Date[] = [];
    const start = new Date(monthStart);
    // Start from Monday of the week containing the 1st
    const startDay = start.getDay();
    start.setDate(start.getDate() - (startDay === 0 ? 6 : startDay - 1));
    
    // Generate 6 weeks (42 days)
    for (let i = 0; i < 42; i++) {
      days.push(new Date(start));
      start.setDate(start.getDate() + 1);
    }
    return days;
  }, [monthStart]);

  // Generate week days
  const weekDays = useMemo(() => {
    const days: Date[] = [];
    const start = new Date(weekStart);
    for (let i = 0; i < 7; i++) {
      days.push(new Date(start));
      start.setDate(start.getDate() + 1);
    }
    return days;
  }, [weekStart]);

  useEffect(() => {
    fetchData();
  }, [currentDate, viewMode]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const startDate = viewMode === 'week' ? weekStart : monthStart;
      const endDateCalc = viewMode === 'week' ? weekEnd : monthEnd;
      
      const [scheduleRes, studioRes] = await Promise.all([
        api.get('/bookings/schedule/weekly', {
          params: { 
            start_date: startDate.toISOString().split('T')[0],
            end_date: endDateCalc.toISOString().split('T')[0]
          }
        }),
        api.get('/studio')
      ]);
      
      // Flatten schedule into sessions array
      const allSessions: ClassSession[] = [];
      Object.values(scheduleRes.data.schedule).forEach((daySessions: any) => {
        allSessions.push(...daySessions);
      });
      setSessions(allSessions);
      if (studioRes.data.studio) {
        setStudioInfo({
          slug: studioRes.data.studio.slug,
          name: studioRes.data.studio.name
        });
      }
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionBookings = async (sessionId: string) => {
    setBookingsLoading(true);
    try {
      const response = await api.get(`/bookings/session/${sessionId}/bookings`);
      setSessionBookings(response.data.bookings || []);
    } catch (err) {
      console.error('Failed to fetch bookings:', err);
      setSessionBookings([]);
    } finally {
      setBookingsLoading(false);
    }
  };

  const handleViewBookings = () => {
    if (selectedSession) {
      fetchSessionBookings(selectedSession.id);
      setShowBookingsModal(true);
    }
  };

  const copyClassLink = (sessionId?: string) => {
    if (!studioInfo?.slug) {
      toast.error('Studio link not available');
      return;
    }
    const baseUrl = window.location.origin;
    const link = sessionId 
      ? `${baseUrl}/book/${studioInfo.slug}?session=${sessionId}`
      : `${baseUrl}/book/${studioInfo.slug}`;
    navigator.clipboard.writeText(link);
    toast.success('Link copied to clipboard!');
  };

  const navigate = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    if (viewMode === 'week') {
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7));
    } else {
      newDate.setMonth(newDate.getMonth() + (direction === 'next' ? 1 : -1));
    }
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  // Format date as YYYY-MM-DD in local timezone (avoids UTC conversion issues)
  const formatDateToLocal = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const getSessionsForDate = (date: Date) => {
    const dateStr = formatDateToLocal(date);
    return sessions.filter(s => s.date === dateStr);
  };

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const isCurrentMonth = (date: Date) => {
    return date.getMonth() === currentDate.getMonth();
  };

  const getStyleColor = (style: string) => {
    return styleColors[style?.toLowerCase()] || 'bg-gray-500';
  };

  // File upload handlers
  const handleImageFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setImageFiles([...imageFiles, ...newFiles]);
    }
  };

  const handleVideoFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setVideoFiles([...videoFiles, ...newFiles]);
    }
  };

  const removeImageFile = (index: number) => {
    setImageFiles(imageFiles.filter((_, i) => i !== index));
  };

  const removeVideoFile = (index: number) => {
    setVideoFiles(videoFiles.filter((_, i) => i !== index));
  };

  const removeImageUrl = (index: number) => {
    setImageUrls(imageUrls.filter((_, i) => i !== index));
  };

  const removeVideoUrl = (index: number) => {
    setVideoUrls(videoUrls.filter((_, i) => i !== index));
  };

  const addImageUrl = () => {
    const urlInput = document.getElementById('image-url-input') as HTMLInputElement;
    if (urlInput && urlInput.value.trim()) {
      setImageUrls([...imageUrls, urlInput.value.trim()]);
      urlInput.value = '';
    }
  };

  const addVideoUrl = () => {
    const urlInput = document.getElementById('video-url-input') as HTMLInputElement;
    if (urlInput && urlInput.value.trim()) {
      setVideoUrls([...videoUrls, urlInput.value.trim()]);
      urlInput.value = '';
    }
  };

  const handleCreateClass = async () => {
    if (!createForm.name) {
      setError('Class name is required');
      return;
    }

    // Validate dates
    if (!createForm.is_recurring && createForm.session_dates.length === 0) {
      setError('Please add at least one class date');
      return;
    }
    if (createForm.is_recurring && !createForm.recurrence_end_date) {
      setError('Please select an end date for recurring classes');
      return;
    }
    if (createForm.is_recurring && createForm.recurrence_days.length === 0) {
      setError('Please select at least one day for recurring classes');
      return;
    }

    setCreateLoading(true);
    setError('');

    try {
      // Generate dates if recurring
      let sessionDates = createForm.session_dates;
      
      if (createForm.is_recurring) {
        sessionDates = generateRecurringDates(
          createForm.recurrence_type,
          createForm.recurrence_days,
          createForm.recurrence_end_date
        );
      }

      // Prepare FormData for multipart upload
      const formData = new FormData();
      
      // Add all form fields
      formData.append('name', createForm.name);
      formData.append('dance_style', createForm.dance_style);
      formData.append('level', createForm.level);
      formData.append('duration_minutes', createForm.duration_minutes.toString());
      formData.append('max_capacity', createForm.max_capacity.toString());
      formData.append('min_capacity', '3');
      formData.append('price', createForm.price.toString());
      formData.append('instructor_name', createForm.instructor_name);
      formData.append('instructor_description', createForm.instructor_description || '');
      formData.append('instructor_instagram_handle', createForm.instructor_instagram_handle || '');
      formData.append('room', createForm.room);
      formData.append('start_time', createForm.start_time);
      formData.append('description', createForm.description || '');
      formData.append('session_dates', JSON.stringify(sessionDates));

      // Add image files
      imageFiles.forEach((file) => {
        formData.append('image_files', file);
      });

      // Add video files
      videoFiles.forEach((file) => {
        formData.append('video_files', file);
      });

      // Add image URLs (if any)
      const allImageUrls = [...imageUrls];
      if (allImageUrls.length > 0) {
        formData.append('images', JSON.stringify(allImageUrls));
      }

      // Add video URLs (if any)
      const allVideoUrls = [...videoUrls];
      if (allVideoUrls.length > 0) {
        formData.append('videos', JSON.stringify(allVideoUrls));
      }

      await api.post('/studio/classes', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setShowCreateModal(false);
      resetForm();
      fetchData();
      toast.success('Class created successfully!');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create class');
      toast.error(err.response?.data?.error || 'Failed to create class');
    } finally {
      setCreateLoading(false);
    }
  };

  const generateRecurringDates = (
    type: string,
    days: number[],
    endDateStr: string
  ): string[] => {
    const dates: string[] = [];
    const startDate = new Date();
    const endDate = new Date(endDateStr);
    
    let current = new Date(startDate);
    
    while (current <= endDate) {
      const dayOfWeek = current.getDay();
      // Convert Sunday=0 to our Mon=0 format
      const normalizedDay = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
      
      if (type === 'daily') {
        dates.push(current.toISOString().split('T')[0]);
      } else if (type === 'weekly' && days.includes(normalizedDay)) {
        dates.push(current.toISOString().split('T')[0]);
      } else if (type === 'biweekly') {
        const weekNum = Math.floor((current.getTime() - startDate.getTime()) / (7 * 24 * 60 * 60 * 1000));
        if (weekNum % 2 === 0 && days.includes(normalizedDay)) {
          dates.push(current.toISOString().split('T')[0]);
        }
      }
      
      current.setDate(current.getDate() + 1);
    }
    
    return dates;
  };

  const resetForm = () => {
    setCreateForm({
      name: '',
      dance_style: '',
      level: 'All Levels',
      duration_minutes: 60,
      max_capacity: 20,
      price: 500,
      instructor_name: '',
      instructor_description: '',
      instructor_instagram_handle: '',
      room: 'Main Studio',
      start_time: '18:00',
      description: '',
      is_recurring: false,
      recurrence_type: 'weekly',
      recurrence_days: [],
      recurrence_end_date: '',
      session_dates: [],
      images: [],
      videos: [],
    });
    setImageFiles([]);
    setVideoFiles([]);
    setImageUrls([]);
    setVideoUrls([]);
    setError('');
    if (imageInputRef.current) imageInputRef.current.value = '';
    if (videoInputRef.current) videoInputRef.current.value = '';
  };

  const toggleRecurrenceDay = (day: number) => {
    setCreateForm(prev => ({
      ...prev,
      recurrence_days: prev.recurrence_days.includes(day)
        ? prev.recurrence_days.filter(d => d !== day)
        : [...prev.recurrence_days, day]
    }));
  };

  const addSingleDate = (date: string) => {
    if (date && !createForm.session_dates.includes(date)) {
      setCreateForm(prev => ({
        ...prev,
        session_dates: [...prev.session_dates, date].sort()
      }));
    }
  };

  const removeSingleDate = (date: string) => {
    setCreateForm(prev => ({
      ...prev,
      session_dates: prev.session_dates.filter(d => d !== date)
    }));
  };


  // Handle delete session
  const handleDeleteSession = async () => {
    if (!selectedSession) return;
    
    setDeleteLoading(true);
    try {
      await api.delete(`/bookings/sessions/${selectedSession.id}`, {
        data: {
          notify_customers: notifyOnDelete,
          cancellation_reason: cancellationReason
        }
      });
      
      toast.success('Class cancelled successfully');
      setSessions(prev => prev.filter(s => s.id !== selectedSession.id));
      setSelectedSession(null);
      setShowDeleteConfirm(false);
      setCancellationReason('');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to cancel class');
    } finally {
      setDeleteLoading(false);
    }
  };


  // Open edit modal with session data
  const openEditModal = () => {
    if (!selectedSession) return;
    
    // Parse the start_time from the ISO string
    const startTime = new Date(selectedSession.start_time);
    const timeStr = startTime.toTimeString().slice(0, 5); // HH:MM format
    
    setEditForm({
      date: selectedSession.date,
      start_time: timeStr,
      max_capacity: selectedSession.max_capacity,
      instructor_name: '',
      instructor_description: '',
      instructor_instagram_handle: '',
      room: '',
      notes: ''
    });
    setShowEditModal(true);
  };

  // Handle update session
  const handleUpdateSession = async () => {
    if (!selectedSession) return;
    
    setEditLoading(true);
    try {
      const response = await api.put(`/bookings/sessions/${selectedSession.id}`, {
        date: editForm.date,
        start_time: editForm.start_time,
        max_capacity: editForm.max_capacity,
        notify_customers: notifyOnEdit,
        change_notes: editForm.notes
      });
      
      toast.success('Class updated successfully');
      
      // Update the session in the list
      setSessions(prev => prev.map(s => 
        s.id === selectedSession.id 
          ? { ...s, ...response.data.session }
          : s
      ));
      
      setShowEditModal(false);
      setSelectedSession(null);
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to update class');
    } finally {
      setEditLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-3 sm:px-6 py-3 sm:py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 sm:gap-4"><h1 className="text-lg sm:text-2xl font-bold text-gray-900">Calendar</h1>
            
            {/* View Toggle */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('week')}
                className={`px-2 sm:px-3 py-1 sm:py-1.5 text-xs sm:text-sm font-medium rounded-md transition-colors ${
                  viewMode === 'week' ? 'bg-white shadow text-gray-900' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Week
              </button>
              <button
                onClick={() => setViewMode('month')}
                className={`px-2 sm:px-3 py-1 sm:py-1.5 text-xs sm:text-sm font-medium rounded-md transition-colors ${
                  viewMode === 'month' ? 'bg-white shadow text-gray-900' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Month
              </button>
            </div>
          </div>
          
          <div className="flex items-center gap-2 sm:gap-3">{/* Navigation */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('prev')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={goToToday}
                className="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Today
              </button>
              <button
                onClick={() => navigate('next')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
            
            {/* Current Period */}
            <div className="text-lg font-semibold text-gray-900 hidden sm:block min-w-[200px] text-center">
              {viewMode === 'week' ? (
                <>
                  {weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - {' '}
                  {weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                </>
              ) : (
                currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
              )}
            </div>
            
            {/* Create Button */}
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              Create Class
            </button>
          </div>
        </div>
      </div>

      {/* Calendar Content */}
      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        </div>
      ) : viewMode === 'week' ? (
        /* Week View */
        <div className="flex-1 overflow-hidden">
          <div className="h-full flex flex-col">
            {/* Day Headers */}
            <div className="grid grid-cols-7 border-b bg-white">
              {weekDays.map((date, idx) => (
                <div
                  key={idx}
                  className={`p-1 sm:p-3 text-center border-r last:border-r-0 ${
                    isToday(date) ? 'bg-purple-50' : ''
                  }`}
                >
                  <div className="text-[10px] sm:text-xs font-medium text-gray-500 uppercase">{DAYS[idx]}</div>
                  <div className={`text-base sm:text-2xl font-semibold mt-0.5 sm:mt-1 ${
                    isToday(date) ? 'text-purple-600' : 'text-gray-900'
                  }`}>
                    {date.getDate()}
                  </div>
                </div>
              ))}
            </div>
            
            {/* Day Columns */}
            <div className="flex-1 grid grid-cols-7 overflow-auto">
              {weekDays.map((date, idx) => (
                <div
                  key={idx}
                  className={`border-r last:border-r-0 p-1 sm:p-2 min-h-[300px] sm:min-h-[500px] ${
                    isToday(date) ? 'bg-purple-50/30' : 'bg-white'
                  }`}
                >
                  <div className="space-y-1 sm:space-y-2">{getSessionsForDate(date).map(session => (
                      <div
                        key={session.id}
                        onClick={() => setSelectedSession(session)}
                        className={`p-1 sm:p-2 rounded-lg cursor-pointer hover:opacity-90 transition-opacity ${
                          getStyleColor(session.class_type)
                        } text-white`}
                      >
                        <div className="text-[10px] sm:text-xs opacity-90">{formatTime(session.start_time)}
                        </div>
                        <div className="font-medium text-[10px] sm:text-sm truncate">
                          {session.class_name}
                        </div>
                        <div className="text-[10px] sm:text-xs opacity-90 hidden sm:flex items-center gap-1 mt-1">
                          <Users className="w-3 h-3" />
                          {session.booked_count}/{session.max_capacity}
                        </div>
                      </div>
                    ))}
                    {getSessionsForDate(date).length === 0 && (
                      <div className="text-center text-gray-400 text-[10px] sm:text-sm py-2 sm:py-4">
                        No classes
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* Month View */
        <div className="flex-1 overflow-auto p-2 sm:p-4">
          <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
            {/* Month Day Headers */}
            <div className="grid grid-cols-7 border-b">
              {DAYS.map(day => (
                <div key={day} className="p-1 sm:p-3 text-center text-[10px] sm:text-sm font-medium text-gray-500 border-r last:border-r-0">
                  {day}
                </div>
              ))}
            </div>
            
            {/* Month Days Grid */}
            <div className="grid grid-cols-7">
              {calendarDays.map((date, idx) => {
                const daySessions = getSessionsForDate(date);
                return (
                  <div
                    key={idx}
                    className={`min-h-[60px] sm:min-h-[120px] p-1 sm:p-2 border-r border-b last:border-r-0 ${
                      !isCurrentMonth(date) ? 'bg-gray-50 text-gray-400' : ''
                    } ${isToday(date) ? 'bg-purple-50' : ''}`}
                  >
                    <div className={`text-[10px] sm:text-sm font-medium mb-0.5 sm:mb-1 ${
                      isToday(date) ? 'text-purple-600' : ''
                    }`}>
                      {date.getDate()}
                    </div>
                    <div className="space-y-0.5 sm:space-y-1">
                      {daySessions.slice(0, 3).map(session => (
                        <div
                          key={session.id}
                          onClick={() => setSelectedSession(session)}
                          className={`text-[8px] sm:text-xs p-0.5 sm:p-1 rounded cursor-pointer truncate ${
                            getStyleColor(session.class_type)
                          } text-white`}
                        >
                          {session.class_name}
                        </div>
                      ))}
                      {daySessions.length > 3 && (
                        <div className="text-xs text-gray-500 text-center">
                          +{daySessions.length - 3} more
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Session Detail Modal */}
      {selectedSession && !showBookingsModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold text-gray-900">{selectedSession.class_name}</h3>
                <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs text-white ${
                  getStyleColor(selectedSession.class_type)
                }`}>
                  {selectedSession.class_type}
                </span>
              </div>
              <button
                onClick={() => setSelectedSession(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <div className="space-y-3 mb-4">
              <div className="flex items-center gap-3 text-gray-600">
                <CalendarIcon className="w-5 h-5" />
                <span>{new Date(selectedSession.date).toLocaleDateString('en-US', { 
                  weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' 
                })}</span>
              </div>
              <div className="flex items-center gap-3 text-gray-600">
                <Clock className="w-5 h-5" />
                <span>{formatTime(selectedSession.start_time)} - {formatTime(selectedSession.end_time)}</span>
              </div>
              {selectedSession.instructor_name && (
                <div className="flex items-center gap-3 text-gray-600">
                  <User className="w-5 h-5" />
                  <span>{selectedSession.instructor_name}</span>
                </div>
              )}
              <div className="flex items-center gap-3 text-gray-600">
                <Users className="w-5 h-5" />
                <span>{selectedSession.booked_count} / {selectedSession.max_capacity} booked</span>
              </div>
            </div>

            {/* Shareable Link Section */}
            {studioInfo?.slug && (
              <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <Link className="w-4 h-4" />
                    Booking Link
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-xs text-primary-600 bg-white p-2 rounded border truncate">
                    {window.location.origin}/book/{studioInfo.slug}?session={selectedSession.id}
                  </code>
                  <button
                    onClick={() => copyClassLink(selectedSession.id)}
                    className="p-2 bg-primary-600 text-white rounded hover:bg-primary-700"
                    title="Copy link"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  <a
                    href={`${window.location.origin}/book/${studioInfo.slug}?session=${selectedSession.id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 border border-gray-300 rounded hover:bg-gray-50"
                    title="Open link"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            )}
            
            <div className="flex gap-3">
              <button
                onClick={() => setSelectedSession(null)}
                className="flex-1 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Close
              </button>
              <button
                onClick={handleViewBookings}
                className="flex-1 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center justify-center gap-2"
              >
                <Users className="w-4 h-4" />
                View Bookings ({selectedSession.booked_count})
              </button>
            </div>
            
            {/* Action Buttons */}
            <div className="flex gap-3 mt-3">
              <button
                onClick={openEditModal}
                className="flex-1 py-2 border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 flex items-center justify-center gap-2"
              >
                <Edit3 className="w-4 h-4" />
                Edit Class
              </button>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="flex-1 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 flex items-center justify-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Cancel Class
              </button>
            </div>
          </div>
        </div>
      )}



      {/* Edit Session Modal */}
      {showEditModal && selectedSession && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold text-gray-900">Edit Class</h3>
                <p className="text-sm text-gray-500">{selectedSession.class_name}</p>
              </div>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <div className="space-y-4">
              {/* Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                <input
                  type="date"
                  value={editForm.date}
                  onChange={(e) => setEditForm(prev => ({ ...prev, date: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              {/* Time */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                <input
                  type="time"
                  value={editForm.start_time}
                  onChange={(e) => setEditForm(prev => ({ ...prev, start_time: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              {/* Max Capacity */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Capacity</label>
                <input
                  type="number"
                  min="1"
                  value={editForm.max_capacity}
                  onChange={(e) => setEditForm(prev => ({ ...prev, max_capacity: parseInt(e.target.value) || 1 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              {/* Notify Students */}
              {selectedSession.booked_count > 0 && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={notifyOnEdit}
                      onChange={(e) => setNotifyOnEdit(e.target.checked)}
                      className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="text-sm text-gray-700">
                      Notify {selectedSession.booked_count} student(s) about changes
                    </span>
                  </label>
                  
                  {notifyOnEdit && (
                    <div className="mt-2">
                      <textarea
                        value={editForm.notes}
                        onChange={(e) => setEditForm(prev => ({ ...prev, notes: e.target.value }))}
                        placeholder="Add a note about the changes (optional)"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
                        rows={2}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowEditModal(false)}
                className="flex-1 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                disabled={editLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateSession}
                disabled={editLoading}
                className="flex-1 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {editLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && selectedSession && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                <AlertCircle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Cancel Class</h3>
                <p className="text-sm text-gray-500">{selectedSession.class_name}</p>
              </div>
            </div>
            
            <p className="text-gray-600 mb-4">
              Are you sure you want to cancel this class? This action cannot be undone.
              {selectedSession.booked_count > 0 && (
                <span className="block mt-2 text-red-600 font-medium">
                  {selectedSession.booked_count} student(s) have booked this class.
                </span>
              )}
            </p>
            
            {selectedSession.booked_count > 0 && (
              <div className="mb-4">
                <label className="flex items-center gap-2 mb-3">
                  <input
                    type="checkbox"
                    checked={notifyOnDelete}
                    onChange={(e) => setNotifyOnDelete(e.target.checked)}
                    className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm text-gray-700">Notify students via email</span>
                </label>
                
                {notifyOnDelete && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Cancellation reason (optional)
                    </label>
                    <textarea
                      value={cancellationReason}
                      onChange={(e) => setCancellationReason(e.target.value)}
                      placeholder="e.g., Instructor unavailable, Studio maintenance..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
                      rows={2}
                    />
                  </div>
                )}
              </div>
            )}
            
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setCancellationReason('');
                }}
                className="flex-1 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                disabled={deleteLoading}
              >
                Keep Class
              </button>
              <button
                onClick={handleDeleteSession}
                disabled={deleteLoading}
                className="flex-1 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {deleteLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Cancelling...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    Cancel Class
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bookings Modal */}
      {showBookingsModal && selectedSession && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 max-w-lg w-full shadow-2xl max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold text-gray-900">Bookings</h3>
                <p className="text-sm text-gray-500">{selectedSession.class_name} - {new Date(selectedSession.date).toLocaleDateString()}</p>
              </div>
              <button
                onClick={() => { setShowBookingsModal(false); setSessionBookings([]); }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto">
              {bookingsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
                </div>
              ) : sessionBookings.length === 0 ? (
                <div className="text-center py-8">
                  <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No bookings yet for this class</p>
                  <p className="text-sm text-gray-400 mt-1">Share the booking link to get students enrolled!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {sessionBookings.map((booking) => (
                    <div key={booking.id} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{booking.customer_name}</p>
                          <p className="text-sm text-gray-500">{booking.customer_email}</p>
                          {booking.customer_phone && (
                            <p className="text-sm text-gray-500">{booking.customer_phone}</p>
                          )}
                          {booking.booking_number && (
                            <p className="text-xs text-gray-400 mt-1">Booking: {booking.booking_number}</p>
                          )}
                          {booking.razorpay_payment_id && (
                            <div className="mt-2 pt-2 border-t border-gray-200">
                              <p className="text-xs font-medium text-gray-600 mb-1">Payment via Razorpay</p>
                              <p className="text-xs text-gray-500 font-mono">Payment ID: {booking.razorpay_payment_id}</p>
                              {booking.razorpay_order_id && (
                                <p className="text-xs text-gray-500 font-mono">Order ID: {booking.razorpay_order_id}</p>
                              )}
                            </div>
                          )}
                          {booking.payment_method && booking.payment_method !== 'online' && !booking.razorpay_payment_id && (
                            <p className="text-xs text-gray-400 mt-1 capitalize">Payment: {booking.payment_method.replace('_', ' ')}</p>
                          )}
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ml-3 ${
                          booking.status === 'confirmed' ? 'bg-green-100 text-green-700' :
                          booking.status === 'pending' ? 'bg-amber-100 text-amber-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {booking.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-2">
                        Booked {new Date(booking.booked_at).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <div className="mt-4 pt-4 border-t">
              <button
                onClick={() => { setShowBookingsModal(false); setSessionBookings([]); }}
                className="w-full py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Class Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-gray-900">Create New Class</h3>
              <button
                onClick={() => { setShowCreateModal(false); resetForm(); }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                <AlertCircle className="w-5 h-5" />
                {error}
              </div>
            )}

            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Class Name *</label>
                  <input
                    type="text"
                    value={createForm.name}
                    onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="e.g., Hip Hop Beginners"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Dance Style</label>
                  <select
                    value={createForm.dance_style}
                    onChange={(e) => setCreateForm({ ...createForm, dance_style: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="">Select style</option>
                    {DANCE_STYLES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Level</label>
                  <select
                    value={createForm.level}
                    onChange={(e) => setCreateForm({ ...createForm, level: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    {LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Instructor Name *</label>
                  <input
                    type="text"
                    value={createForm.instructor_name}
                    onChange={(e) => setCreateForm({ ...createForm, instructor_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="e.g., Priya Sharma"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Instructor Description</label>
                  <textarea
                    value={createForm.instructor_description}
                    onChange={(e) => setCreateForm({ ...createForm, instructor_description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="Brief description about the instructor..."
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Instagram Handle</label>
                  <div className="flex items-center">
                    <span className="px-3 py-2 border border-r-0 border-gray-300 rounded-l-lg bg-gray-50 text-gray-500">@</span>
                    <input
                      type="text"
                      value={createForm.instructor_instagram_handle}
                      onChange={(e) => setCreateForm({ ...createForm, instructor_instagram_handle: e.target.value.replace('@', '') })}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-r-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="instructor_handle"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                  <input
                    type="time"
                    value={createForm.start_time}
                    onChange={(e) => setCreateForm({ ...createForm, start_time: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Duration (mins)</label>
                  <input
                    type="number"
                    value={createForm.duration_minutes}
                    onChange={(e) => setCreateForm({ ...createForm, duration_minutes: parseInt(e.target.value) || 60 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    min="15"
                    step="15"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Max Capacity</label>
                  <input
                    type="number"
                    value={createForm.max_capacity}
                    onChange={(e) => setCreateForm({ ...createForm, max_capacity: parseInt(e.target.value) || 20 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    min="1"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Price (₹)</label>
                  <input
                    type="number"
                    value={createForm.price}
                    onChange={(e) => setCreateForm({ ...createForm, price: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    min="0"
                  />
                </div>
              </div>

              {/* Images Section */}
              <div className="border-t pt-4">
                <label className="block text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                  <ImageIcon className="w-4 h-4" />
                  Class Images
                </label>
                
                {/* File Upload */}
                <div className="mb-3">
                  <input
                    ref={imageInputRef}
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={handleImageFileSelect}
                    className="hidden"
                    id="image-upload"
                  />
                  <label
                    htmlFor="image-upload"
                    className="flex items-center gap-2 px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-purple-500 hover:bg-purple-50 transition-colors"
                  >
                    <Upload className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-600">Upload Images</span>
                  </label>
                </div>

                {/* URL Input */}
                <div className="flex gap-2 mb-3">
                  <input
                    id="image-url-input"
                    type="url"
                    placeholder="Or paste image URL"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addImageUrl();
                      }
                    }}
                  />
                  <button
                    type="button"
                    onClick={addImageUrl}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                  >
                    Add URL
                  </button>
                </div>

                {/* Image Previews */}
                {(imageFiles.length > 0 || imageUrls.length > 0) && (
                  <div className="grid grid-cols-3 gap-2">
                    {imageFiles.map((file, idx) => (
                      <div key={`file-${idx}`} className="relative group">
                        <img
                          src={URL.createObjectURL(file)}
                          alt={`Preview ${idx + 1}`}
                          className="w-full h-24 object-cover rounded-lg"
                        />
                        <button
                          type="button"
                          onClick={() => removeImageFile(idx)}
                          className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <X className="w-3 h-3" />
                        </button>
                        <p className="text-xs text-gray-500 mt-1 truncate">{file.name}</p>
                      </div>
                    ))}
                    {imageUrls.map((url, idx) => (
                      <div key={`url-${idx}`} className="relative group">
                        <img
                          src={url}
                          alt={`URL ${idx + 1}`}
                          className="w-full h-24 object-cover rounded-lg"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3EImage%3C/text%3E%3C/svg%3E';
                          }}
                        />
                        <button
                          type="button"
                          onClick={() => removeImageUrl(idx)}
                          className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Videos Section */}
              <div className="border-t pt-4">
                <label className="block text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                  <Video className="w-4 h-4" />
                  Class Videos
                </label>
                
                {/* File Upload */}
                <div className="mb-3">
                  <input
                    ref={videoInputRef}
                    type="file"
                    accept="video/*"
                    multiple
                    onChange={handleVideoFileSelect}
                    className="hidden"
                    id="video-upload"
                  />
                  <label
                    htmlFor="video-upload"
                    className="flex items-center gap-2 px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-purple-500 hover:bg-purple-50 transition-colors"
                  >
                    <Upload className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-600">Upload Videos</span>
                  </label>
                </div>

                {/* URL Input */}
                <div className="flex gap-2 mb-3">
                  <input
                    id="video-url-input"
                    type="url"
                    placeholder="Or paste video URL (YouTube, Vimeo, etc.)"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addVideoUrl();
                      }
                    }}
                  />
                  <button
                    type="button"
                    onClick={addVideoUrl}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                  >
                    Add URL
                  </button>
                </div>

                {/* Video Previews */}
                {(videoFiles.length > 0 || videoUrls.length > 0) && (
                  <div className="space-y-2">
                    {videoFiles.map((file, idx) => (
                      <div key={`file-${idx}`} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg group">
                        <Video className="w-4 h-4 text-gray-400" />
                        <span className="flex-1 text-sm text-gray-600 truncate">{file.name}</span>
                        <span className="text-xs text-gray-400">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                        <button
                          type="button"
                          onClick={() => removeVideoFile(idx)}
                          className="p-1 text-red-500 hover:text-red-700 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                    {videoUrls.map((url, idx) => (
                      <div key={`url-${idx}`} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg group">
                        <Video className="w-4 h-4 text-gray-400" />
                        <span className="flex-1 text-sm text-gray-600 truncate">{url}</span>
                        <button
                          type="button"
                          onClick={() => removeVideoUrl(idx)}
                          className="p-1 text-red-500 hover:text-red-700 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Recurring Toggle */}
              <div className="border-t pt-4">
                <div className="flex items-center gap-3 mb-4">
                  <button
                    type="button"
                    onClick={() => setCreateForm({ ...createForm, is_recurring: !createForm.is_recurring })}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      createForm.is_recurring ? 'bg-purple-600' : 'bg-gray-200'
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      createForm.is_recurring ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                  <span className="font-medium text-gray-700 flex items-center gap-2">
                    <Repeat className="w-4 h-4" />
                    Recurring Class
                  </span>
                </div>

                {createForm.is_recurring ? (
                  <div className="space-y-4 pl-4 border-l-2 border-purple-200">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Repeat</label>
                      <select
                        value={createForm.recurrence_type}
                        onChange={(e) => setCreateForm({ ...createForm, recurrence_type: e.target.value as any })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="biweekly">Bi-weekly</option>
                      </select>
                    </div>
                    
                    {createForm.recurrence_type !== 'daily' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">On Days</label>
                        <div className="flex gap-2">
                          {FULL_DAYS.map((day, idx) => (
                            <button
                              key={day}
                              type="button"
                              onClick={() => toggleRecurrenceDay(idx)}
                              className={`w-10 h-10 rounded-full text-sm font-medium transition-colors ${
                                createForm.recurrence_days.includes(idx)
                                  ? 'bg-purple-600 text-white'
                                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                              }`}
                            >
                              {day.charAt(0)}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Until</label>
                      <input
                        type="date"
                        value={createForm.recurrence_end_date}
                        onChange={(e) => setCreateForm({ ...createForm, recurrence_end_date: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        min={new Date().toISOString().split('T')[0]}
                      />
                    </div>
                    
                    {createForm.recurrence_end_date && createForm.recurrence_days.length > 0 && (
                      <div className="p-3 bg-purple-50 rounded-lg">
                        <div className="text-sm text-purple-800">
                          <strong>Preview:</strong> {generateRecurringDates(
                            createForm.recurrence_type,
                            createForm.recurrence_days,
                            createForm.recurrence_end_date
                          ).length} classes will be created
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    <label className="block text-sm font-medium text-gray-700">Select Dates *</label>
                    <div className="flex gap-2">
                      <input
                        type="date"
                        id="single-date"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        min={new Date().toISOString().split('T')[0]}
                        onChange={(e) => {
                          if (e.target.value) {
                            addSingleDate(e.target.value);
                            e.target.value = '';
                          }
                        }}
                      />
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {createForm.session_dates.map(date => (
                        <span
                          key={date}
                          className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm"
                        >
                          {new Date(date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                          <button
                            type="button"
                            onClick={() => removeSingleDate(date)}
                            className="hover:text-purple-600"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </span>
                      ))}
                    </div>
                    {createForm.session_dates.length === 0 && (
                      <p className="text-sm text-gray-500">Click on dates above to add class sessions</p>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={() => { setShowCreateModal(false); resetForm(); }}
                className="flex-1 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateClass}
                disabled={createLoading}
                className="flex-1 py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {createLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Check className="w-5 h-5" />
                    Create Class
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
