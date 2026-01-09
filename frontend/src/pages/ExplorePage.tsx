import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Search, MapPin, Star, Calendar, Clock, Users, 
  ChevronRight, Loader2, LogOut, User, Building2
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import api from '../lib/api';

interface Studio {
  id: number;
  name: string;
  slug: string;
  description?: string;
  address?: string;
  city?: string;
  logo_url?: string;
  rating?: number;
  total_classes?: number;
}

interface UpcomingClass {
  id: number;
  studio_id: number;
  studio_name: string;
  studio_slug: string;
  class_name: string;
  style: string;
  level: string;
  instructor_name: string;
  start_time: string;
  date: string;
  price: number;
  spots_available: number;
}

export default function ExplorePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [studios, setStudios] = useState<Studio[]>([]);
  const [upcomingClasses, setUpcomingClasses] = useState<UpcomingClass[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCity, setSelectedCity] = useState<string>('');

  useEffect(() => {
    fetchStudios();
    fetchUpcomingClasses();
  }, []);

  const fetchStudios = async () => {
    try {
      const response = await api.get('/studio/explore');
      setStudios(response.data.studios || []);
    } catch (err) {
      console.error('Failed to fetch studios:', err);
      // Demo data if API not available
      setStudios([
        {
          id: 1,
          name: 'Rhythm Dance Academy',
          slug: 'rhythm-dance-academy',
          description: 'Premier dance studio offering classes in various styles',
          address: '123 Dance Street',
          city: 'Mumbai',
          rating: 4.8,
          total_classes: 12
        },
        {
          id: 2,
          name: 'Urban Beats Studio',
          slug: 'urban-beats-studio',
          description: 'Hip-hop and contemporary dance classes',
          address: '456 Beat Avenue',
          city: 'Mumbai',
          rating: 4.6,
          total_classes: 8
        }
      ]);
    }
  };

  const fetchUpcomingClasses = async () => {
    try {
      const response = await api.get('/studio/explore/classes');
      setUpcomingClasses(response.data.classes || []);
    } catch (err) {
      console.error('Failed to fetch classes:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const filteredStudios = studios.filter(studio => {
    const matchesSearch = studio.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         studio.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCity = !selectedCity || studio.city === selectedCity;
    return matchesSearch && matchesCity;
  });

  const cities = [...new Set(studios.map(s => s.city).filter(Boolean))];

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatTime = (timeStr: string) => {
    const [hours, minutes] = timeStr.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const hour12 = hour % 12 || 12;
    return `${hour12}:${minutes} ${ampm}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Building2 className="w-8 h-8 text-primary-600" />
              <span className="text-xl font-bold text-gray-900">Studio OS</span>
            </div>
            
            <nav className="flex items-center gap-4">
              <Link 
                to="/explore" 
                className="text-primary-600 font-medium"
              >
                Explore
              </Link>
              <Link 
                to="/my-bookings" 
                className="text-gray-600 hover:text-gray-900"
              >
                My Bookings
              </Link>
              <div className="flex items-center gap-3 ml-4 pl-4 border-l">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-primary-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">{user?.name}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">
            Find Your Perfect Dance Class
          </h1>
          <p className="text-primary-100 text-lg mb-8">
            Discover studios near you and book classes instantly
          </p>
          
          {/* Search Bar */}
          <div className="flex flex-col md:flex-row gap-4 max-w-3xl">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search studios or classes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-white"
              />
            </div>
            {cities.length > 0 && (
              <select
                value={selectedCity}
                onChange={(e) => setSelectedCity(e.target.value)}
                className="px-4 py-3 rounded-lg text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-white"
              >
                <option value="">All Cities</option>
                {cities.map(city => (
                  <option key={city} value={city}>{city}</option>
                ))}
              </select>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upcoming Classes Section */}
        {upcomingClasses.length > 0 && (
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Upcoming Classes</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {upcomingClasses.slice(0, 6).map((cls) => (
                <div
                  key={cls.id}
                  className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">{cls.class_name}</h3>
                      <p className="text-sm text-gray-500">{cls.studio_name}</p>
                    </div>
                    <span className="px-2 py-1 bg-primary-100 text-primary-700 text-xs font-medium rounded">
                      {cls.level}
                    </span>
                  </div>
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Calendar className="w-4 h-4" />
                      <span>{formatDate(cls.date)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Clock className="w-4 h-4" />
                      <span>{formatTime(cls.start_time)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Users className="w-4 h-4" />
                      <span>{cls.spots_available} spots left</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-bold text-gray-900">₹{cls.price}</span>
                    <Link
                      to={`/book/${cls.studio_slug}/${cls.id}`}
                      className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
                    >
                      Book Now
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Studios Section */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              {searchQuery || selectedCity ? 'Search Results' : 'Popular Studios'}
            </h2>
            <span className="text-gray-500">{filteredStudios.length} studios</span>
          </div>

          {filteredStudios.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-xl border border-gray-100">
              <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No studios found</h3>
              <p className="text-gray-500">Try adjusting your search or filters</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredStudios.map((studio) => (
                <Link
                  key={studio.id}
                  to={`/book/${studio.slug}`}
                  className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow group"
                >
                  {/* Studio Image/Logo */}
                  <div className="h-40 bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
                    {studio.logo_url ? (
                      <img 
                        src={studio.logo_url} 
                        alt={studio.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <Building2 className="w-16 h-16 text-primary-400" />
                    )}
                  </div>
                  
                  <div className="p-5">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
                        {studio.name}
                      </h3>
                      {studio.rating && (
                        <div className="flex items-center gap-1 text-amber-500">
                          <Star className="w-4 h-4 fill-current" />
                          <span className="text-sm font-medium">{studio.rating}</span>
                        </div>
                      )}
                    </div>
                    
                    {studio.address && (
                      <div className="flex items-center gap-2 text-sm text-gray-500 mb-3">
                        <MapPin className="w-4 h-4" />
                        <span>{studio.address}{studio.city && `, ${studio.city}`}</span>
                      </div>
                    )}
                    
                    {studio.description && (
                      <p className="text-sm text-gray-600 line-clamp-2 mb-4">
                        {studio.description}
                      </p>
                    )}
                    
                    <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                      {studio.total_classes && (
                        <span className="text-sm text-gray-500">
                          {studio.total_classes} classes available
                        </span>
                      )}
                      <span className="text-primary-600 font-medium text-sm flex items-center gap-1 group-hover:gap-2 transition-all">
                        View Schedule
                        <ChevronRight className="w-4 h-4" />
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
