"""Parent (orchestrator) agent for the multi-agent tourism system.

This agent coordinates between child agents (weather, places, geocoding)
to handle user travel planning queries.
"""

import re
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional

from agents.tools.geocode_tool import geocode
from agents.tools.weather_agent_stub import get_weather
from agents.tools.places_agent_stub import find_pois

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def detect_intent(user_input: str) -> Tuple[bool, bool]:
    """
    Detect user intent from input text.
    
    Args:
        user_input: User's query text
        
    Returns:
        Tuple of (wants_weather, wants_places)
    """
    text_lower = user_input.lower()
    
    # Weather keywords: 'temperature','weather','rain' -> weather
    weather_keywords = ['temperature', 'weather', 'rain', 'raining', 'rainy']
    wants_weather = any(keyword in text_lower for keyword in weather_keywords)
    
    # Places keywords: 'visit','places','tour','attractions','plan' -> places
    places_keywords = ['visit', 'places', 'tour', 'attractions', 'plan', 'sights', 
                      'see', 'go', 'tourist', 'things to do']
    wants_places = any(keyword in text_lower for keyword in places_keywords)
    
    # If no explicit intent, default to both
    if not wants_weather and not wants_places:
        wants_weather = True
        wants_places = True
    
    return wants_weather, wants_places


def extract_place_name(user_input: str) -> Optional[str]:
    """
    Robust place extractor.

    Strategy:
    1. Split input into sentence/clauses and examine from last -> first.
    2. In each clause, prefer explicit phrase matches (to/in/visit/going to/...),
       taking the last match in that clause (handles "going to go to X").
    3. Accept lowercase matches if token length > 2 and not blacklisted.
    4. Fallback to capitalized proper-noun sequences in the clause.
    5. Final fallback: last capitalized sequence in whole input (ignoring blacklist).
    Returns normalized Title Case string or None.
    """
    if not user_input or not user_input.strip():
        return None

    text = user_input.strip()

    # tokens we absolutely should not treat as place names
    blacklist = {
        "i", "i'm", "i’m", "im", "i am",
        "the", "a", "an",
        "go", "going", "and", "lets", "let's",
        "please", "thanks", "thank"
    }

    # helper to normalize candidate to Title Case
    def normalize(tok: str) -> str:
        parts = [p for p in re.split(r"[\s\-_/()]+", tok.strip()) if p]
        return " ".join([w.capitalize() for w in parts])

    # split into clauses/sentences (keep order), examine from last to first
    clauses = re.split(r'[;.!?]\s*', text)
    if not clauses:
        clauses = [text]

    # phrase patterns to find place mentions (we'll take the last match in the clause)
    phrase_patterns = [
        r"\bgoing\s+to\s+([A-Za-z][A-Za-z\-\s']+)",
        r"\bto\s+([A-Za-z][A-Za-z\-\s']+)",
        r"\bin\s+([A-Za-z][A-Za-z\-\s']+)",
        r"\bvisit\s+([A-Za-z][A-Za-z\-\s']+)",
        r"\btravel\s+to\s+([A-Za-z][A-Za-z\-\s']+)"
    ]

    for clause in reversed(clauses):
        clause = clause.strip()
        if not clause:
            continue

        # Look for all phrase matches in this clause, prefer the last one
        candidates = []
        for pat in phrase_patterns:
            for m in re.finditer(pat, clause, re.IGNORECASE):
                raw = m.group(1).strip()
                # take first token of the captured group (handles "to go to mangalore")
                first_token = re.split(r"[\s,\/\-\(\)]+", raw)[0]
                if first_token:
                    # determine original char capitalization in clause for this match
                    start_idx = m.start(1)
                    orig_first_char = clause[start_idx:start_idx+1]
                    candidates.append((first_token, orig_first_char))
        # if we found any, evaluate the last candidate
        if candidates:
            tok, orig_first_char = candidates[-1]
            if orig_first_char.isupper():
                if tok.lower() not in blacklist:
                    return normalize(tok)
            else:
                tok_clean = tok.strip().lower()
                if tok_clean not in blacklist and len(tok_clean) > 2:
                    return normalize(tok_clean)
            # otherwise continue to fallback checks for this clause

        # Fallback within clause: find the last sequence of capitalized words
        # e.g., "Tell me about New Delhi" or "Visit Sri Krishna Temple"
        words = re.findall(r"[A-Za-z][A-Za-z'\-]*", clause)
        proper_seq = []
        for w in reversed(words):
            if w and w[0].isupper() and w.lower() not in blacklist:
                proper_seq.insert(0, w)
            elif proper_seq:
                # finished a capitalized sequence
                return " ".join(proper_seq)
        if proper_seq:
            return " ".join(proper_seq)

    # Final fallback: examine entire text for last capitalized sequence (ignore blacklisted tokens)
    all_words = re.findall(r"[A-Za-z][A-Za-z'\-]*", text)
    seq = []
    for w in reversed(all_words):
        if w and w[0].isupper() and w.lower() not in blacklist:
            seq.insert(0, w)
        elif seq:
            return " ".join(seq)
    if seq:
        return " ".join(seq)

    # Last-ditch: capture the first non-blacklist word after last "to" or "in" even if lowercase
    m = re.search(r"(?:to|in|visit|travel to|going to)\s+([a-z][a-z\-\s']+)$", text.strip(), re.IGNORECASE)
    if m:
        tok = re.split(r"[\s,\/\-\(\)]+", m.group(1).strip())[0]
        if tok and tok.lower() not in blacklist and len(tok) > 2:
            return normalize(tok)

    return None




def handle_query(user_input: str) -> Dict[str, Any]:
    """
    Main handler for user queries.
    
    Processes the query, detects intent, geocodes place, fetches weather/places,
    and formats the response according to assignment specifications.
    
    Args:
        user_input: User's query text
        
    Returns:
        Dictionary with keys:
        - reply: Formatted response text
        - debug: Debug information (logs, errors, etc.)
    """
    # Initialize debug structure
    debug_info: Dict[str, Any] = {
        "user_input": user_input,
        "place_query": None,
        "geocode": {},
        "weather_api": {"called": False, "result": None, "error": None},
        "places_api": {"called": False, "result_count": 0, "error": None},
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        # Step 1: Detect intent
        wants_weather, wants_places = detect_intent(user_input)
        logger.info(f"Detected intent: weather={wants_weather}, places={wants_places}")
        
        # Step 2: Extract place name
        place_name = extract_place_name(user_input)
        if not place_name:
            debug_info["error"] = "missing_place"
            logger.warning("Could not extract place name from input")
            return {
                "reply": "Which place are you planning to visit? Please provide the city or landmark name.",
                "debug": debug_info
            }
        
        debug_info["place_query"] = place_name
        
        # Step 3: Geocode the place
        try:
            geocode_result = geocode(place_name)
            lat = geocode_result["lat"]
            lon = geocode_result["lon"]
            display_name = geocode_result["display_name"]
            debug_info["geocode"] = geocode_result
            logger.info(f"Geocoded '{place_name}' to ({lat}, {lon}): {display_name}")
        except ValueError as e:
            if "place_not_found" in str(e):
                debug_info["geocode"] = {"error": "place_not_found"}
                logger.error(f"Place not found: {place_name}")
                return {
                    "reply": "I'm sorry — I don't know this place. Could you check the spelling or provide a nearby city/country?",
                    "debug": debug_info
                }
            else:
                debug_info["geocode"] = {"error": str(e)}
                logger.error(f"Geocoding error: {e}")
                return {
                    "reply": "I'm sorry — I encountered an error processing your request.",
                    "debug": debug_info
                }
        except RuntimeError as e:
            debug_info["geocode"] = {"error": str(e)}
            logger.error(f"Geocoding API error: {e}")
            return {
                "reply": "I'm sorry — I encountered an error processing your request.",
                "debug": debug_info
            }
        
        # Use a short place name (user-provided / extracted) for responses.
        # Keep the full display_name in debug (debug_info["geocode"] already contains it).
        display_place_name = place_name  # use short user-friendly name in replies
        
        # Step 4: Fetch weather if requested
        weather_data = None
        weather_error = None
        if wants_weather:
            debug_info["weather_api"]["called"] = True
            try:
                weather_data = get_weather(lat, lon)
                debug_info["weather_api"]["result"] = {
                    "temp_c": weather_data.get("temp_c"),
                    "precip_percent": weather_data.get("precip_percent")
                }
                logger.info(f"Weather data: {weather_data}")
            except RuntimeError as e:
                weather_error = str(e)
                debug_info["weather_api"]["error"] = weather_error
                logger.error(f"Weather API error: {e}")
            except Exception as e:
                weather_error = str(e)
                debug_info["weather_api"]["error"] = weather_error
                logger.error(f"Weather error: {e}")
        
        # Step 5: Fetch places if requested
        places_list = []
        places_error = None
        if wants_places:
            debug_info["places_api"]["called"] = True
            try:
                places_list = find_pois(lat, lon, radius_m=5000, max_results=5)
                debug_info["places_api"]["result_count"] = len(places_list)
                logger.info(f"Found {len(places_list)} places")
            except RuntimeError as e:
                places_error = str(e)
                debug_info["places_api"]["error"] = places_error
                logger.error(f"Places API error: {e}")
            except Exception as e:
                places_error = str(e)
                debug_info["places_api"]["error"] = places_error
                logger.error(f"Places error: {e}")
        
        # Step 6: Format response according to assignment examples
        reply = format_response(
            display_place_name, 
            wants_weather, 
            wants_places, 
            weather_data, 
            weather_error,
            places_list,
            places_error
        )
        
        # Log debug info
        logger.info(f"Debug info: {debug_info}")
        
        return {
            "reply": reply,
            "debug": debug_info
        }
        
    except Exception as e:
        debug_info["error"] = f"Unexpected error: {str(e)}"
        logger.exception("Unexpected error in handle_query")
        return {
            "reply": "I'm sorry — I encountered an error processing your request.",
            "debug": debug_info
        }


def format_response(
    place_name: str, 
    wants_weather: bool, 
    wants_places: bool,
    weather_data: Optional[Dict[str, Any]], 
    weather_error: Optional[str],
    places_list: List[Dict[str, Any]], 
    places_error: Optional[str]
) -> str:
    """
    Format the final response according to assignment specifications.
    
    Args:
        place_name: Display name of the place (short name used in replies)
        wants_weather: Whether user wants weather info
        wants_places: Whether user wants places info
        weather_data: Weather data dict with temp_c and precip_percent
        weather_error: Error message if weather fetch failed
        places_list: List of POI dicts with "name" and "distance_m"
        places_error: Error message if places fetch failed
        
    Returns:
        Formatted response string
    """
    parts = []
    
    # Weather part
    if wants_weather:
        if weather_data:
            # Round temperature to nearest integer, precipitation as integer
            temp = round(weather_data.get("temp_c", 0))
            rain_prob = int(weather_data.get("precip_percent", 0))
            weather_text = f"In {place_name} it's currently {temp}°C with a chance of {rain_prob}% to rain."
            parts.append(weather_text)
        elif weather_error:
            # User-friendly fallback for weather errors
            parts.append(f"Weather information currently unavailable for {place_name}.")
    
    # Places part
    if wants_places:
        if places_list and len(places_list) > 0:
            # Extract names from dict format
            place_names = [place.get("name", "Unknown") for place in places_list if isinstance(place, dict)]
            
            if place_names:
                if parts:
                    # If weather was included, add connector
                    places_text = "And these are the places you can go:\n"
                else:
                    places_text = f"In {place_name} these are the places you can go:\n"
                
                # Format places as bullet list (up to 5)
                places_items = "\n".join([f"- {name}" for name in place_names[:5]])
                places_text += places_items
                parts.append(places_text)
            else:
                # No valid places found
                if not parts:  # Only show if no weather info
                    parts.append(f"I couldn't find tourist attractions within 5 km of {place_name}.")
        elif places_error:
            # Error occurred but continue (error already in debug)
            if not parts:  # Only show if no weather info
                parts.append(f"I couldn't find tourist attractions within 5 km of {place_name}.")
        else:
            # No places found (empty list returned)
            if not parts:  # Only show if no weather info
                parts.append(f"I couldn't find tourist attractions within 5 km of {place_name}.")
    
    # If no data available for requested intents
    if not parts:
        if wants_weather and wants_places:
            return f"I'm sorry — I couldn't find weather or places information for {place_name}."
        elif wants_weather:
            return f"I'm sorry — I couldn't find weather information for {place_name}."
        elif wants_places:
            return f"I'm sorry — I couldn't find places information for {place_name}."
        else:
            return f"I'm sorry — I couldn't process your request for {place_name}."
    
    return "\n".join(parts)

def detect_intent(user_input: str) -> Tuple[bool, bool]:
    """
    Detect user intent from input text.

    Rules:
    - Look for weather-specific keywords => weather intent.
    - Look for place/tour-specific keywords => places intent.
    - Remove overly-generic tokens like 'go' which cause false positives.
    - If weather keywords are present and there are no explicit places keywords,
      prefer weather-only (so asking "what is the temperature" won't return places).
    - If no explicit keywords found, default to both (helps when user just says "I'm going to X").
    """
    text_lower = user_input.lower()

    # Weather keywords (explicit)
    weather_keywords = ['temperature', 'temp', 'weather', 'rain', 'raining', 'rainy', 'forecast']

    # Places keywords — avoid generic verbs like "go"
    places_keywords = [
        'visit', 'places', 'tour', 'attractions', 'plan', 'sights',
        'see', 'tourist', 'things to do', 'things to see', 'what to do'
    ]

    wants_weather = any(keyword in text_lower for keyword in weather_keywords)
    wants_places = any(keyword in text_lower for keyword in places_keywords)

    # If user explicitly asked for weather and didn't ask for places -> weather only
    if wants_weather and not wants_places:
        return True, False

    # If user explicitly asked for places and didn't ask for weather -> places only
    if wants_places and not wants_weather:
        return False, True

    # If both detected, return both
    if wants_weather and wants_places:
        return True, True

    # If nothing explicit, default to both (keeps behavior for "I'm going to <city>")
    return True, True

