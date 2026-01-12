"""
Location and Timezone Services
==============================
Provides utilities for:
- Country/State/City lookups with autocomplete
- Timezone detection from location
- Address formatting and validation
- Coordinate-based timezone lookup

Uses:
- pycountry: ISO country/subdivision data
- timezonefinder: Coordinates to timezone
- zoneinfo: Python's built-in timezone library
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones
from typing import Optional, List, Dict, Any, Tuple
import re

# Comprehensive timezone data by country/region
# Maps country codes to their common timezones
COUNTRY_TIMEZONES = {
    # India
    'IN': ['Asia/Kolkata'],
    
    # United States
    'US': [
        'America/New_York',      # Eastern
        'America/Chicago',       # Central
        'America/Denver',        # Mountain
        'America/Los_Angeles',   # Pacific
        'America/Anchorage',     # Alaska
        'Pacific/Honolulu',      # Hawaii
        'America/Phoenix',       # Arizona (no DST)
    ],
    
    # United Kingdom
    'GB': ['Europe/London'],
    
    # Canada
    'CA': [
        'America/Toronto',       # Eastern
        'America/Vancouver',     # Pacific
        'America/Edmonton',      # Mountain
        'America/Winnipeg',      # Central
        'America/Halifax',       # Atlantic
        'America/St_Johns',      # Newfoundland
    ],
    
    # Australia
    'AU': [
        'Australia/Sydney',      # AEST
        'Australia/Melbourne',
        'Australia/Brisbane',
        'Australia/Perth',       # AWST
        'Australia/Adelaide',    # ACST
        'Australia/Darwin',
    ],
    
    # European countries
    'DE': ['Europe/Berlin'],
    'FR': ['Europe/Paris'],
    'ES': ['Europe/Madrid'],
    'IT': ['Europe/Rome'],
    'NL': ['Europe/Amsterdam'],
    'BE': ['Europe/Brussels'],
    'CH': ['Europe/Zurich'],
    'AT': ['Europe/Vienna'],
    'PL': ['Europe/Warsaw'],
    'CZ': ['Europe/Prague'],
    'SE': ['Europe/Stockholm'],
    'NO': ['Europe/Oslo'],
    'DK': ['Europe/Copenhagen'],
    'FI': ['Europe/Helsinki'],
    'PT': ['Europe/Lisbon'],
    'GR': ['Europe/Athens'],
    'RO': ['Europe/Bucharest'],
    'HU': ['Europe/Budapest'],
    'IE': ['Europe/Dublin'],
    
    # Asian countries
    'JP': ['Asia/Tokyo'],
    'CN': ['Asia/Shanghai'],
    'KR': ['Asia/Seoul'],
    'SG': ['Asia/Singapore'],
    'HK': ['Asia/Hong_Kong'],
    'TW': ['Asia/Taipei'],
    'TH': ['Asia/Bangkok'],
    'MY': ['Asia/Kuala_Lumpur'],
    'ID': ['Asia/Jakarta', 'Asia/Makassar', 'Asia/Jayapura'],
    'PH': ['Asia/Manila'],
    'VN': ['Asia/Ho_Chi_Minh'],
    'BD': ['Asia/Dhaka'],
    'PK': ['Asia/Karachi'],
    'LK': ['Asia/Colombo'],
    'NP': ['Asia/Kathmandu'],
    'AE': ['Asia/Dubai'],
    'SA': ['Asia/Riyadh'],
    'IL': ['Asia/Jerusalem'],
    'TR': ['Europe/Istanbul'],
    
    # Middle East
    'QA': ['Asia/Qatar'],
    'KW': ['Asia/Kuwait'],
    'BH': ['Asia/Bahrain'],
    'OM': ['Asia/Muscat'],
    
    # Africa
    'ZA': ['Africa/Johannesburg'],
    'EG': ['Africa/Cairo'],
    'NG': ['Africa/Lagos'],
    'KE': ['Africa/Nairobi'],
    'MA': ['Africa/Casablanca'],
    'GH': ['Africa/Accra'],
    
    # South America
    'BR': ['America/Sao_Paulo', 'America/Manaus', 'America/Fortaleza'],
    'AR': ['America/Buenos_Aires'],
    'CL': ['America/Santiago'],
    'CO': ['America/Bogota'],
    'PE': ['America/Lima'],
    'MX': ['America/Mexico_City', 'America/Tijuana', 'America/Cancun'],
    
    # New Zealand
    'NZ': ['Pacific/Auckland', 'Pacific/Chatham'],
    
    # Russia
    'RU': [
        'Europe/Moscow',
        'Europe/Kaliningrad',
        'Asia/Yekaterinburg',
        'Asia/Novosibirsk',
        'Asia/Vladivostok',
    ],
}

# Indian states with major cities
INDIAN_STATES = {
    'AN': {'name': 'Andaman and Nicobar Islands', 'cities': ['Port Blair']},
    'AP': {'name': 'Andhra Pradesh', 'cities': ['Visakhapatnam', 'Vijayawada', 'Guntur', 'Tirupati', 'Nellore', 'Rajahmundry']},
    'AR': {'name': 'Arunachal Pradesh', 'cities': ['Itanagar', 'Naharlagun', 'Pasighat']},
    'AS': {'name': 'Assam', 'cities': ['Guwahati', 'Silchar', 'Dibrugarh', 'Jorhat', 'Nagaon']},
    'BR': {'name': 'Bihar', 'cities': ['Patna', 'Gaya', 'Bhagalpur', 'Muzaffarpur', 'Darbhanga']},
    'CH': {'name': 'Chandigarh', 'cities': ['Chandigarh']},
    'CT': {'name': 'Chhattisgarh', 'cities': ['Raipur', 'Bhilai', 'Bilaspur', 'Korba', 'Durg']},
    'DL': {'name': 'Delhi', 'cities': ['New Delhi', 'Delhi']},
    'GA': {'name': 'Goa', 'cities': ['Panaji', 'Margao', 'Vasco da Gama', 'Mapusa']},
    'GJ': {'name': 'Gujarat', 'cities': ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Gandhinagar', 'Bhavnagar']},
    'HR': {'name': 'Haryana', 'cities': ['Faridabad', 'Gurgaon', 'Panipat', 'Ambala', 'Karnal', 'Rohtak']},
    'HP': {'name': 'Himachal Pradesh', 'cities': ['Shimla', 'Manali', 'Dharamshala', 'Kullu', 'Solan']},
    'JK': {'name': 'Jammu and Kashmir', 'cities': ['Srinagar', 'Jammu', 'Anantnag', 'Baramulla']},
    'JH': {'name': 'Jharkhand', 'cities': ['Ranchi', 'Jamshedpur', 'Dhanbad', 'Bokaro', 'Hazaribagh']},
    'KA': {'name': 'Karnataka', 'cities': ['Bangalore', 'Bengaluru', 'Mysore', 'Mangalore', 'Hubli', 'Belgaum', 'Dharwad']},
    'KL': {'name': 'Kerala', 'cities': ['Thiruvananthapuram', 'Kochi', 'Kozhikode', 'Thrissur', 'Kannur', 'Kollam']},
    'LA': {'name': 'Ladakh', 'cities': ['Leh', 'Kargil']},
    'MP': {'name': 'Madhya Pradesh', 'cities': ['Bhopal', 'Indore', 'Jabalpur', 'Gwalior', 'Ujjain', 'Sagar']},
    'MH': {'name': 'Maharashtra', 'cities': ['Mumbai', 'Pune', 'Nagpur', 'Thane', 'Nashik', 'Aurangabad', 'Navi Mumbai']},
    'MN': {'name': 'Manipur', 'cities': ['Imphal', 'Thoubal', 'Bishnupur']},
    'ML': {'name': 'Meghalaya', 'cities': ['Shillong', 'Tura', 'Jowai']},
    'MZ': {'name': 'Mizoram', 'cities': ['Aizawl', 'Lunglei', 'Champhai']},
    'NL': {'name': 'Nagaland', 'cities': ['Kohima', 'Dimapur', 'Mokokchung']},
    'OR': {'name': 'Odisha', 'cities': ['Bhubaneswar', 'Cuttack', 'Rourkela', 'Berhampur', 'Sambalpur']},
    'PY': {'name': 'Puducherry', 'cities': ['Puducherry', 'Karaikal']},
    'PB': {'name': 'Punjab', 'cities': ['Ludhiana', 'Amritsar', 'Jalandhar', 'Patiala', 'Bathinda']},
    'RJ': {'name': 'Rajasthan', 'cities': ['Jaipur', 'Jodhpur', 'Udaipur', 'Kota', 'Ajmer', 'Bikaner']},
    'SK': {'name': 'Sikkim', 'cities': ['Gangtok', 'Namchi', 'Mangan']},
    'TN': {'name': 'Tamil Nadu', 'cities': ['Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli', 'Salem', 'Tirunelveli']},
    'TG': {'name': 'Telangana', 'cities': ['Hyderabad', 'Warangal', 'Nizamabad', 'Karimnagar', 'Khammam']},
    'TR': {'name': 'Tripura', 'cities': ['Agartala', 'Dharmanagar', 'Udaipur']},
    'UP': {'name': 'Uttar Pradesh', 'cities': ['Lucknow', 'Kanpur', 'Varanasi', 'Agra', 'Noida', 'Ghaziabad', 'Allahabad', 'Meerut']},
    'UK': {'name': 'Uttarakhand', 'cities': ['Dehradun', 'Haridwar', 'Rishikesh', 'Nainital', 'Roorkee']},
    'WB': {'name': 'West Bengal', 'cities': ['Kolkata', 'Howrah', 'Durgapur', 'Asansol', 'Siliguri', 'Darjeeling']},
}

# Popular countries list for dropdown
POPULAR_COUNTRIES = [
    {'code': 'IN', 'name': 'India', 'phone_code': '+91', 'flag': '🇮🇳'},
    {'code': 'US', 'name': 'United States', 'phone_code': '+1', 'flag': '🇺🇸'},
    {'code': 'GB', 'name': 'United Kingdom', 'phone_code': '+44', 'flag': '🇬🇧'},
    {'code': 'CA', 'name': 'Canada', 'phone_code': '+1', 'flag': '🇨🇦'},
    {'code': 'AU', 'name': 'Australia', 'phone_code': '+61', 'flag': '🇦🇺'},
    {'code': 'DE', 'name': 'Germany', 'phone_code': '+49', 'flag': '🇩🇪'},
    {'code': 'FR', 'name': 'France', 'phone_code': '+33', 'flag': '🇫🇷'},
    {'code': 'AE', 'name': 'United Arab Emirates', 'phone_code': '+971', 'flag': '🇦🇪'},
    {'code': 'SG', 'name': 'Singapore', 'phone_code': '+65', 'flag': '🇸🇬'},
    {'code': 'JP', 'name': 'Japan', 'phone_code': '+81', 'flag': '🇯🇵'},
    {'code': 'NZ', 'name': 'New Zealand', 'phone_code': '+64', 'flag': '🇳🇿'},
    {'code': 'ZA', 'name': 'South Africa', 'phone_code': '+27', 'flag': '🇿🇦'},
    {'code': 'NL', 'name': 'Netherlands', 'phone_code': '+31', 'flag': '🇳🇱'},
    {'code': 'ES', 'name': 'Spain', 'phone_code': '+34', 'flag': '🇪🇸'},
    {'code': 'IT', 'name': 'Italy', 'phone_code': '+39', 'flag': '🇮🇹'},
    {'code': 'BR', 'name': 'Brazil', 'phone_code': '+55', 'flag': '🇧🇷'},
    {'code': 'MX', 'name': 'Mexico', 'phone_code': '+52', 'flag': '🇲🇽'},
    {'code': 'KR', 'name': 'South Korea', 'phone_code': '+82', 'flag': '🇰🇷'},
    {'code': 'TH', 'name': 'Thailand', 'phone_code': '+66', 'flag': '🇹🇭'},
    {'code': 'MY', 'name': 'Malaysia', 'phone_code': '+60', 'flag': '🇲🇾'},
    {'code': 'ID', 'name': 'Indonesia', 'phone_code': '+62', 'flag': '🇮🇩'},
    {'code': 'PH', 'name': 'Philippines', 'phone_code': '+63', 'flag': '🇵🇭'},
    {'code': 'SA', 'name': 'Saudi Arabia', 'phone_code': '+966', 'flag': '🇸🇦'},
    {'code': 'QA', 'name': 'Qatar', 'phone_code': '+974', 'flag': '🇶🇦'},
    {'code': 'KW', 'name': 'Kuwait', 'phone_code': '+965', 'flag': '🇰🇼'},
]

# All countries (ISO 3166-1)
ALL_COUNTRIES = [
    {'code': 'AF', 'name': 'Afghanistan'},
    {'code': 'AL', 'name': 'Albania'},
    {'code': 'DZ', 'name': 'Algeria'},
    {'code': 'AD', 'name': 'Andorra'},
    {'code': 'AO', 'name': 'Angola'},
    {'code': 'AR', 'name': 'Argentina'},
    {'code': 'AM', 'name': 'Armenia'},
    {'code': 'AU', 'name': 'Australia'},
    {'code': 'AT', 'name': 'Austria'},
    {'code': 'AZ', 'name': 'Azerbaijan'},
    {'code': 'BH', 'name': 'Bahrain'},
    {'code': 'BD', 'name': 'Bangladesh'},
    {'code': 'BY', 'name': 'Belarus'},
    {'code': 'BE', 'name': 'Belgium'},
    {'code': 'BZ', 'name': 'Belize'},
    {'code': 'BJ', 'name': 'Benin'},
    {'code': 'BT', 'name': 'Bhutan'},
    {'code': 'BO', 'name': 'Bolivia'},
    {'code': 'BA', 'name': 'Bosnia and Herzegovina'},
    {'code': 'BW', 'name': 'Botswana'},
    {'code': 'BR', 'name': 'Brazil'},
    {'code': 'BN', 'name': 'Brunei'},
    {'code': 'BG', 'name': 'Bulgaria'},
    {'code': 'KH', 'name': 'Cambodia'},
    {'code': 'CM', 'name': 'Cameroon'},
    {'code': 'CA', 'name': 'Canada'},
    {'code': 'CL', 'name': 'Chile'},
    {'code': 'CN', 'name': 'China'},
    {'code': 'CO', 'name': 'Colombia'},
    {'code': 'CR', 'name': 'Costa Rica'},
    {'code': 'HR', 'name': 'Croatia'},
    {'code': 'CU', 'name': 'Cuba'},
    {'code': 'CY', 'name': 'Cyprus'},
    {'code': 'CZ', 'name': 'Czech Republic'},
    {'code': 'DK', 'name': 'Denmark'},
    {'code': 'DO', 'name': 'Dominican Republic'},
    {'code': 'EC', 'name': 'Ecuador'},
    {'code': 'EG', 'name': 'Egypt'},
    {'code': 'SV', 'name': 'El Salvador'},
    {'code': 'EE', 'name': 'Estonia'},
    {'code': 'ET', 'name': 'Ethiopia'},
    {'code': 'FI', 'name': 'Finland'},
    {'code': 'FR', 'name': 'France'},
    {'code': 'GE', 'name': 'Georgia'},
    {'code': 'DE', 'name': 'Germany'},
    {'code': 'GH', 'name': 'Ghana'},
    {'code': 'GR', 'name': 'Greece'},
    {'code': 'GT', 'name': 'Guatemala'},
    {'code': 'HN', 'name': 'Honduras'},
    {'code': 'HK', 'name': 'Hong Kong'},
    {'code': 'HU', 'name': 'Hungary'},
    {'code': 'IS', 'name': 'Iceland'},
    {'code': 'IN', 'name': 'India'},
    {'code': 'ID', 'name': 'Indonesia'},
    {'code': 'IR', 'name': 'Iran'},
    {'code': 'IQ', 'name': 'Iraq'},
    {'code': 'IE', 'name': 'Ireland'},
    {'code': 'IL', 'name': 'Israel'},
    {'code': 'IT', 'name': 'Italy'},
    {'code': 'JM', 'name': 'Jamaica'},
    {'code': 'JP', 'name': 'Japan'},
    {'code': 'JO', 'name': 'Jordan'},
    {'code': 'KZ', 'name': 'Kazakhstan'},
    {'code': 'KE', 'name': 'Kenya'},
    {'code': 'KW', 'name': 'Kuwait'},
    {'code': 'KG', 'name': 'Kyrgyzstan'},
    {'code': 'LA', 'name': 'Laos'},
    {'code': 'LV', 'name': 'Latvia'},
    {'code': 'LB', 'name': 'Lebanon'},
    {'code': 'LY', 'name': 'Libya'},
    {'code': 'LT', 'name': 'Lithuania'},
    {'code': 'LU', 'name': 'Luxembourg'},
    {'code': 'MO', 'name': 'Macau'},
    {'code': 'MY', 'name': 'Malaysia'},
    {'code': 'MV', 'name': 'Maldives'},
    {'code': 'MT', 'name': 'Malta'},
    {'code': 'MX', 'name': 'Mexico'},
    {'code': 'MD', 'name': 'Moldova'},
    {'code': 'MC', 'name': 'Monaco'},
    {'code': 'MN', 'name': 'Mongolia'},
    {'code': 'ME', 'name': 'Montenegro'},
    {'code': 'MA', 'name': 'Morocco'},
    {'code': 'MZ', 'name': 'Mozambique'},
    {'code': 'MM', 'name': 'Myanmar'},
    {'code': 'NA', 'name': 'Namibia'},
    {'code': 'NP', 'name': 'Nepal'},
    {'code': 'NL', 'name': 'Netherlands'},
    {'code': 'NZ', 'name': 'New Zealand'},
    {'code': 'NI', 'name': 'Nicaragua'},
    {'code': 'NG', 'name': 'Nigeria'},
    {'code': 'NO', 'name': 'Norway'},
    {'code': 'OM', 'name': 'Oman'},
    {'code': 'PK', 'name': 'Pakistan'},
    {'code': 'PA', 'name': 'Panama'},
    {'code': 'PY', 'name': 'Paraguay'},
    {'code': 'PE', 'name': 'Peru'},
    {'code': 'PH', 'name': 'Philippines'},
    {'code': 'PL', 'name': 'Poland'},
    {'code': 'PT', 'name': 'Portugal'},
    {'code': 'PR', 'name': 'Puerto Rico'},
    {'code': 'QA', 'name': 'Qatar'},
    {'code': 'RO', 'name': 'Romania'},
    {'code': 'RU', 'name': 'Russia'},
    {'code': 'RW', 'name': 'Rwanda'},
    {'code': 'SA', 'name': 'Saudi Arabia'},
    {'code': 'SN', 'name': 'Senegal'},
    {'code': 'RS', 'name': 'Serbia'},
    {'code': 'SG', 'name': 'Singapore'},
    {'code': 'SK', 'name': 'Slovakia'},
    {'code': 'SI', 'name': 'Slovenia'},
    {'code': 'ZA', 'name': 'South Africa'},
    {'code': 'KR', 'name': 'South Korea'},
    {'code': 'ES', 'name': 'Spain'},
    {'code': 'LK', 'name': 'Sri Lanka'},
    {'code': 'SE', 'name': 'Sweden'},
    {'code': 'CH', 'name': 'Switzerland'},
    {'code': 'TW', 'name': 'Taiwan'},
    {'code': 'TZ', 'name': 'Tanzania'},
    {'code': 'TH', 'name': 'Thailand'},
    {'code': 'TN', 'name': 'Tunisia'},
    {'code': 'TR', 'name': 'Turkey'},
    {'code': 'UA', 'name': 'Ukraine'},
    {'code': 'AE', 'name': 'United Arab Emirates'},
    {'code': 'GB', 'name': 'United Kingdom'},
    {'code': 'US', 'name': 'United States'},
    {'code': 'UY', 'name': 'Uruguay'},
    {'code': 'UZ', 'name': 'Uzbekistan'},
    {'code': 'VE', 'name': 'Venezuela'},
    {'code': 'VN', 'name': 'Vietnam'},
    {'code': 'YE', 'name': 'Yemen'},
    {'code': 'ZM', 'name': 'Zambia'},
    {'code': 'ZW', 'name': 'Zimbabwe'},
]

# Timezone display names
TIMEZONE_DISPLAY = {
    'Asia/Kolkata': 'India Standard Time (IST) UTC+5:30',
    'America/New_York': 'Eastern Time (ET) UTC-5/-4',
    'America/Chicago': 'Central Time (CT) UTC-6/-5',
    'America/Denver': 'Mountain Time (MT) UTC-7/-6',
    'America/Los_Angeles': 'Pacific Time (PT) UTC-8/-7',
    'America/Anchorage': 'Alaska Time (AKT) UTC-9/-8',
    'Pacific/Honolulu': 'Hawaii Time (HST) UTC-10',
    'Europe/London': 'British Time (GMT/BST) UTC+0/+1',
    'Europe/Paris': 'Central European Time (CET) UTC+1/+2',
    'Europe/Berlin': 'Central European Time (CET) UTC+1/+2',
    'Asia/Dubai': 'Gulf Standard Time (GST) UTC+4',
    'Asia/Singapore': 'Singapore Time (SGT) UTC+8',
    'Asia/Tokyo': 'Japan Standard Time (JST) UTC+9',
    'Asia/Shanghai': 'China Standard Time (CST) UTC+8',
    'Australia/Sydney': 'Australian Eastern Time (AEST) UTC+10/+11',
    'Australia/Perth': 'Australian Western Time (AWST) UTC+8',
    'Pacific/Auckland': 'New Zealand Time (NZST) UTC+12/+13',
    'America/Sao_Paulo': 'Brasilia Time (BRT) UTC-3',
    'Africa/Johannesburg': 'South Africa Time (SAST) UTC+2',
    'Europe/Moscow': 'Moscow Time (MSK) UTC+3',
}


class LocationService:
    """Service for location and timezone operations."""
    
    @staticmethod
    def get_all_timezones() -> List[Dict[str, str]]:
        """Get all available timezones with display names."""
        timezones = []
        
        # Group by region
        regions = {}
        for tz in sorted(available_timezones()):
            if '/' in tz and not tz.startswith('Etc/'):
                region = tz.split('/')[0]
                if region not in regions:
                    regions[region] = []
                
                # Get current offset
                try:
                    now = datetime.now(ZoneInfo(tz))
                    offset = now.strftime('%z')
                    offset_formatted = f"UTC{offset[:3]}:{offset[3:]}"
                    
                    display_name = TIMEZONE_DISPLAY.get(tz, f"{tz.replace('_', ' ')} ({offset_formatted})")
                    
                    regions[region].append({
                        'value': tz,
                        'label': display_name,
                        'offset': offset,
                        'region': region
                    })
                except Exception:
                    pass
        
        # Flatten with region headers
        for region in ['Asia', 'America', 'Europe', 'Australia', 'Pacific', 'Africa']:
            if region in regions:
                timezones.extend(sorted(regions[region], key=lambda x: x['label']))
        
        return timezones
    
    @staticmethod
    def get_timezones_for_country(country_code: str) -> List[Dict[str, str]]:
        """Get timezones for a specific country."""
        tz_list = COUNTRY_TIMEZONES.get(country_code.upper(), [])
        
        result = []
        for tz in tz_list:
            try:
                now = datetime.now(ZoneInfo(tz))
                offset = now.strftime('%z')
                offset_formatted = f"UTC{offset[:3]}:{offset[3:]}"
                
                display_name = TIMEZONE_DISPLAY.get(tz, f"{tz.replace('_', ' ')} ({offset_formatted})")
                
                result.append({
                    'value': tz,
                    'label': display_name,
                    'offset': offset
                })
            except Exception:
                result.append({
                    'value': tz,
                    'label': tz.replace('_', ' '),
                    'offset': ''
                })
        
        return result
    
    @staticmethod
    def get_default_timezone_for_country(country_code: str) -> str:
        """Get the default/primary timezone for a country."""
        tz_list = COUNTRY_TIMEZONES.get(country_code.upper(), [])
        return tz_list[0] if tz_list else 'UTC'
    
    @staticmethod
    def get_countries(popular_only: bool = False) -> List[Dict[str, Any]]:
        """Get list of countries."""
        if popular_only:
            return POPULAR_COUNTRIES
        return ALL_COUNTRIES
    
    @staticmethod
    def get_states_for_country(country_code: str) -> List[Dict[str, str]]:
        """Get states/provinces for a country."""
        if country_code.upper() == 'IN':
            return [
                {'code': code, 'name': data['name']}
                for code, data in sorted(INDIAN_STATES.items(), key=lambda x: x[1]['name'])
            ]
        # Add more countries as needed
        return []
    
    @staticmethod
    def get_cities_for_state(country_code: str, state_code: str) -> List[str]:
        """Get cities for a state."""
        if country_code.upper() == 'IN':
            state_data = INDIAN_STATES.get(state_code.upper())
            if state_data:
                return sorted(state_data.get('cities', []))
        return []
    
    @staticmethod
    def search_cities(query: str, country_code: Optional[str] = None, limit: int = 10) -> List[Dict[str, str]]:
        """Search cities by name."""
        results = []
        query_lower = query.lower()
        
        if country_code and country_code.upper() == 'IN':
            for state_code, state_data in INDIAN_STATES.items():
                for city in state_data['cities']:
                    if query_lower in city.lower():
                        results.append({
                            'city': city,
                            'state': state_data['name'],
                            'state_code': state_code,
                            'country': 'India',
                            'country_code': 'IN',
                            'display': f"{city}, {state_data['name']}, India"
                        })
                        if len(results) >= limit:
                            return results
        elif not country_code:
            # Search all Indian cities if no country specified
            for state_code, state_data in INDIAN_STATES.items():
                for city in state_data['cities']:
                    if query_lower in city.lower():
                        results.append({
                            'city': city,
                            'state': state_data['name'],
                            'state_code': state_code,
                            'country': 'India',
                            'country_code': 'IN',
                            'display': f"{city}, {state_data['name']}, India"
                        })
                        if len(results) >= limit:
                            return results
        
        return results
    
    @staticmethod
    def format_timezone_offset(timezone_str: str) -> str:
        """Get formatted offset for a timezone."""
        try:
            now = datetime.now(ZoneInfo(timezone_str))
            offset = now.strftime('%z')
            return f"UTC{offset[:3]}:{offset[3:]}"
        except Exception:
            return ''
    
    @staticmethod
    def convert_to_timezone(dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """Convert datetime from one timezone to another."""
        try:
            # If datetime is naive, assume it's in from_tz
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo(from_tz))
            else:
                dt = dt.astimezone(ZoneInfo(from_tz))
            
            return dt.astimezone(ZoneInfo(to_tz))
        except Exception:
            return dt
    
    @staticmethod
    def get_current_time_in_timezone(timezone_str: str) -> datetime:
        """Get current time in a specific timezone."""
        try:
            return datetime.now(ZoneInfo(timezone_str))
        except Exception:
            return datetime.now(timezone.utc)
    
    @staticmethod
    def format_time_with_timezone(dt: datetime, timezone_str: str, format_str: str = '%I:%M %p %Z') -> str:
        """Format a datetime in a specific timezone."""
        try:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo('UTC'))
            
            local_dt = dt.astimezone(ZoneInfo(timezone_str))
            return local_dt.strftime(format_str)
        except Exception:
            return dt.strftime(format_str)
    
    @staticmethod
    def is_valid_timezone(timezone_str: str) -> bool:
        """Check if a timezone string is valid."""
        try:
            ZoneInfo(timezone_str)
            return True
        except Exception:
            return False
    
    @staticmethod
    def guess_timezone_from_location(city: str, country_code: str) -> Optional[str]:
        """Guess timezone based on city and country."""
        # Get country timezones
        timezones = COUNTRY_TIMEZONES.get(country_code.upper(), [])
        
        if len(timezones) == 1:
            return timezones[0]
        
        # For countries with multiple timezones, try to match by city
        city_lower = city.lower()
        
        # US city mappings
        if country_code.upper() == 'US':
            eastern_cities = ['new york', 'boston', 'philadelphia', 'miami', 'atlanta', 'washington', 'charlotte']
            central_cities = ['chicago', 'dallas', 'houston', 'austin', 'san antonio', 'nashville', 'new orleans']
            mountain_cities = ['denver', 'phoenix', 'salt lake city', 'albuquerque']
            pacific_cities = ['los angeles', 'san francisco', 'seattle', 'san diego', 'portland', 'las vegas']
            
            for c in eastern_cities:
                if c in city_lower:
                    return 'America/New_York'
            for c in central_cities:
                if c in city_lower:
                    return 'America/Chicago'
            for c in mountain_cities:
                if c in city_lower:
                    return 'America/Denver'
            for c in pacific_cities:
                if c in city_lower:
                    return 'America/Los_Angeles'
        
        # Canada city mappings
        if country_code.upper() == 'CA':
            if any(c in city_lower for c in ['toronto', 'ottawa', 'montreal', 'quebec']):
                return 'America/Toronto'
            if any(c in city_lower for c in ['vancouver', 'victoria']):
                return 'America/Vancouver'
            if any(c in city_lower for c in ['calgary', 'edmonton']):
                return 'America/Edmonton'
        
        # Australia city mappings
        if country_code.upper() == 'AU':
            if any(c in city_lower for c in ['sydney', 'melbourne', 'canberra']):
                return 'Australia/Sydney'
            if 'perth' in city_lower:
                return 'Australia/Perth'
            if 'brisbane' in city_lower:
                return 'Australia/Brisbane'
        
        # Return first timezone as default
        return timezones[0] if timezones else 'UTC'


# Create singleton instance
location_service = LocationService()
