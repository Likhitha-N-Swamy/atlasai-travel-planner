"""Geocoding tool for converting place names to coordinates.

Implements Nominatim API (OpenStreetMap) for geocoding.
"""

import time
import json
from typing import Dict, Any, List

import httpx


# Nominatim API endpoint
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search"

# Custom User-Agent header (required by Nominatim usage policy)
USER_AGENT = "AtlasAI-TravelPlanner/1.0 (contact: lisw22cs@cmrit.ac.in)"


def geocode(place: str) -> Dict[str, Any]:
    """
    Convert a place name to latitude, longitude, and display name using Nominatim API.
    
    Args:
        place: Place name or address to geocode
        
    Returns:
        Dictionary with keys:
        {
            "lat": float,           # Latitude
            "lon": float,           # Longitude
            "display_name": str     # Full display name
        }
        
    Raises:
        ValueError: If place is not found (empty results)
        RuntimeError: If API request fails or response cannot be parsed
        
    Notes:
        - Includes 1-second delay after request (Nominatim usage policy)
        - Selects best match based on "importance" field
        - Falls back to first result if importance not available
    """
    if not place or not place.strip():
        raise ValueError("place_not_found")
    
    # Prepare request parameters
    params = {
        "q": place.strip(),
        "format": "json",
        "limit": 5,
        "addressdetails": 1
    }
    
    # Prepare headers with custom User-Agent
    headers = {
        "User-Agent": USER_AGENT
    }
    
    try:
        # Make API request
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                NOMINATIM_BASE_URL,
                params=params,
                headers=headers
            )
            response.raise_for_status()
        
        # Add 1-second delay after request (Nominatim usage policy)
        time.sleep(1)
        
    except httpx.HTTPError as e:
        # Request failure
        raise RuntimeError("geocode_api_error") from e
    except Exception as e:
        # Other request errors
        raise RuntimeError("geocode_api_error") from e
    
    # Parse JSON response
    try:
        results: List[Dict[str, Any]] = response.json()
    except (json.JSONDecodeError, ValueError) as e:
        # Invalid JSON
        raise RuntimeError("geocode_parse_error") from e
    
    # Check if results are empty
    if not results or len(results) == 0:
        raise ValueError("place_not_found")
    
    # Select best match based on importance
    best_result = select_best_match(results)
    
    # Extract required fields
    try:
        lat = float(best_result.get("lat", 0))
        lon = float(best_result.get("lon", 0))
        display_name = best_result.get("display_name", place)
        
        return {
            "lat": lat,
            "lon": lon,
            "display_name": display_name
        }
    except (ValueError, TypeError) as e:
        # Invalid data in response
        raise RuntimeError("geocode_parse_error") from e


def select_best_match(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Select the best match from geocoding results.
    
    Selection criteria:
    1. Highest "importance" field (if available)
    2. Fallback to first result
    
    Args:
        results: List of geocoding results from Nominatim
        
    Returns:
        Best matching result dictionary
    """
    if not results:
        raise ValueError("place_not_found")
    
    # If only one result, return it
    if len(results) == 1:
        return results[0]
    
    # Try to find result with highest importance
    best_result = None
    max_importance = -1.0
    
    for result in results:
        importance = result.get("importance", -1.0)
        if isinstance(importance, (int, float)) and importance > max_importance:
            max_importance = importance
            best_result = result
    
    # If we found a result with importance, return it
    if best_result is not None and max_importance >= 0:
        return best_result
    
    # Fallback to first result
    return results[0]
