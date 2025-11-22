"""Weather agent for fetching current weather conditions.

Implements Open-Meteo API for weather data.
"""

import requests
from datetime import datetime
from typing import Dict, Any, Optional


# Open-Meteo API base URL
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch current weather for the given coordinates using Open-Meteo.
    
    Args:
        lat: Latitude (must be float)
        lon: Longitude (must be float)
        
    Returns:
        Dictionary with weather data:
        {
            "temp_c": float,          # Current temperature in Celsius
            "precip_percent": int,    # 0-100, chance of rain
            "summary": str            # Short text description
        }
        
    Raises:
        RuntimeError: On API/network/parse errors
        TypeError: If lat/lon are not float types
        
    Notes:
        - Extracts temperature from current_weather.temperature
        - Estimates precipitation from hourly data closest to current time
        - Maps weathercode to human-readable summary
    """
    # Validate input types
    if not isinstance(lat, float) and not isinstance(lat, int):
        raise TypeError(f"lat must be float, got {type(lat)}")
    if not isinstance(lon, float) and not isinstance(lon, int):
        raise TypeError(f"lon must be float, got {type(lon)}")
    
    # Convert to float if int
    lat = float(lat)
    lon = float(lon)
    
    # Prepare request parameters
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": "precipitation_probability",
        "timezone": "auto"
    }
    
    try:
        # Make API request
        response = requests.get(
            OPEN_METEO_BASE_URL,
            params=params,
            timeout=10.0
        )
        
        # Check for HTTP errors
        if response.status_code != 200:
            raise RuntimeError("weather_api_error")
        
        # Parse JSON response
        try:
            data = response.json()
        except (ValueError, TypeError) as e:
            raise RuntimeError("weather_parse_error") from e
        
        # Extract current temperature
        try:
            current_weather = data.get("current_weather", {})
            temp_c = float(current_weather.get("temperature", 0.0))
        except (ValueError, TypeError, KeyError) as e:
            raise RuntimeError("weather_parse_error") from e
        
        # Extract precipitation probability
        precip_percent = extract_precipitation_probability(data)
        
        # Generate summary from weathercode
        summary = generate_weather_summary(current_weather.get("weathercode"))
        
        return {
            "temp_c": temp_c,
            "precip_percent": precip_percent,
            "summary": summary
        }
        
    except requests.RequestException as e:
        # Network/request errors
        raise RuntimeError("weather_api_error") from e
    except RuntimeError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Other unexpected errors
        raise RuntimeError("weather_api_error") from e


def extract_precipitation_probability(data: Dict[str, Any]) -> int:
    """
    Extract precipitation probability from hourly data.
    
    Finds the hourly precipitation_probability value for the hour closest
    to the current time. If not available, defaults to 0.
    
    Args:
        data: Full API response dictionary
        
    Returns:
        Precipitation probability as integer (0-100)
    """
    try:
        hourly = data.get("hourly", {})
        precip_prob = hourly.get("precipitation_probability", [])
        time_values = hourly.get("time", [])
        
        if not precip_prob or not time_values:
            return 0
        
        # Get current UTC time
        current_utc = datetime.utcnow()
        
        # Find the closest hour
        closest_idx = 0
        min_diff = float('inf')
        
        for idx, time_str in enumerate(time_values):
            try:
                # Parse time string (format: "2024-01-01T12:00" or "2024-01-01T12:00Z")
                # Remove timezone suffix if present
                clean_time = time_str.replace("Z", "").replace("+00:00", "")
                time_obj = datetime.fromisoformat(clean_time)
                
                # Calculate time difference
                diff = abs((time_obj - current_utc).total_seconds())
                
                if diff < min_diff:
                    min_diff = diff
                    closest_idx = idx
            except (ValueError, TypeError, AttributeError):
                continue
        
        # Get precipitation probability for closest hour (or first if no match found)
        if closest_idx < len(precip_prob):
            prob = precip_prob[closest_idx]
            if prob is not None:
                return int(prob)
        
        # Fallback: use first value if available
        if len(precip_prob) > 0 and precip_prob[0] is not None:
            return int(precip_prob[0])
        
        return 0
        
    except (KeyError, ValueError, TypeError, IndexError):
        # If anything fails, default to 0
        return 0


def generate_weather_summary(weathercode: Optional[int]) -> str:
    """
    Generate a human-readable weather summary from weathercode.
    
    Maps WMO weather codes to text descriptions.
    
    Args:
        weathercode: WMO weather code (0-99) or None
        
    Returns:
        Short text description of weather conditions
    """
    if weathercode is None:
        return "Weather data available"
    
    # WMO Weather interpretation codes (WW)
    # Reference: https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
    weather_map = {
        # Clear sky
        0: "Clear sky",
        # Mainly clear, partly cloudy, overcast
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        # Fog and depositing rime fog
        45: "Fog",
        48: "Depositing rime fog",
        # Drizzle
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        # Rain
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        # Snow
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        # Rain showers
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        # Thunderstorm
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    
    # Check exact match first
    if weathercode in weather_map:
        return weather_map[weathercode]
    
    # Check ranges
    if 1 <= weathercode <= 3:
        return "Partly cloudy"
    elif 51 <= weathercode <= 67:
        return "Drizzle/Rain"
    elif 71 <= weathercode <= 77:
        return "Snow"
    elif 80 <= weathercode <= 82:
        return "Rain showers"
    elif 95 <= weathercode <= 99:
        return "Thunderstorm"
    else:
        return "Weather data available"
