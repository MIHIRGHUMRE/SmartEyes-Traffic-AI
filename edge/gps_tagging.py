from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime
import json

class GPSTagger:
    """Handle GPS tagging and location services."""

    def __init__(self, api_key: str = None):
        """
        Initialize GPS tagger.

        Args:
            api_key: API key for location services (optional)
        """
        self.geolocator = Nominatim(user_agent="traffic_violation_system")
        self.api_key = api_key

    def get_location_from_gps(self, latitude: float, longitude: float) -> Dict:
        """
        Get location details from GPS coordinates.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Location information dictionary
        """
        try:
            location = self.geolocator.reverse((latitude, longitude))

            if location:
                address = location.raw.get('address', {})

                return {
                    'latitude': latitude,
                    'longitude': longitude,
                    'address': location.address,
                    'city': address.get('city', address.get('town', address.get('village'))),
                    'state': address.get('state'),
                    'country': address.get('country'),
                    'postcode': address.get('postcode'),
                    'road': address.get('road'),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Error getting location: {e}")

        return {
            'latitude': latitude,
            'longitude': longitude,
            'address': None,
            'timestamp': datetime.now().isoformat()
        }

    def get_gps_from_ip(self) -> Optional[Tuple[float, float]]:
        """Get approximate GPS coordinates from IP address."""
        try:
            response = requests.get('http://ip-api.com/json/')
            data = response.json()

            if data['status'] == 'success':
                return data['lat'], data['lon']
        except Exception as e:
            print(f"Error getting GPS from IP: {e}")

        return None

    def calculate_distance(self, point1: Tuple[float, float],
                          point2: Tuple[float, float]) -> float:
        """
        Calculate distance between two GPS points in kilometers.

        Args:
            point1: (latitude, longitude) tuple
            point2: (latitude, longitude) tuple

        Returns:
            Distance in kilometers
        """
        return geodesic(point1, point2).kilometers

    def is_within_city_limits(self, latitude: float, longitude: float,
                            city_center: Tuple[float, float], radius_km: float = 50) -> bool:
        """
        Check if GPS point is within city limits.

        Args:
            latitude: Point latitude
            longitude: Point longitude
            city_center: (lat, lon) of city center
            radius_km: City radius in kilometers

        Returns:
            True if within city limits
        """
        point = (latitude, longitude)
        distance = self.calculate_distance(point, city_center)
        return distance <= radius_km

    def get_speed_zones(self, latitude: float, longitude: float) -> Dict:
        """
        Get speed limits for location (mock implementation).

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            Speed zone information
        """
        # This would typically query a GIS database or API
        # For demo purposes, return default values
        return {
            'speed_limit': 60,  # km/h
            'zone_type': 'urban',
            'restrictions': []
        }

    def tag_evidence(self, evidence: Dict, latitude: float = None,
                    longitude: float = None) -> Dict:
        """
        Tag evidence with GPS information.

        Args:
            evidence: Evidence dictionary
            latitude: Optional latitude
            longitude: Optional longitude

        Returns:
            Tagged evidence
        """
        if latitude is None or longitude is None:
            gps_coords = self.get_gps_from_ip()
            if gps_coords:
                latitude, longitude = gps_coords

        if latitude and longitude:
            location_info = self.get_location_from_gps(latitude, longitude)
            evidence['gps'] = location_info

            # Add speed zone info
            speed_info = self.get_speed_zones(latitude, longitude)
            evidence['speed_zone'] = speed_info

        return evidence