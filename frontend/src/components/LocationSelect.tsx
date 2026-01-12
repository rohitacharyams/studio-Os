import { useState, useEffect, useRef } from 'react';
import { MapPin, ChevronDown, Search, Globe, Clock } from 'lucide-react';
import api from '../lib/api';

interface Country {
  code: string;
  name: string;
  phone_code?: string;
  flag?: string;
}

interface State {
  code: string;
  name: string;
}

interface City {
  city: string;
  state: string;
  state_code: string;
  country: string;
  country_code: string;
  display: string;
}

interface Timezone {
  value: string;
  label: string;
  offset: string;
}

interface LocationData {
  country: string;
  country_code: string;
  state: string;
  state_code: string;
  city: string;
  postal_code: string;
  address: string;
  timezone: string;
}

interface LocationSelectProps {
  value: LocationData;
  onChange: (location: LocationData) => void;
  showTimezone?: boolean;
  required?: boolean;
}

export default function LocationSelect({ 
  value, 
  onChange, 
  showTimezone = true,
  required = false 
}: LocationSelectProps) {
  const [countries, setCountries] = useState<Country[]>([]);
  const [states, setStates] = useState<State[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [timezones, setTimezones] = useState<Timezone[]>([]);
  const [citySearch, setCitySearch] = useState('');
  const [cityResults, setCityResults] = useState<City[]>([]);
  const [showCityDropdown, setShowCityDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const cityInputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch countries on mount
  useEffect(() => {
    fetchCountries();
  }, []);

  // Fetch states when country changes
  useEffect(() => {
    if (value.country_code) {
      fetchStates(value.country_code);
      fetchTimezones(value.country_code);
    }
  }, [value.country_code]);

  // Fetch cities when state changes
  useEffect(() => {
    if (value.country_code && value.state_code) {
      fetchCities(value.country_code, value.state_code);
    }
  }, [value.country_code, value.state_code]);

  // Search cities as user types
  useEffect(() => {
    if (citySearch.length >= 2) {
      searchCities(citySearch);
    } else {
      setCityResults([]);
    }
  }, [citySearch]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowCityDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchCountries = async () => {
    try {
      const response = await api.get('/location/countries?popular=true');
      setCountries(response.data.countries);
    } catch (error) {
      // Fallback to basic list
      setCountries([
        { code: 'IN', name: 'India', flag: '🇮🇳' },
        { code: 'US', name: 'United States', flag: '🇺🇸' },
        { code: 'GB', name: 'United Kingdom', flag: '🇬🇧' },
        { code: 'CA', name: 'Canada', flag: '🇨🇦' },
        { code: 'AU', name: 'Australia', flag: '🇦🇺' },
      ]);
    }
  };

  const fetchStates = async (countryCode: string) => {
    try {
      const response = await api.get(`/location/countries/${countryCode}/states`);
      setStates(response.data.states);
    } catch (error) {
      setStates([]);
    }
  };

  const fetchCities = async (countryCode: string, stateCode: string) => {
    try {
      const response = await api.get(`/location/countries/${countryCode}/states/${stateCode}/cities`);
      setCities(response.data.cities);
    } catch (error) {
      setCities([]);
    }
  };

  const fetchTimezones = async (countryCode: string) => {
    try {
      const response = await api.get(`/location/timezones?country=${countryCode}`);
      setTimezones(response.data.timezones);
      
      // Auto-select default timezone if not set
      if (!value.timezone && response.data.timezones.length > 0) {
        const defaultTz = await api.get(`/location/timezones/default?country=${countryCode}&city=${value.city || ''}`);
        onChange({ ...value, timezone: defaultTz.data.timezone });
      }
    } catch (error) {
      setTimezones([]);
    }
  };

  const searchCities = async (query: string) => {
    setLoading(true);
    try {
      const response = await api.get(`/location/cities/search?q=${query}&country=${value.country_code || ''}&limit=8`);
      setCityResults(response.data.cities);
      setShowCityDropdown(true);
    } catch (error) {
      setCityResults([]);
    }
    setLoading(false);
  };

  const handleCountryChange = (code: string) => {
    const country = countries.find(c => c.code === code);
    onChange({
      ...value,
      country_code: code,
      country: country?.name || '',
      state: '',
      state_code: '',
      city: '',
      timezone: ''
    });
  };

  const handleStateChange = (code: string) => {
    const state = states.find(s => s.code === code);
    onChange({
      ...value,
      state_code: code,
      state: state?.name || '',
      city: ''
    });
  };

  const handleCitySelect = (city: City) => {
    onChange({
      ...value,
      city: city.city,
      state: city.state,
      state_code: city.state_code,
      country: city.country,
      country_code: city.country_code
    });
    setCitySearch('');
    setShowCityDropdown(false);
    
    // Fetch timezone for this location
    fetchTimezoneForCity(city.city, city.country_code);
  };

  const fetchTimezoneForCity = async (city: string, countryCode: string) => {
    try {
      const response = await api.get(`/location/timezones/default?country=${countryCode}&city=${city}`);
      if (response.data.timezone) {
        onChange({ ...value, timezone: response.data.timezone, city });
      }
    } catch (error) {
      // Ignore
    }
  };

  return (
    <div className="space-y-4">
      {/* Country Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          <Globe className="w-4 h-4 inline mr-1" />
          Country {required && <span className="text-red-500">*</span>}
        </label>
        <div className="relative">
          <select
            value={value.country_code}
            onChange={(e) => handleCountryChange(e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none bg-white"
            required={required}
          >
            <option value="">Select Country</option>
            {countries.map((country) => (
              <option key={country.code} value={country.code}>
                {country.flag} {country.name}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
        </div>
      </div>

      {/* State Selection (if states available) */}
      {states.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            State/Province {required && <span className="text-red-500">*</span>}
          </label>
          <div className="relative">
            <select
              value={value.state_code}
              onChange={(e) => handleStateChange(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none bg-white"
              required={required}
            >
              <option value="">Select State</option>
              {states.map((state) => (
                <option key={state.code} value={state.code}>
                  {state.name}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
          </div>
        </div>
      )}

      {/* City Search/Selection */}
      <div className="relative" ref={dropdownRef}>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          <MapPin className="w-4 h-4 inline mr-1" />
          City {required && <span className="text-red-500">*</span>}
        </label>
        
        {/* If cities list available from state selection */}
        {cities.length > 0 ? (
          <div className="relative">
            <select
              value={value.city}
              onChange={(e) => onChange({ ...value, city: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none bg-white"
              required={required}
            >
              <option value="">Select City</option>
              {cities.map((city) => (
                <option key={city} value={city}>
                  {city}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
          </div>
        ) : (
          /* Search input for cities */
          <div className="relative">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                ref={cityInputRef}
                type="text"
                value={value.city || citySearch}
                onChange={(e) => {
                  setCitySearch(e.target.value);
                  if (!e.target.value) {
                    onChange({ ...value, city: '' });
                  }
                }}
                onFocus={() => citySearch.length >= 2 && setShowCityDropdown(true)}
                placeholder="Search for your city..."
                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              {loading && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </div>
            
            {/* City search results dropdown */}
            {showCityDropdown && cityResults.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                {cityResults.map((city, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleCitySelect(city)}
                    className="w-full px-4 py-2.5 text-left hover:bg-purple-50 flex items-center gap-2"
                  >
                    <MapPin className="w-4 h-4 text-gray-400 flex-shrink-0" />
                    <span>{city.display}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Address */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Street Address
        </label>
        <input
          type="text"
          value={value.address}
          onChange={(e) => onChange({ ...value, address: e.target.value })}
          placeholder="123 Main Street, Building Name"
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
      </div>

      {/* Postal Code */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Postal/ZIP Code
        </label>
        <input
          type="text"
          value={value.postal_code}
          onChange={(e) => onChange({ ...value, postal_code: e.target.value })}
          placeholder="560001"
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
      </div>

      {/* Timezone Selection */}
      {showTimezone && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <Clock className="w-4 h-4 inline mr-1" />
            Timezone {required && <span className="text-red-500">*</span>}
          </label>
          <div className="relative">
            <select
              value={value.timezone}
              onChange={(e) => onChange({ ...value, timezone: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none bg-white"
              required={required}
            >
              <option value="">Select Timezone</option>
              {timezones.map((tz) => (
                <option key={tz.value} value={tz.value}>
                  {tz.label}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
          </div>
          {value.timezone && (
            <p className="mt-1 text-sm text-gray-500">
              All class schedules will be displayed in this timezone
            </p>
          )}
        </div>
      )}

      {/* Location Preview */}
      {(value.city || value.country) && (
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">
            <MapPin className="w-4 h-4 inline mr-1" />
            <span className="font-medium">Studio Location:</span>{' '}
            {[value.address, value.city, value.state, value.country]
              .filter(Boolean)
              .join(', ')}
          </p>
          {value.timezone && (
            <p className="text-sm text-gray-500 mt-1">
              <Clock className="w-4 h-4 inline mr-1" />
              Timezone: {value.timezone}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// Simple timezone-only selector
export function TimezoneSelect({ 
  value, 
  onChange, 
  countryCode 
}: { 
  value: string; 
  onChange: (tz: string) => void;
  countryCode?: string;
}) {
  const [timezones, setTimezones] = useState<Timezone[]>([]);

  useEffect(() => {
    fetchTimezones();
  }, [countryCode]);

  const fetchTimezones = async () => {
    try {
      const url = countryCode 
        ? `/location/timezones?country=${countryCode}`
        : '/location/timezones';
      const response = await api.get(url);
      setTimezones(response.data.timezones);
    } catch (error) {
      // Fallback timezones
      setTimezones([
        { value: 'Asia/Kolkata', label: 'India Standard Time (IST) UTC+5:30', offset: '+0530' },
        { value: 'America/New_York', label: 'Eastern Time (ET) UTC-5/-4', offset: '-0500' },
        { value: 'America/Los_Angeles', label: 'Pacific Time (PT) UTC-8/-7', offset: '-0800' },
        { value: 'Europe/London', label: 'British Time (GMT/BST) UTC+0/+1', offset: '+0000' },
        { value: 'Asia/Dubai', label: 'Gulf Standard Time (GST) UTC+4', offset: '+0400' },
      ]);
    }
  };

  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none bg-white"
      >
        <option value="">Select Timezone</option>
        {timezones.map((tz) => (
          <option key={tz.value} value={tz.value}>
            {tz.label}
          </option>
        ))}
      </select>
      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
    </div>
  );
}
