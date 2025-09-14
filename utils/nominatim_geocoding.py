"""
Nominatim Geocoding Module for Coordinate-to-Country Mapping
Uses OpenStreetMap's Nominatim API for accurate reverse geocoding with fallback support

Features:
- Accurate country detection using OSM boundaries
- Rate limiting (1 req/sec max as per Nominatim policy)
- Proper User-Agent headers
- Intelligent caching with TTL
- Country name normalization for GDP lookup compatibility
- Fallback to rectangular bounding box system on failure
- Error handling for network issues and edge cases
"""

import requests
import time
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import hashlib
import re
from collections import Counter
import streamlit as st

class NominatimGeocoder:
    """
    OpenStreetMap Nominatim reverse geocoding with intelligent caching and rate limiting
    """
    
    def __init__(self):
        # Nominatim API endpoint (public instance)
        self.base_url = "https://nominatim.openstreetmap.org/reverse"
        
        # Rate limiting: Nominatim policy allows max 1 request per second
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds
        
        # Cache configuration 
        self.cache = {}
        self.cache_ttl = 86400  # 24 hours in seconds
        self.max_cache_size = 1000  # Maximum cache entries
        
        # User-Agent header (required by Nominatim terms of service)
        self.headers = {
            'User-Agent': 'Ecological-Valuation-Engine/1.0 (ecosystem-services-app; research-tool)'
        }
        
        # Country name normalization mapping to match GDP lookup keys
        self.country_normalization = {
            # Common variations to standardized keys
            'United States': 'united_states',
            'United States of America': 'united_states',
            'USA': 'united_states',
            'US': 'united_states',
            'United Kingdom': 'united_kingdom',
            'UK': 'united_kingdom',
            'Great Britain': 'united_kingdom',
            'England': 'united_kingdom',
            'Scotland': 'united_kingdom',
            'Wales': 'united_kingdom',
            'Northern Ireland': 'united_kingdom',
            'Canada': 'canada',
            'Mexico': 'mexico',
            'Deutschland': 'germany',
            'Germany': 'germany',
            'France': 'france',
            'España': 'spain',
            'Spain': 'spain',
            'Italia': 'italy',
            'Italy': 'italy',
            'Nederland': 'netherlands',
            'Netherlands': 'netherlands',
            'Holland': 'netherlands',
            'België': 'belgium',
            'Belgium': 'belgium',
            'Österreich': 'austria',
            'Austria': 'austria',
            'Switzerland': 'switzerland',
            'Schweiz': 'switzerland',
            'Suisse': 'switzerland',
            'Sverige': 'sweden',
            'Sweden': 'sweden',
            'Norge': 'norway',
            'Norway': 'norway',
            'Danmark': 'denmark',
            'Denmark': 'denmark',
            'Suomi': 'finland',
            'Finland': 'finland',
            'Ireland': 'ireland',
            'Portugal': 'portugal',
            'Ελλάδα': 'greece',
            'Greece': 'greece',
            'Polska': 'poland',
            'Poland': 'poland',
            'Česká republika': 'czech_republic',
            'Czech Republic': 'czech_republic',
            'Czechia': 'czech_republic',
            'Magyarország': 'hungary',
            'Hungary': 'hungary',
            'Slovensko': 'slovakia',
            'Slovakia': 'slovakia',
            'Slovenija': 'slovenia',
            'Slovenia': 'slovenia',
            'Eesti': 'estonia',
            'Estonia': 'estonia',
            'Latvija': 'latvia',
            'Latvia': 'latvia',
            'Lietuva': 'lithuania',
            'Lithuania': 'lithuania',
            'Hrvatska': 'croatia',
            'Croatia': 'croatia',
            'România': 'romania',
            'Romania': 'romania',
            'България': 'bulgaria',
            'Bulgaria': 'bulgaria',
            'Україна': 'ukraine',
            'Ukraine': 'ukraine',
            'Россия': 'russia',
            'Russia': 'russia',
            'Russian Federation': 'russia',
            '日本': 'japan',
            'Japan': 'japan',
            'Australia': 'australia',
            'New Zealand': 'new_zealand',
            '대한민국': 'south_korea',
            'South Korea': 'south_korea',
            'Korea': 'south_korea',
            'Republic of Korea': 'south_korea',
            'Singapore': 'singapore',
            'Hong Kong': 'hong_kong',
            '中国': 'china',
            'China': 'china',
            "People's Republic of China": 'china',
            'भारत': 'india',
            'India': 'india',
            'Indonesia': 'indonesia',
            'ประเทศไทย': 'thailand',
            'Thailand': 'thailand',
            'Malaysia': 'malaysia',
            'Philippines': 'philippines',
            'Việt Nam': 'vietnam',
            'Vietnam': 'vietnam',
            'বাংলাদেশ': 'bangladesh',
            'Bangladesh': 'bangladesh',
            'Pakistan': 'pakistan',
            'Sri Lanka': 'sri_lanka',
            'Myanmar': 'myanmar',
            'Cambodia': 'cambodia',
            'Laos': 'laos',
            'Mongolia': 'mongolia',
            'Brasil': 'brazil',
            'Brazil': 'brazil',
            'Argentina': 'argentina',
            'México': 'mexico',
            'Colombia': 'colombia',
            'Perú': 'peru',
            'Peru': 'peru',
            'Chile': 'chile',
            'Ecuador': 'ecuador',
            'Bolivia': 'bolivia',
            'Paraguay': 'paraguay',
            'Uruguay': 'uruguay',
            'Venezuela': 'venezuela',
            'Guatemala': 'guatemala',
            'Honduras': 'honduras',
            'El Salvador': 'el_salvador',
            'Nicaragua': 'nicaragua',
            'Costa Rica': 'costa_rica',
            'Panamá': 'panama',
            'Panama': 'panama',
            'السعودية': 'saudi_arabia',
            'Saudi Arabia': 'saudi_arabia',
            'الإمارات': 'uae',
            'United Arab Emirates': 'uae',
            'UAE': 'uae',
            'قطر': 'qatar',
            'Qatar': 'qatar',
            'الكويت': 'kuwait',
            'Kuwait': 'kuwait',
            'البحرين': 'bahrain',
            'Bahrain': 'bahrain',
            'عُمان': 'oman',
            'Oman': 'oman',
            'Israel': 'israel',
            'Türkiye': 'turkey',
            'Turkey': 'turkey',
            'مصر': 'egypt',
            'Egypt': 'egypt',
            'المغرب': 'morocco',
            'Morocco': 'morocco',
            'تونس': 'tunisia',
            'Tunisia': 'tunisia',
            'الجزائر': 'algeria',
            'Algeria': 'algeria',
            'الأردن': 'jordan',
            'Jordan': 'jordan',
            'لبنان': 'lebanon',
            'Lebanon': 'lebanon',
            'العراق': 'iraq',
            'Iraq': 'iraq',
            'إيران': 'iran',
            'Iran': 'iran',
            'South Africa': 'south_africa',
            'Nigeria': 'nigeria',
            'Kenya': 'kenya',
            'Ethiopia': 'ethiopia',
            'Ghana': 'ghana',
            'Uganda': 'uganda',
            'Tanzania': 'tanzania',
            'Mozambique': 'mozambique',
            'Madagascar': 'madagascar',
            'Malawi': 'malawi',
            'Zambia': 'zambia',
            'Zimbabwe': 'zimbabwe',
            'Botswana': 'botswana',
            'Namibia': 'namibia',
            'Angola': 'angola',
            'Cameroon': 'cameroon',
            "Côte d'Ivoire": 'ivory_coast',
            'Ivory Coast': 'ivory_coast',
            'Senegal': 'senegal',
            'Burkina Faso': 'burkina_faso',
            'Mali': 'mali',
            'Niger': 'niger',
            'Chad': 'chad',
            'Central African Republic': 'central_african_republic',
            'Democratic Republic of the Congo': 'democratic_republic_congo',
            'DRC': 'democratic_republic_congo',
            'Congo': 'democratic_republic_congo',
            'Rwanda': 'rwanda',
            'Burundi': 'burundi'
        }
    
    def _normalize_country_name(self, country_name: str) -> str:
        """
        Normalize country name to match GDP lookup keys
        
        Args:
            country_name: Raw country name from Nominatim API
            
        Returns:
            Normalized country code for GDP lookup
        """
        if not country_name:
            return 'global_average'
        
        # Try exact match first
        if country_name in self.country_normalization:
            return self.country_normalization[country_name]
        
        # Try case-insensitive match
        for key, value in self.country_normalization.items():
            if key.lower() == country_name.lower():
                return value
        
        # Convert to snake_case as fallback
        normalized = re.sub(r'[^\w\s]', '', country_name.lower())
        normalized = re.sub(r'\s+', '_', normalized.strip())
        
        return normalized if normalized else 'global_average'
    
    def _get_cache_key(self, lat: float, lon: float) -> str:
        """Generate cache key for coordinates with precision rounding"""
        # Round to 3 decimal places (~100m precision) for reasonable cache hit rates
        rounded_lat = round(lat, 3)
        rounded_lon = round(lon, 3)
        cache_string = f"{rounded_lat},{rounded_lon}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cached entry is still valid"""
        return (time.time() - timestamp) < self.cache_ttl
    
    def _cleanup_cache(self):
        """Remove expired entries and maintain size limit"""
        current_time = time.time()
        
        # Remove expired entries
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if not self._is_cache_valid(timestamp)
        ]
        for key in expired_keys:
            del self.cache[key]
        
        # Enforce size limit (remove oldest entries)
        if len(self.cache) > self.max_cache_size:
            # Sort by timestamp and remove oldest entries
            sorted_items = sorted(
                self.cache.items(),
                key=lambda x: x[1][1]  # Sort by timestamp
            )
            entries_to_remove = len(self.cache) - self.max_cache_size
            for key, _ in sorted_items[:entries_to_remove]:
                del self.cache[key]
    
    def _enforce_rate_limit(self):
        """Enforce Nominatim rate limiting (max 1 request per second)"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_country_from_coordinates(self, lat: float, lon: float) -> str:
        """
        Get country code from coordinates using Nominatim API with fallback
        
        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)
            
        Returns:
            Country code string for GDP lookup (fallback: 'global_average')
        """
        # Input validation
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            print(f"⚠️  Invalid coordinates: lat={lat}, lon={lon}")
            return 'global_average'
        
        # Check cache first
        cache_key = self._get_cache_key(lat, lon)
        if cache_key in self.cache:
            country_code, timestamp = self.cache[cache_key]
            if self._is_cache_valid(timestamp):
                return country_code
        
        try:
            # Enforce rate limiting
            self._enforce_rate_limit()
            
            # Prepare API request
            params = {
                'format': 'json',
                'lat': lat,
                'lon': lon,
                'addressdetails': 1,
                'zoom': 3,  # Country-level resolution
                'accept-language': 'en'  # Prefer English responses
            }
            
            # Make API request
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10  # 10 second timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract country from response
                country_name = None
                if 'address' in data:
                    # Try multiple possible country fields
                    address = data['address']
                    country_name = (
                        address.get('country') or
                        address.get('country_code') or
                        address.get('state') or  # For some territories
                        None
                    )
                
                if country_name:
                    # Normalize country name
                    country_code = self._normalize_country_name(country_name)
                    
                    # Cache successful result
                    self.cache[cache_key] = (country_code, time.time())
                    self._cleanup_cache()
                    
                    return country_code
                else:
                    print(f"⚠️  No country found in Nominatim response for {lat}, {lon}")
                    
            elif response.status_code == 429:
                print("⚠️  Nominatim rate limit exceeded, using fallback")
                time.sleep(2)  # Extra delay for rate limit
                
            else:
                print(f"⚠️  Nominatim API error {response.status_code} for {lat}, {lon}")
                
        except requests.exceptions.Timeout:
            print(f"⚠️  Nominatim API timeout for {lat}, {lon}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Nominatim API request failed for {lat}, {lon}: {e}")
        except Exception as e:
            print(f"⚠️  Unexpected error in Nominatim geocoding for {lat}, {lon}: {e}")
        
        # Fallback to rectangular bounding box system
        return self._fallback_get_country(lat, lon)
    
    def _fallback_get_country(self, lat: float, lon: float) -> str:
        """
        Fallback coordinate-to-country mapping using rectangular bounding boxes
        (Original implementation preserved)
        """
        # North America
        if lat >= 14 and -141 <= lon <= -52:
            # Canada (prioritize northern latitudes)
            if lat >= 49 and -141 <= lon <= -52:
                return 'canada'
            # United States (continental)  
            elif lat >= 25 and lat <= 49 and -125 <= lon <= -66:
                return 'united_states'
            # Alaska (US)
            elif lat >= 54 and lat <= 71 and -169 <= lon <= -130:
                return 'united_states'
            # Mexico
            elif lat >= 14 and lat <= 32 and -118 <= lon <= -86:
                return 'mexico'
            # Default to US for overlapping areas
            else:
                return 'united_states'
        
        # Europe
        elif lat >= 35 and -10 <= lon <= 50:
            if lat >= 50 and lat <= 61 and -8 <= lon <= 2:
                return 'united_kingdom' if lon > -3 else 'ireland'
            elif lat >= 47 and lat <= 55 and 6 <= lon <= 15:
                return 'germany'
            elif lat >= 42 and lat <= 51 and -5 <= lon <= 8:
                return 'france'
            elif lat >= 36 and lat <= 44 and -10 <= lon <= 4:
                return 'spain'
            elif lat >= 36 and lat <= 47 and 6 <= lon <= 19:
                return 'italy'
            else:
                return 'germany'  # European average
        
        # Asia-Pacific Developed
        elif lat >= -50 and 110 <= lon <= 180:
            if lat >= 24 and lat <= 46 and 123 <= lon <= 146:
                return 'japan'
            elif lat >= -44 and lat <= -10 and 113 <= lon <= 154:
                return 'australia'
            elif lat >= -47 and lat <= -34 and 166 <= lon <= 179:
                return 'new_zealand'
            elif lat >= 33 and lat <= 39 and 124 <= lon <= 132:
                return 'south_korea'
            elif lat >= 1 and lat <= 2 and 103 <= lon <= 104:
                return 'singapore'
        
        # Asia Emerging  
        elif lat >= -10 and 60 <= lon <= 140:
            if lat >= 18 and lat <= 54 and 73 <= lon <= 135:
                return 'china'
            elif lat >= 8 and lat <= 37 and 68 <= lon <= 97:
                return 'india'
            elif lat >= -11 and lat <= 6 and 95 <= lon <= 141:
                return 'indonesia'
            elif lat >= 5 and lat <= 21 and 97 <= lon <= 106:
                return 'thailand'
            elif lat >= 8 and lat <= 24 and 102 <= lon <= 110:
                return 'vietnam'
            elif lat >= 1 and lat <= 7 and 100 <= lon <= 120:
                return 'malaysia'
            elif lat >= 5 and lat <= 21 and 116 <= lon <= 127:
                return 'philippines'
            else:
                return 'china'  # Default for unmapped Asian areas
        
        # Latin America
        elif lat >= -55 and -120 <= lon <= -30:
            if lat >= -34 and lat <= 5 and -74 <= lon <= -32:
                return 'brazil'
            elif lat >= -55 and lat <= -22 and -74 <= lon <= -53:
                return 'argentina'
            elif lat >= -56 and lat <= -17 and -76 <= lon <= -66:
                return 'chile'
            elif lat >= -4 and lat <= 12 and -79 <= lon <= -67:
                return 'colombia'
            elif lat >= -18 and lat <= 0 and -81 <= lon <= -68:
                return 'peru'
        
        # Sub-Saharan Africa
        elif lat >= -35 and lat <= 15 and -20 <= lon <= 52:
            if lat >= -35 and lat <= -22 and 16 <= lon <= 33:
                return 'south_africa'
            elif lat >= 4 and lat <= 14 and 3 <= lon <= 15:
                return 'nigeria'
            elif lat >= -5 and lat <= 5 and 34 <= lon <= 42:
                return 'kenya'
            elif lat >= 3 and lat <= 15 and 33 <= lon <= 48:
                return 'ethiopia'
        
        # Default to global average
        return 'global_average'

# Create singleton instance for module-level usage
_nominatim_geocoder = NominatimGeocoder()

def get_country_from_coordinates_nominatim(lat: float, lon: float) -> str:
    """
    Module-level function for getting country from coordinates using Nominatim API
    
    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        
    Returns:
        Country code string for GDP lookup
    """
    return _nominatim_geocoder.get_country_from_coordinates(lat, lon)

def clear_geocoding_cache():
    """Clear the geocoding cache (useful for testing)"""
    _nominatim_geocoder.cache.clear()

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics for monitoring"""
    cache = _nominatim_geocoder.cache
    current_time = time.time()
    
    valid_entries = sum(
        1 for _, (_, timestamp) in cache.items()
        if _nominatim_geocoder._is_cache_valid(timestamp)
    )
    
    return {
        'total_entries': len(cache),
        'valid_entries': valid_entries,
        'expired_entries': len(cache) - valid_entries,
        'cache_hit_rate': 'N/A',  # Would need request tracking
        'max_size': _nominatim_geocoder.max_cache_size,
        'ttl_hours': _nominatim_geocoder.cache_ttl / 3600
    }

@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def determine_predominant_country(sample_points: List[Tuple[float, float]]) -> Dict[str, Any]:
    """
    Determine the predominant country across multiple sampling points using majority vote
    with smart optimizations for reduced API calls and improved performance.
    
    Args:
        sample_points: List of (latitude, longitude) tuples to analyze
        
    Returns:
        Dict containing:
        - country: The predominant country code (or "International Waters")
        - count: Number of points in the predominant country
        - total_points: Total number of valid points processed
        - tie_broken: Whether a tie-breaking procedure was used
        - method: Method used for final determination
        
    Features:
    - Deduplicates points by rounding to 4 decimal places (~11m precision)
    - Uses existing geocoding cache to minimize API calls
    - Implements tie-breaking: centroid country → alphabetical order
    - Handles international waters and edge cases
    - Provides progress feedback via Streamlit spinner
    - Comprehensive error handling and logging
    """
    
    # Input validation
    if not sample_points:
        print("⚠️  Empty sample points list provided")
        return {
            'country': 'global_average',
            'count': 0,
            'total_points': 0,
            'tie_broken': False,
            'method': 'default_fallback'
        }
    
    # Step 1: Deduplicate points by rounding to 4 decimal places (~11m precision)
    print(f"🔍 Processing {len(sample_points)} sample points for country determination")
    
    unique_points = set()
    for lat, lon in sample_points:
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            # Round to 4 decimal places for deduplication
            rounded_lat = round(lat, 4)
            rounded_lon = round(lon, 4)
            unique_points.add((rounded_lat, rounded_lon))
        else:
            print(f"⚠️  Invalid coordinates skipped: ({lat}, {lon})")
    
    unique_points_list = list(unique_points)
    total_unique = len(unique_points_list)
    
    if total_unique == 0:
        print("⚠️  No valid coordinates found")
        return {
            'country': 'global_average',
            'count': 0,
            'total_points': 0,
            'tie_broken': False,
            'method': 'no_valid_coordinates'
        }
    
    print(f"📍 Deduplicated to {total_unique} unique points (precision: 4 decimal places)")
    
    # Step 2: Get country for each unique point with progress tracking
    country_results = []
    
    with st.spinner(f"🌍 Determining countries for {total_unique} unique points..."):
        for i, (lat, lon) in enumerate(unique_points_list):
            try:
                # Use the existing cached geocoding function
                country = get_country_from_coordinates_nominatim(lat, lon)
                country_results.append(country)
                
                # Progress feedback every 25% or significant milestones
                if total_unique > 4 and (i + 1) % max(1, total_unique // 4) == 0:
                    progress = ((i + 1) / total_unique) * 100
                    print(f"🔄 Country lookup progress: {progress:.1f}% ({i + 1}/{total_unique})")
                    
            except Exception as e:
                print(f"⚠️  Error geocoding ({lat}, {lon}): {e}")
                country_results.append('global_average')
    
    # Step 3: Count countries and handle special cases
    valid_countries = [c for c in country_results if c and c != 'global_average']
    
    if not valid_countries:
        print("🌊 All points are in international waters or unidentifiable")
        return {
            'country': 'International Waters',
            'count': len(country_results),
            'total_points': total_unique,
            'tie_broken': False,
            'method': 'all_international_waters'
        }
    
    # Count occurrences
    country_counts = Counter(valid_countries)
    total_valid_points = len(valid_countries)
    
    print(f"📊 Country distribution: {dict(country_counts)}")
    
    # Step 4: Determine winner with tie-breaking logic
    max_count = max(country_counts.values())
    top_countries = [country for country, count in country_counts.items() if count == max_count]
    
    tie_broken = len(top_countries) > 1
    method = 'majority_vote'
    
    if tie_broken:
        print(f"⚖️  Tie detected between {len(top_countries)} countries: {top_countries}")
        
        # Tie-breaker 1: Use polygon centroid country
        try:
            # Calculate centroid of all sample points
            total_lat = sum(lat for lat, lon in sample_points)
            total_lon = sum(lon for lat, lon in sample_points)
            centroid_lat = total_lat / len(sample_points)
            centroid_lon = total_lon / len(sample_points)
            
            print(f"📍 Calculating tie-breaker using centroid: ({centroid_lat:.4f}, {centroid_lon:.4f})")
            
            centroid_country = get_country_from_coordinates_nominatim(centroid_lat, centroid_lon)
            
            if centroid_country in top_countries:
                final_country = centroid_country
                method = 'centroid_tiebreaker'
                print(f"✅ Tie resolved using centroid country: {final_country}")
            else:
                # Tie-breaker 2: Alphabetical order
                final_country = sorted(top_countries)[0]
                method = 'alphabetical_tiebreaker'
                print(f"✅ Tie resolved alphabetically: {final_country} (from {top_countries})")
                
        except Exception as e:
            print(f"⚠️  Centroid calculation failed: {e}")
            # Fallback to alphabetical
            final_country = sorted(top_countries)[0]
            method = 'alphabetical_tiebreaker'
            print(f"✅ Tie resolved alphabetically (fallback): {final_country}")
    else:
        final_country = top_countries[0]
        print(f"✅ Clear winner: {final_country} with {max_count}/{total_valid_points} points")
    
    # Step 5: Prepare comprehensive result
    result = {
        'country': final_country,
        'count': country_counts[final_country],
        'total_points': total_unique,
        'tie_broken': tie_broken,
        'method': method
    }
    
    # Step 6: Log final result
    percentage = (result['count'] / total_valid_points) * 100
    print(f"🏆 Final result: {final_country} ({result['count']}/{total_valid_points} = {percentage:.1f}%)")
    print(f"📋 Method: {method}, Tie broken: {tie_broken}")
    
    return result