"""
Location API Routes
===================
Provides endpoints for:
- Country/State/City lookups
- Timezone information
- Location autocomplete
"""

from flask import Blueprint, request, jsonify
from app.services.location import location_service, POPULAR_COUNTRIES

location_bp = Blueprint('location', __name__, url_prefix='/api/location')


@location_bp.route('/countries', methods=['GET'])
def get_countries():
    """
    Get list of countries.
    Query params:
        popular: true to get only popular countries
    """
    popular_only = request.args.get('popular', 'false').lower() == 'true'
    countries = location_service.get_countries(popular_only=popular_only)
    
    return jsonify({
        'countries': countries,
        'total': len(countries)
    })


@location_bp.route('/countries/<country_code>/states', methods=['GET'])
def get_states(country_code):
    """Get states/provinces for a country."""
    states = location_service.get_states_for_country(country_code)
    
    return jsonify({
        'states': states,
        'country_code': country_code,
        'total': len(states)
    })


@location_bp.route('/countries/<country_code>/states/<state_code>/cities', methods=['GET'])
def get_cities(country_code, state_code):
    """Get cities for a state."""
    cities = location_service.get_cities_for_state(country_code, state_code)
    
    return jsonify({
        'cities': cities,
        'state_code': state_code,
        'country_code': country_code,
        'total': len(cities)
    })


@location_bp.route('/cities/search', methods=['GET'])
def search_cities():
    """
    Search cities by name.
    Query params:
        q: search query (required)
        country: country code to filter by (optional)
        limit: max results (default 10)
    """
    query = request.args.get('q', '')
    country_code = request.args.get('country')
    limit = request.args.get('limit', 10, type=int)
    
    if not query or len(query) < 2:
        return jsonify({'cities': [], 'total': 0})
    
    cities = location_service.search_cities(query, country_code, limit)
    
    return jsonify({
        'cities': cities,
        'total': len(cities)
    })


@location_bp.route('/timezones', methods=['GET'])
def get_timezones():
    """
    Get list of timezones.
    Query params:
        country: filter by country code
    """
    country_code = request.args.get('country')
    
    if country_code:
        timezones = location_service.get_timezones_for_country(country_code)
    else:
        timezones = location_service.get_all_timezones()
    
    return jsonify({
        'timezones': timezones,
        'total': len(timezones)
    })


@location_bp.route('/timezones/default', methods=['GET'])
def get_default_timezone():
    """
    Get default timezone for a country.
    Query params:
        country: country code (required)
        city: city name (optional, for better accuracy)
    """
    country_code = request.args.get('country')
    city = request.args.get('city', '')
    
    if not country_code:
        return jsonify({'error': 'country is required'}), 400
    
    if city:
        timezone = location_service.guess_timezone_from_location(city, country_code)
    else:
        timezone = location_service.get_default_timezone_for_country(country_code)
    
    offset = location_service.format_timezone_offset(timezone)
    
    return jsonify({
        'timezone': timezone,
        'offset': offset,
        'country_code': country_code
    })


@location_bp.route('/timezones/validate', methods=['GET'])
def validate_timezone():
    """
    Validate a timezone string.
    Query params:
        tz: timezone string to validate
    """
    tz = request.args.get('tz', '')
    
    if not tz:
        return jsonify({'valid': False, 'error': 'tz is required'}), 400
    
    is_valid = location_service.is_valid_timezone(tz)
    
    response = {'valid': is_valid, 'timezone': tz}
    
    if is_valid:
        response['offset'] = location_service.format_timezone_offset(tz)
        response['current_time'] = location_service.get_current_time_in_timezone(tz).isoformat()
    
    return jsonify(response)


@location_bp.route('/time/convert', methods=['POST'])
def convert_time():
    """
    Convert time between timezones.
    Body:
    {
        "datetime": "2025-01-12T18:00:00",
        "from_timezone": "Asia/Kolkata",
        "to_timezone": "America/New_York"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    required = ['datetime', 'from_timezone', 'to_timezone']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    from datetime import datetime
    
    try:
        dt = datetime.fromisoformat(data['datetime'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid datetime format'}), 400
    
    if not location_service.is_valid_timezone(data['from_timezone']):
        return jsonify({'error': f"Invalid from_timezone: {data['from_timezone']}"}), 400
    
    if not location_service.is_valid_timezone(data['to_timezone']):
        return jsonify({'error': f"Invalid to_timezone: {data['to_timezone']}"}), 400
    
    converted = location_service.convert_to_timezone(
        dt, 
        data['from_timezone'], 
        data['to_timezone']
    )
    
    return jsonify({
        'original': {
            'datetime': data['datetime'],
            'timezone': data['from_timezone']
        },
        'converted': {
            'datetime': converted.isoformat(),
            'timezone': data['to_timezone'],
            'formatted': converted.strftime('%B %d, %Y at %I:%M %p %Z')
        }
    })


@location_bp.route('/current-time', methods=['GET'])
def get_current_time():
    """
    Get current time in a timezone.
    Query params:
        tz: timezone (default: UTC)
    """
    tz = request.args.get('tz', 'UTC')
    
    if not location_service.is_valid_timezone(tz):
        return jsonify({'error': f'Invalid timezone: {tz}'}), 400
    
    current = location_service.get_current_time_in_timezone(tz)
    
    return jsonify({
        'timezone': tz,
        'datetime': current.isoformat(),
        'formatted': current.strftime('%B %d, %Y at %I:%M %p %Z'),
        'offset': location_service.format_timezone_offset(tz)
    })
