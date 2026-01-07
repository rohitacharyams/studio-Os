import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Calendar, Clock, User, MapPin, Users, ChevronLeft, ChevronRight,
  Check, AlertCircle, Loader2
} from 'lucide-react';
import api from '../lib/api';

interface ClassSession {
  id: string;
  date: string;
  start_time: string;
  end_time: string;
  class_name: string;
  class_type: string;
  level: string;
  instructor_name: string;
  room_name: string;
  max_capacity: number;
  booked_count: number;
  available_spots: number;
  is_full: boolean;
  drop_in_price: number;
}

interface WeeklySchedule {
  [key: number]: ClassSession[];
}

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const levelColors: Record<string, string> = {
  beginner: 'bg-green-100 text-green-800',
  intermediate: 'bg-yellow-100 text-yellow-800',
  advanced: 'bg-red-100 text-red-800',
};

export default function BookingPage() {
  const navigate = useNavigate();
  const [schedule, setSchedule] = useState<WeeklySchedule>({});
  const [loading, setLoading] = useState(true);
  const [weekStart, setWeekStart] = useState<Date>(() => {
    const today = new Date();
    const day = today.getDay();
    const diff = today.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(today.setDate(diff));
  });
  const [selectedSession, setSelectedSession] = useState<ClassSession | null>(null);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSchedule();
  }, [weekStart]);

  const fetchSchedule = async () => {
    setLoading(true);
    try {
      const response = await api.get('/bookings/schedule/weekly', {
        params: { start_date: weekStart.toISOString().split('T')[0] }
      });
      setSchedule(response.data.schedule);
    } catch (err) {
      console.error('Failed to fetch schedule:', err);
    } finally {
      setLoading(false);
    }
  };

  const navigateWeek = (direction: 'prev' | 'next') => {
    const newDate = new Date(weekStart);
    newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7));
    setWeekStart(newDate);
  };

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const formatDate = (dayIndex: number) => {
    const date = new Date(weekStart);
    date.setDate(date.getDate() + dayIndex);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getAvailabilityColor = (session: ClassSession) => {
    if (session.is_full) return 'bg-red-50 border-red-200';
    if (session.available_spots <= 3) return 'bg-yellow-50 border-yellow-200';
    return 'bg-white border-gray-200';
  };

  const getAvailabilityBadge = (session: ClassSession) => {
    if (session.is_full) {
      return <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full">Full</span>;
    }
    if (session.available_spots <= 3) {
      return <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full">{session.available_spots} left</span>;
    }
    return <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">{session.available_spots} spots</span>;
  };

  const handleBookSession = async (session: ClassSession) => {
    setSelectedSession(session);
  };

  const confirmBooking = async () => {
    if (!selectedSession) return;
    
    setBookingLoading(true);
    setError('');
    
    try {
      // For demo, using first contact. In real app, this would be the logged-in user's contact
      const contactsRes = await api.get('/contacts');
      const contactId = contactsRes.data.contacts[0]?.id;
      
      if (!contactId) {
        setError('No contact found. Please create a contact first.');
        return;
      }

      const response = await api.post('/bookings', {
        session_id: selectedSession.id,
        contact_id: contactId,
        payment_method: 'drop_in'
      });

      if (response.data.booking) {
        setBookingSuccess(true);
        setTimeout(() => {
          setSelectedSession(null);
          setBookingSuccess(false);
          fetchSchedule();
        }, 2000);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Booking failed');
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Book a Class</h1>
        <p className="text-gray-600">Browse our weekly schedule and book your spot</p>
      </div>

      {/* Week Navigation */}
      <div className="flex items-center justify-between mb-6 bg-white rounded-lg p-4 shadow-sm">
        <button
          onClick={() => navigateWeek('prev')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        
        <div className="text-center">
          <h2 className="text-lg font-semibold">
            {weekStart.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
          </h2>
          <p className="text-sm text-gray-500">
            {weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - {' '}
            {new Date(weekStart.getTime() + 6 * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </p>
        </div>

        <button
          onClick={() => navigateWeek('next')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Schedule Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        </div>
      ) : (
        <div className="grid grid-cols-7 gap-4">
          {DAYS.map((day, index) => (
            <div key={day} className="min-h-[400px]">
              {/* Day Header */}
              <div className="bg-purple-600 text-white p-3 rounded-t-lg text-center">
                <div className="font-semibold">{day}</div>
                <div className="text-sm opacity-90">{formatDate(index)}</div>
              </div>

              {/* Sessions */}
              <div className="bg-gray-50 rounded-b-lg p-2 space-y-2 min-h-[350px]">
                {schedule[index]?.length > 0 ? (
                  schedule[index].map((session) => (
                    <div
                      key={session.id}
                      className={`p-3 rounded-lg border cursor-pointer hover:shadow-md transition-all ${getAvailabilityColor(session)}`}
                      onClick={() => handleBookSession(session)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-gray-500">
                          {formatTime(session.start_time)}
                        </span>
                        {getAvailabilityBadge(session)}
                      </div>
                      
                      <h3 className="font-semibold text-sm text-gray-900 mb-1">
                        {session.class_name}
                      </h3>
                      
                      <div className={`inline-block text-xs px-2 py-0.5 rounded-full mb-2 ${levelColors[session.level?.toLowerCase()] || 'bg-gray-100 text-gray-700'}`}>
                        {session.level}
                      </div>
                      
                      <div className="text-xs text-gray-500 space-y-0.5">
                        <div className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {session.instructor_name}
                        </div>
                        {session.room_name && (
                          <div className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {session.room_name}
                          </div>
                        )}
                      </div>
                      
                      <div className="mt-2 text-sm font-semibold text-purple-600">
                        ₹{session.drop_in_price}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-gray-400 text-sm py-8">
                    No classes
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Booking Modal */}
      {selectedSession && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
            {bookingSuccess ? (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Check className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Booking Confirmed!</h3>
                <p className="text-gray-600">You're all set for {selectedSession.class_name}</p>
              </div>
            ) : (
              <>
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-bold text-gray-900">{selectedSession.class_name}</h3>
                  <button
                    onClick={() => setSelectedSession(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-3 mb-6">
                  <div className="flex items-center gap-3 text-gray-600">
                    <Calendar className="w-5 h-5" />
                    <span>{new Date(selectedSession.date).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</span>
                  </div>
                  <div className="flex items-center gap-3 text-gray-600">
                    <Clock className="w-5 h-5" />
                    <span>{formatTime(selectedSession.start_time)} - {formatTime(selectedSession.end_time)}</span>
                  </div>
                  <div className="flex items-center gap-3 text-gray-600">
                    <User className="w-5 h-5" />
                    <span>{selectedSession.instructor_name}</span>
                  </div>
                  <div className="flex items-center gap-3 text-gray-600">
                    <Users className="w-5 h-5" />
                    <span>{selectedSession.available_spots} spots available</span>
                  </div>
                  {selectedSession.room_name && (
                    <div className="flex items-center gap-3 text-gray-600">
                      <MapPin className="w-5 h-5" />
                      <span>{selectedSession.room_name}</span>
                    </div>
                  )}
                </div>

                <div className={`inline-block text-sm px-3 py-1 rounded-full mb-4 ${levelColors[selectedSession.level?.toLowerCase()] || 'bg-gray-100 text-gray-700'}`}>
                  {selectedSession.level} Level
                </div>

                {error && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                    <AlertCircle className="w-5 h-5" />
                    {error}
                  </div>
                )}

                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-gray-600">Drop-in Price</span>
                    <span className="text-2xl font-bold text-gray-900">₹{selectedSession.drop_in_price}</span>
                  </div>

                  {selectedSession.is_full ? (
                    <button
                      className="w-full py-3 bg-yellow-500 text-white rounded-lg font-semibold hover:bg-yellow-600 transition-colors"
                    >
                      Join Waitlist
                    </button>
                  ) : (
                    <button
                      onClick={confirmBooking}
                      disabled={bookingLoading}
                      className="w-full py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      {bookingLoading ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Booking...
                        </>
                      ) : (
                        'Confirm Booking'
                      )}
                    </button>
                  )}

                  <button
                    onClick={() => navigate('/checkout', { state: { session: selectedSession } })}
                    className="w-full mt-2 py-3 border border-purple-600 text-purple-600 rounded-lg font-semibold hover:bg-purple-50 transition-colors"
                  >
                    Pay with Razorpay
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
