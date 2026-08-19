from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Nominatim requires a unique user_agent per app (their usage policy)
geolocator = Nominatim(user_agent="civicsignal_app")


def geocode_location(location_text: str) -> tuple[float | None, float | None]:
    """
    Convert free-text location (e.g. 'Ward 4, near Central Market')
    into (latitude, longitude). Returns (None, None) if geocoding fails
    or no location text was provided — never raises, so it never blocks
    a citizen request from being saved.
    """
    if not location_text or not location_text.strip():
        return None, None

    try:
        location = geolocator.geocode(location_text, timeout=5)
        if location:
            return location.latitude, location.longitude
        return None, None
    except (GeocoderTimedOut, GeocoderServiceError):
        return None, None
    except Exception:
        return None, None