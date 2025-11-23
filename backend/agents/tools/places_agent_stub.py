"""Places agent for finding points of interest (POIs).

Implements Overpass API (OpenStreetMap) for finding tourist attractions.
"""

import time
import json
from typing import List, Dict, Any, Optional

import requests

from ...utils.haversine import haversine_distance
from ...utils.cache import SimpleCache


# Overpass API endpoint
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"

# Cache for POI results (24 hours TTL)
poi_cache = SimpleCache(ttl=86400)  # 24 hours in seconds


def find_pois(lat: float, lon: float, radius_m: int = 5000, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Find points of interest near a location using Overpass API.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius_m: Search radius in meters (default: 5000)
        max_results: Maximum number of results to return (default: 5)
        
    Returns:
        List of POI dictionaries, each containing:
        [
            {
                "name": str,           # POI name
                "distance_m": int      # Distance in meters
            },
            ...
        ]
        Sorted by distance (ascending), with preference for tourism > historic > parks/museums.
        
    Raises:
        RuntimeError: On API errors or rate limiting (after retries)
        
    Notes:
        - Results are cached for 24 hours
        - Filters out entries without names or with generic names
        - Deduplicates by name (case-insensitive)
        - Handles rate limiting with retry logic
    """
    # Validate inputs
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        raise TypeError("lat and lon must be numeric")
    if not isinstance(radius_m, int) or radius_m <= 0:
        raise TypeError("radius_m must be a positive integer")
    if not isinstance(max_results, int) or max_results <= 0:
        raise TypeError("max_results must be a positive integer")
    
    # Check cache first
    cache_key = f"pois_{lat}_{lon}_{radius_m}"
    cached_result = poi_cache.get(cache_key)
    if cached_result is not None:
        return cached_result[:max_results]  # Return cached results limited to max_results
    
    # Build Overpass QL query
    query = build_overpass_query(lat, lon, radius_m)
    
    # Make API request with retry logic for rate limiting
    try:
        response_data = make_overpass_request(query, lat, lon, radius_m)
    except RuntimeError as e:
        if "rate_limited" in str(e):
            raise
        raise RuntimeError("places_api_error") from e
    
    # Parse and process results
    try:
        pois = parse_overpass_response(response_data, lat, lon, max_results)
    except (KeyError, ValueError, TypeError) as e:
        raise RuntimeError("places_parse_error") from e
    
    # Cache results
    poi_cache.set(cache_key, pois)
    
    return pois[:max_results]


def build_overpass_query(lat: float, lon: float, radius_m: int) -> str:
    """
    Build Overpass QL query for finding POIs.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius_m: Search radius in meters
        
    Returns:
        Overpass QL query string
    """
    query = f"""[out:json][timeout:25];
(
  node(around:{radius_m},{lat},{lon})[tourism];
  node(around:{radius_m},{lat},{lon})[historic];
  node(around:{radius_m},{lat},{lon})[leisure=park];
  node(around:{radius_m},{lat},{lon})[amenity=museum];
  way(around:{radius_m},{lat},{lon})[tourism];
  way(around:{radius_m},{lat},{lon})[historic];
  relation(around:{radius_m},{lat},{lon})[tourism];
  relation(around:{radius_m},{lat},{lon})[historic];
);
out center;"""
    return query


def make_overpass_request(query: str, lat: float, lon: float, radius_m: int) -> Dict[str, Any]:
    """
    Make Overpass API request with rate limiting retry logic.
    
    Args:
        query: Overpass QL query string
        lat: Latitude (for retry with broader radius)
        lon: Longitude (for retry with broader radius)
        radius_m: Current radius (for retry with broader radius)
        
    Returns:
        Parsed JSON response data
        
    Raises:
        RuntimeError: On API errors or rate limiting (after all retries)
    """
    headers = {
        "Content-Type": "text/plain"
    }
    
    # First attempt
    try:
        response = requests.post(
            OVERPASS_API_URL,
            data=query,
            headers=headers,
            timeout=30.0
        )
        
        # Check for rate limiting (429)
        if response.status_code == 429:
            # Wait 1 second and retry once
            time.sleep(1)
            response = requests.post(
                OVERPASS_API_URL,
                data=query,
                headers=headers,
                timeout=30.0
            )
            
            # If still rate limited, try with broader radius
            if response.status_code == 429:
                broader_query = build_overpass_query(lat, lon, 15000)
                time.sleep(1)
                response = requests.post(
                    OVERPASS_API_URL,
                    data=broader_query,
                    headers=headers,
                    timeout=30.0
                )
                
                # If still rate limited after all retries
                if response.status_code == 429:
                    raise RuntimeError("places_api_rate_limited")
        
        # Check for other HTTP errors
        if response.status_code != 200:
            raise RuntimeError("places_api_error")
        
        # Parse JSON response
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError) as e:
            raise RuntimeError("places_parse_error") from e
            
    except requests.RequestException as e:
        raise RuntimeError("places_api_error") from e


def parse_overpass_response(data: Dict[str, Any], lat: float, lon: float, max_results: int) -> List[Dict[str, Any]]:
    """
    Parse Overpass API response and extract POIs.
    
    Args:
        data: Parsed JSON response from Overpass
        lat: Reference latitude for distance calculation
        lon: Reference longitude for distance calculation
        max_results: Maximum number of results
        
    Returns:
        List of POI dictionaries sorted by distance
    """
    elements = data.get("elements", [])
    pois = []
    seen_names = set()  # For deduplication (case-insensitive)
    
    for element in elements:
        # Extract name from tags
        tags = element.get("tags", {})
        name = tags.get("name", "").strip()
        
        # Filter out entries without names or with generic names
        if not name or name.lower() in ["unnamed", "unknown", ""]:
            continue
        
        # Deduplicate by name (case-insensitive)
        name_lower = name.lower()
        if name_lower in seen_names:
            continue
        seen_names.add(name_lower)
        
        # Get coordinates
        if element.get("type") == "node":
            poi_lat = element.get("lat")
            poi_lon = element.get("lon")
        elif element.get("type") in ["way", "relation"]:
            center = element.get("center", {})
            poi_lat = center.get("lat")
            poi_lon = center.get("lon")
        else:
            continue
        
        if poi_lat is None or poi_lon is None:
            continue
        
        # Calculate distance using Haversine formula (returns km, convert to meters)
        distance_km = haversine_distance(lat, lon, poi_lat, poi_lon)
        distance_m = int(distance_km * 1000)
        
        # Calculate priority score (tourism > historic > parks/museums)
        priority = calculate_priority(tags)
        
        pois.append({
            "name": name,
            "distance_m": distance_m,
            "priority": priority,
            "lat": poi_lat,
            "lon": poi_lon
        })
    
    # Sort by priority (higher first), then by distance (lower first)
    pois.sort(key=lambda x: (-x["priority"], x["distance_m"]))
    
    # Remove priority from final results
    result = [
        {
            "name": poi["name"],
            "distance_m": poi["distance_m"]
        }
        for poi in pois[:max_results]
    ]
    
    return result


def calculate_priority(tags: Dict[str, Any]) -> int:
    """
    Calculate priority score for a POI based on its tags.
    
    Higher priority = more important for tourists.
    tourism > historic > parks/museums > others
    
    Args:
        tags: OSM tags dictionary
        
    Returns:
        Priority score (higher = more important)
    """
    if "tourism" in tags:
        return 3
    elif "historic" in tags:
        return 2
    elif tags.get("leisure") == "park" or tags.get("amenity") == "museum":
        return 1
    else:
        return 0
