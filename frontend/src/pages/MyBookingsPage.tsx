import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Calendar, Clock, User, Check, X, 
  Loader2
} from 'lucide-react';
import api from '../lib/api';

interface Booking {
  id: string;
  booking_number: string;
  status: string;
  session_date: string;
  session_time: string;
  class_name: string;
  contact_name: string;
  payment_method: string;
  booked_at: string;
  checked_in_at: string | null;
  cancelled_at: string | null;
}

const statusColors: Record<string, string> = {
  CONFIRMED: 'bg-green-100 text-green-800',
  PENDING: 'bg-yellow-100 text-yellow-800',
  CANCELLED: 'bg-red-100 text-red-800',
  ATTENDED: 'bg-blue-100 text-blue-800',
  NO_SHOW: 'bg-gray-100 text-gray-800',
  WAITLIST: 'bg-purple-100 text-purple-800',
};

export default function MyBookingsPage() {
  const navigate = useNavigate();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'upcoming' | 'past' | 'all'>('upcoming');
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  useEffect(() => {
    fetchBookings();
  }, [filter]);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filter === 'upcoming') {
        params.upcoming = true;
      }
      
      const response = await api.get('/bookings', { params });
      setBookings(response.data.bookings || []);
    } catch (err) {
      console.error('Failed to fetch bookings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (bookingId: string) => {
    if (!confirm('Are you sure you want to cancel this booking?')) return;
    
    setCancellingId(bookingId);
    try {
      await api.put(`/bookings/${bookingId}/cancel`, {
        reason: 'Customer requested cancellation'
      });
      fetchBookings();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to cancel booking');
    } finally {
      setCancellingId(null);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatTime = (timeStr: string) => {
    return new Date(timeStr).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const isUpcoming = (dateStr: string) => {
    return new Date(dateStr) >= new Date();
  };

  const canCancel = (booking: Booking) => {
    return booking.status === 'CONFIRMED' && isUpcoming(booking.session_date);
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Bookings</h1>
          <p className="text-gray-600">View and manage your class bookings</p>
        </div>
        <button
          onClick={() => navigate('/booking')}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700"
        >
          Book a Class
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6">
        {(['upcoming', 'past', 'all'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg font-medium capitalize transition-colors ${
              filter === f
                ? 'bg-purple-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-100'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Bookings List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        </div>
      ) : bookings.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl">
          <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No bookings found</h3>
          <p className="text-gray-600 mb-4">You haven't booked any classes yet</p>
          <button
            onClick={() => navigate('/booking')}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700"
          >
            Browse Classes
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {bookings.map((booking) => {
            return (
              <div
                key={booking.id}
                className={`bg-white rounded-xl p-6 shadow-sm border-l-4 ${
                  booking.status === 'CONFIRMED' ? 'border-green-500' :
                  booking.status === 'CANCELLED' ? 'border-red-500' :
                  booking.status === 'ATTENDED' ? 'border-blue-500' :
                  'border-gray-300'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {booking.class_name}
                      </h3>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[booking.status]}`}>
                        {booking.status}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        {formatDate(booking.session_date)}
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        {booking.session_time ? formatTime(booking.session_time) : 'TBD'}
                      </div>
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4" />
                        {booking.contact_name}
                      </div>
                      <div className="text-gray-400">
                        #{booking.booking_number}
                      </div>
                    </div>

                    {booking.checked_in_at && (
                      <div className="mt-2 text-sm text-green-600 flex items-center gap-1">
                        <Check className="w-4 h-4" />
                        Checked in at {formatTime(booking.checked_in_at)}
                      </div>
                    )}

                    {booking.cancelled_at && (
                      <div className="mt-2 text-sm text-red-600 flex items-center gap-1">
                        <X className="w-4 h-4" />
                        Cancelled on {formatDate(booking.cancelled_at)}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {canCancel(booking) && (
                      <button
                        onClick={() => handleCancel(booking.id)}
                        disabled={cancellingId === booking.id}
                        className="px-4 py-2 text-red-600 border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-50 flex items-center gap-2"
                      >
                        {cancellingId === booking.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <X className="w-4 h-4" />
                        )}
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
