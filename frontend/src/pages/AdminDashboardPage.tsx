import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield, LogOut, Building2, Users, Calendar, TrendingUp,
  Activity, ChevronRight, Search, Loader2, RefreshCw,
  Clock, CheckCircle, XCircle, UserPlus, Store, BarChart3,
  Eye, Mail, Phone, MapPin, ExternalLink
} from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'https://studioos-api.azurewebsites.net';

interface Overview {
  total_studios: number;
  active_studios: number;
  new_studios_this_month: number;
  total_users: number;
  total_studio_owners: number;
  total_customers: number;
  total_bookings: number;
  recent_bookings_30d: number;
  total_classes: number;
  total_sessions: number;
  total_contacts: number;
  booking_by_status: Record<string, number>;
}

interface Studio {
  id: string;
  name: string;
  slug: string;
  email: string;
  phone?: string;
  address?: string;
  city?: string;
  created_at: string;
  onboarding_completed: boolean;
  owner?: {
    id: string;
    name: string;
    email: string;
  };
  stats: {
    bookings: number;
    classes: number;
    contacts: number;
  };
}

interface Activity {
  type: string;
  message: string;
  timestamp: string;
  data: any;
}

interface StudioDetails {
  studio: any;
  owner: any;
  staff: any[];
  classes: any[];
  stats: any;
  recent_bookings: any[];
}

export default function AdminDashboardPage() {
  const navigate = useNavigate();
  const [adminUser, setAdminUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [studios, setStudios] = useState<Studio[]>([]);
  const [recentActivity, setRecentActivity] = useState<Activity[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedStudio, setSelectedStudio] = useState<StudioDetails | null>(null);
  const [studioDetailsLoading, setStudioDetailsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'studios' | 'activity'>('overview');

  useEffect(() => {
    // Check admin auth
    const token = localStorage.getItem('admin_token');
    const user = localStorage.getItem('admin_user');
    
    if (!token || !user) {
      navigate('/platform-admin/login');
      return;
    }

    setAdminUser(JSON.parse(user));
    fetchDashboardData();
  }, [navigate]);

  const getAuthHeaders = () => ({
    headers: { Authorization: `Bearer ${localStorage.getItem('admin_token')}` }
  });

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [overviewRes, studiosRes, activityRes] = await Promise.all([
        axios.get(`${API_URL}/api/admin/analytics/overview`, getAuthHeaders()),
        axios.get(`${API_URL}/api/admin/studios?per_page=10`, getAuthHeaders()),
        axios.get(`${API_URL}/api/admin/activity/recent?limit=20`, getAuthHeaders())
      ]);

      setOverview(overviewRes.data.overview);
      setStudios(studiosRes.data.studios);
      setTotalPages(studiosRes.data.pagination?.pages || 1);
      setRecentActivity(activityRes.data.activity);
    } catch (err: any) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        handleLogout();
      }
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStudios = async (page: number = 1, search: string = '') => {
    try {
      const res = await axios.get(`${API_URL}/api/admin/studios`, {
        ...getAuthHeaders(),
        params: { page, per_page: 10, search }
      });
      setStudios(res.data.studios);
      setTotalPages(res.data.pagination?.pages || 1);
      setCurrentPage(page);
    } catch (err) {
      console.error('Failed to fetch studios:', err);
    }
  };

  const fetchStudioDetails = async (studioId: string) => {
    setStudioDetailsLoading(true);
    try {
      const res = await axios.get(`${API_URL}/api/admin/studios/${studioId}`, getAuthHeaders());
      setSelectedStudio(res.data);
    } catch (err) {
      console.error('Failed to fetch studio details:', err);
    } finally {
      setStudioDetailsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    navigate('/platform-admin/login');
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchStudios(1, searchQuery);
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatDateTime = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-600 rounded-xl flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">Platform Admin</h1>
                <p className="text-xs text-slate-400">Studio OS Control Center</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <p className="text-sm text-white">{adminUser?.name}</p>
                <p className="text-xs text-slate-400">{adminUser?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-700 transition-colors"
                title="Logout"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-slate-800/50 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex gap-1">
            {[
              { id: 'overview', label: 'Overview', icon: BarChart3 },
              { id: 'studios', label: 'Studios', icon: Building2 },
              { id: 'activity', label: 'Activity', icon: Activity }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'text-purple-400 border-purple-400'
                    : 'text-slate-400 border-transparent hover:text-white'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && overview && (
          <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                icon={Building2}
                label="Total Studios"
                value={overview.total_studios}
                subtext={`${overview.new_studios_this_month} new this month`}
                color="purple"
              />
              <StatCard
                icon={Users}
                label="Total Users"
                value={overview.total_users}
                subtext={`${overview.total_customers} customers`}
                color="blue"
              />
              <StatCard
                icon={Calendar}
                label="Total Bookings"
                value={overview.total_bookings}
                subtext={`${overview.recent_bookings_30d} in last 30 days`}
                color="green"
              />
              <StatCard
                icon={TrendingUp}
                label="Active Studios"
                value={overview.active_studios}
                subtext="With recent activity"
                color="orange"
              />
            </div>

            {/* Additional Stats */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <p className="text-slate-400 text-sm">Studio Owners</p>
                <p className="text-2xl font-bold text-white mt-1">{overview.total_studio_owners}</p>
              </div>
              <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <p className="text-slate-400 text-sm">Dance Classes</p>
                <p className="text-2xl font-bold text-white mt-1">{overview.total_classes}</p>
              </div>
              <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <p className="text-slate-400 text-sm">Class Sessions</p>
                <p className="text-2xl font-bold text-white mt-1">{overview.total_sessions}</p>
              </div>
              <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <p className="text-slate-400 text-sm">Contacts</p>
                <p className="text-2xl font-bold text-white mt-1">{overview.total_contacts}</p>
              </div>
              <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <p className="text-slate-400 text-sm">Confirmed Bookings</p>
                <p className="text-2xl font-bold text-green-400 mt-1">
                  {overview.booking_by_status?.CONFIRMED || 0}
                </p>
              </div>
            </div>

            {/* Top Studios Quick View */}
            <div className="bg-slate-800 rounded-xl border border-slate-700">
              <div className="p-4 border-b border-slate-700 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">Recent Studios</h2>
                <button
                  onClick={() => setActiveTab('studios')}
                  className="text-sm text-purple-400 hover:text-purple-300 flex items-center gap-1"
                >
                  View all <ChevronRight className="w-4 h-4" />
                </button>
              </div>
              <div className="divide-y divide-slate-700">
                {studios.slice(0, 5).map((studio) => (
                  <div
                    key={studio.id}
                    className="p-4 hover:bg-slate-700/50 cursor-pointer transition-colors"
                    onClick={() => fetchStudioDetails(studio.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-white">{studio.name}</h3>
                        <p className="text-sm text-slate-400">{studio.email}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-slate-300">{studio.stats.bookings} bookings</p>
                        <p className="text-xs text-slate-500">{formatDate(studio.created_at)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Studios Tab */}
        {activeTab === 'studios' && (
          <div className="space-y-6">
            {/* Search */}
            <form onSubmit={handleSearch} className="flex gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search studios by name, email, or slug..."
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Search
              </button>
              <button
                type="button"
                onClick={() => { setSearchQuery(''); fetchStudios(1, ''); }}
                className="p-2.5 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition-colors"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
            </form>

            {/* Studios List */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left p-4 text-sm font-medium text-slate-400">Studio</th>
                      <th className="text-left p-4 text-sm font-medium text-slate-400">Owner</th>
                      <th className="text-left p-4 text-sm font-medium text-slate-400">Stats</th>
                      <th className="text-left p-4 text-sm font-medium text-slate-400">Created</th>
                      <th className="text-left p-4 text-sm font-medium text-slate-400">Status</th>
                      <th className="text-right p-4 text-sm font-medium text-slate-400">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700">
                    {studios.map((studio) => (
                      <tr key={studio.id} className="hover:bg-slate-700/50">
                        <td className="p-4">
                          <div>
                            <p className="font-medium text-white">{studio.name}</p>
                            <p className="text-sm text-slate-400">{studio.email}</p>
                            <p className="text-xs text-purple-400">/{studio.slug}</p>
                          </div>
                        </td>
                        <td className="p-4">
                          {studio.owner ? (
                            <div>
                              <p className="text-sm text-white">{studio.owner.name}</p>
                              <p className="text-xs text-slate-400">{studio.owner.email}</p>
                            </div>
                          ) : (
                            <span className="text-slate-500">-</span>
                          )}
                        </td>
                        <td className="p-4">
                          <div className="flex gap-4 text-sm">
                            <span className="text-slate-300">{studio.stats.bookings} bookings</span>
                            <span className="text-slate-300">{studio.stats.classes} classes</span>
                          </div>
                        </td>
                        <td className="p-4 text-sm text-slate-300">
                          {formatDate(studio.created_at)}
                        </td>
                        <td className="p-4">
                          {studio.onboarding_completed ? (
                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">
                              <CheckCircle className="w-3 h-3" /> Active
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs rounded-full">
                              <Clock className="w-3 h-3" /> Setup
                            </span>
                          )}
                        </td>
                        <td className="p-4 text-right">
                          <button
                            onClick={() => fetchStudioDetails(studio.id)}
                            className="p-2 text-slate-400 hover:text-white hover:bg-slate-600 rounded-lg transition-colors"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="p-4 border-t border-slate-700 flex items-center justify-between">
                  <p className="text-sm text-slate-400">Page {currentPage} of {totalPages}</p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => fetchStudios(currentPage - 1, searchQuery)}
                      disabled={currentPage <= 1}
                      className="px-3 py-1 bg-slate-700 text-white rounded disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => fetchStudios(currentPage + 1, searchQuery)}
                      disabled={currentPage >= totalPages}
                      className="px-3 py-1 bg-slate-700 text-white rounded disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Activity Tab */}
        {activeTab === 'activity' && (
          <div className="bg-slate-800 rounded-xl border border-slate-700">
            <div className="p-4 border-b border-slate-700">
              <h2 className="text-lg font-semibold text-white">Recent Activity</h2>
            </div>
            <div className="divide-y divide-slate-700 max-h-[600px] overflow-y-auto">
              {recentActivity.map((activity, idx) => (
                <div key={idx} className="p-4 flex items-start gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    activity.type === 'new_studio' ? 'bg-purple-500/20 text-purple-400' :
                    activity.type === 'booking' ? 'bg-green-500/20 text-green-400' :
                    'bg-blue-500/20 text-blue-400'
                  }`}>
                    {activity.type === 'new_studio' ? <Store className="w-4 h-4" /> :
                     activity.type === 'booking' ? <Calendar className="w-4 h-4" /> :
                     <UserPlus className="w-4 h-4" />}
                  </div>
                  <div className="flex-1">
                    <p className="text-white">{activity.message}</p>
                    <p className="text-xs text-slate-400 mt-1">{formatDateTime(activity.timestamp)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Studio Details Modal */}
      {selectedStudio && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden border border-slate-700">
            <div className="p-6 border-b border-slate-700 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white">{selectedStudio.studio.name}</h2>
                <p className="text-sm text-purple-400">/{selectedStudio.studio.slug}</p>
              </div>
              <button
                onClick={() => setSelectedStudio(null)}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            
            {studioDetailsLoading ? (
              <div className="p-8 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
              </div>
            ) : (
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)] space-y-6">
                {/* Studio Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-slate-300">
                      <Mail className="w-4 h-4 text-slate-400" />
                      {selectedStudio.studio.email}
                    </div>
                    {selectedStudio.studio.phone && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <Phone className="w-4 h-4 text-slate-400" />
                        {selectedStudio.studio.phone}
                      </div>
                    )}
                    {selectedStudio.studio.address && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <MapPin className="w-4 h-4 text-slate-400" />
                        {selectedStudio.studio.address}
                        {selectedStudio.studio.city && `, ${selectedStudio.studio.city}`}
                      </div>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-400">Created</p>
                    <p className="text-white">{formatDate(selectedStudio.studio.created_at)}</p>
                  </div>
                </div>

                {/* Owner Info */}
                {selectedStudio.owner && (
                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-slate-400 mb-2">Owner</h3>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-white font-medium">{selectedStudio.owner.name}</p>
                        <p className="text-sm text-slate-400">{selectedStudio.owner.email}</p>
                      </div>
                      <div className="text-right text-sm">
                        <p className="text-slate-400">Last login</p>
                        <p className="text-slate-300">
                          {selectedStudio.owner.last_login ? formatDateTime(selectedStudio.owner.last_login) : 'Never'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Stats */}
                <div className="grid grid-cols-4 gap-3">
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-white">{selectedStudio.stats.total_bookings}</p>
                    <p className="text-xs text-slate-400">Bookings</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-green-400">{selectedStudio.stats.confirmed_bookings}</p>
                    <p className="text-xs text-slate-400">Confirmed</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-white">{selectedStudio.stats.total_classes}</p>
                    <p className="text-xs text-slate-400">Classes</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-white">{selectedStudio.stats.total_contacts}</p>
                    <p className="text-xs text-slate-400">Contacts</p>
                  </div>
                </div>

                {/* Recent Bookings */}
                {selectedStudio.recent_bookings.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-slate-400 mb-2">Recent Bookings</h3>
                    <div className="space-y-2">
                      {selectedStudio.recent_bookings.slice(0, 5).map((booking: any) => (
                        <div key={booking.id} className="bg-slate-700/50 rounded-lg p-3 flex items-center justify-between">
                          <div>
                            <p className="text-white">{booking.customer_name}</p>
                            <p className="text-xs text-slate-400">{booking.customer_email}</p>
                          </div>
                          <div className="text-right">
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              booking.status === 'CONFIRMED' ? 'bg-green-500/20 text-green-400' :
                              booking.status === 'CANCELLED' ? 'bg-red-500/20 text-red-400' :
                              'bg-slate-600 text-slate-300'
                            }`}>
                              {booking.status}
                            </span>
                            <p className="text-xs text-slate-400 mt-1">{formatDateTime(booking.booked_at)}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* View Studio Link */}
                <a
                  href={`/book/${selectedStudio.studio.slug}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  View Public Booking Page
                </a>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Stat Card Component
function StatCard({ 
  icon: Icon, 
  label, 
  value, 
  subtext, 
  color 
}: { 
  icon: any; 
  label: string; 
  value: number; 
  subtext: string;
  color: 'purple' | 'blue' | 'green' | 'orange';
}) {
  const colors = {
    purple: 'bg-purple-500/20 text-purple-400',
    blue: 'bg-blue-500/20 text-blue-400',
    green: 'bg-green-500/20 text-green-400',
    orange: 'bg-orange-500/20 text-orange-400'
  };

  return (
    <div className="bg-slate-800 rounded-xl p-4 sm:p-5 border border-slate-700">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colors[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <span className="text-slate-400 text-sm">{label}</span>
      </div>
      <p className="text-2xl sm:text-3xl font-bold text-white">{value.toLocaleString()}</p>
      <p className="text-xs text-slate-500 mt-1">{subtext}</p>
    </div>
  );
}
