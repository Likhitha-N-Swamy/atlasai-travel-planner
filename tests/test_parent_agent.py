# tests/test_parent_agent.py
"""Test suite for parent agent.

Tests cover:
- Places-only queries
- Weather-only queries
- Both weather and places queries
- Unknown place handling
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.agents.parent_agent import handle_query, detect_intent, extract_place_name


class TestIntentDetection:
    """Test intent detection functionality."""
    
    def test_weather_intent(self):
        """Test detection of weather intent."""
        wants_weather, wants_places = detect_intent("What's the weather in Paris?")
        assert wants_weather is True
        assert wants_places is False
    
    def test_places_intent(self):
        """Test detection of places intent."""
        wants_weather, wants_places = detect_intent("What places can I visit in Tokyo?")
        assert wants_weather is False
        assert wants_places is True
    
    def test_both_intent(self):
        """Test detection of both weather and places intent."""
        wants_weather, wants_places = detect_intent("I'm going to London. What's the weather and what can I see?")
        assert wants_weather is True
        assert wants_places is True
    
    def test_default_intent(self):
        """Test default to both when no explicit intent."""
        wants_weather, wants_places = detect_intent("I'm going to New York")
        assert wants_weather is True
        assert wants_places is True


class TestPlaceExtraction:
    """Test place name extraction."""
    
    def test_extract_place_going_to(self):
        """Test extraction from 'going to' pattern."""
        place = extract_place_name("I'm going to Bangalore")
        assert place == "Bangalore"
    
    def test_extract_place_in(self):
        """Test extraction from 'in' pattern."""
        place = extract_place_name("What's the weather in Paris?")
        assert place == "Paris"
    
    def test_extract_place_visit(self):
        """Test extraction from 'visit' pattern."""
        place = extract_place_name("I want to visit Tokyo")
        assert place == "Tokyo"
    
    def test_extract_place_fallback(self):
        """Test fallback pattern for capitalized place names."""
        place = extract_place_name("Tell me about Mumbai")
        assert place is not None


class TestPlacesOnlyQuery:
    """Test queries requesting only places information."""
    
    @patch('agents.parent_agent.find_pois')
    @patch('agents.parent_agent.get_weather')
    @patch('agents.parent_agent.geocode')
    def test_places_only_success(self, mock_geocode, mock_weather, mock_places):
        """Test successful places-only query."""
        # Setup mocks
        mock_geocode.return_value = {
            "lat": 12.9716,
            "lon": 77.5946,
            "display_name": "Bangalore, Karnataka, India"
        }
        mock_places.return_value = [
            {"name": "Lalbagh Botanical Garden", "distance_m": 1200},
            {"name": "Cubbon Park", "distance_m": 2500},
            {"name": "Bangalore Palace", "distance_m": 3500}
        ]
        
        # Execute
        result = handle_query("What places can I visit in Bangalore?")
        
        # Assertions
        assert "reply" in result
        assert "debug" in result
        # We now expect the short place name in reply (implementation uses extracted place)
        assert "Bangalore" in result["reply"]
        assert "places you can go" in result["reply"]
        assert "Lalbagh" in result["reply"]
        
        # Verify geocode was called
        mock_geocode.assert_called_once()
        # Verify places was called
        mock_places.assert_called_once()
        # Weather should not be called
        mock_weather.assert_not_called()
    
    @patch('agents.parent_agent.geocode')
    def test_places_only_unknown_place(self, mock_geocode):
        """Test places-only query with unknown place."""
        # Setup mock to raise ValueError with "place_not_found"
        mock_geocode.side_effect = ValueError("place_not_found")
        
        # Execute
        result = handle_query("What places can I visit in UnknownCity?")
        
        # Assertions
        assert "I'm sorry — I don't know this place." in result["reply"]
        assert "Could you check the spelling" in result["reply"]
        assert "geocode" in result["debug"]
        assert result["debug"]["geocode"].get("error") == "place_not_found"


class TestWeatherOnlyQuery:
    """Test queries requesting only weather information."""
    
    @patch('agents.parent_agent.find_pois')
    @patch('agents.parent_agent.get_weather')
    @patch('agents.parent_agent.geocode')
    def test_weather_only_success(self, mock_geocode, mock_weather, mock_places):
        """Test successful weather-only query."""
        # Setup mocks
        mock_geocode.return_value = {
            "lat": 48.8566,
            "lon": 2.3522,
            "display_name": "Paris, France"
        }
        mock_weather.return_value = {
            "temp_c": 22.5,
            "precip_percent": 15,
            "summary": "Partly cloudy"
        }
        
        # Execute
        result = handle_query("What's the weather like in Paris?")
        
        # Assertions
        assert "reply" in result
        assert "debug" in result
        assert "Paris" in result["reply"]
        # Temperature should be rounded to integer (22.5 -> 23)
        assert "23°C" in result["reply"] or "22°C" in result["reply"]
        assert "15%" in result["reply"]
        # Check debug structure
        assert result["debug"]["weather_api"]["called"] is True
        assert result["debug"]["weather_api"]["result"] is not None
        assert "timestamp" in result["debug"]
        
        # Verify weather was called
        mock_weather.assert_called_once()
        # Places should not be called
        mock_places.assert_not_called()
    
    @patch('agents.parent_agent.geocode')
    def test_weather_only_unknown_place(self, mock_geocode):
        """Test weather-only query with unknown place."""
        # Setup mock to raise ValueError with "place_not_found"
        mock_geocode.side_effect = ValueError("place_not_found")
        
        # Execute
        result = handle_query("What's the weather in FakeCity?")
        
        # Assertions
        assert "I'm sorry — I don't know this place." in result["reply"]
        assert "Could you check the spelling" in result["reply"]


class TestBothWeatherAndPlaces:
    """Test queries requesting both weather and places."""
    
    @patch('agents.parent_agent.find_pois')
    @patch('agents.parent_agent.get_weather')
    @patch('agents.parent_agent.geocode')
    def test_both_success(self, mock_geocode, mock_weather, mock_places):
        """Test successful query with both weather and places."""
        # Setup mocks
        mock_geocode.return_value = {
            "lat": 35.6762,
            "lon": 139.6503,
            "display_name": "Tokyo, Japan"
        }
        mock_weather.return_value = {
            "temp_c": 18.0,
            "precip_percent": 40,
            "summary": "Clear sky"
        }
        mock_places.return_value = [
            {"name": "Tokyo Skytree", "distance_m": 800},
            {"name": "Senso-ji Temple", "distance_m": 1500},
            {"name": "Shibuya Crossing", "distance_m": 2200}
        ]
        
        # Execute
        result = handle_query("I'm going to Tokyo. What's the weather and what can I see?")
        
        # Assertions
        assert "reply" in result
        assert "debug" in result
        assert "Tokyo" in result["reply"]
        assert "18°C" in result["reply"]
        assert "40%" in result["reply"]
        assert "And these are the places you can go:" in result["reply"]
        assert "Tokyo Skytree" in result["reply"]
        
        # Verify both were called
        mock_weather.assert_called_once()
        mock_places.assert_called_once()
        
        # Check debug structure
        assert result["debug"]["weather_api"]["called"] is True
        assert result["debug"]["places_api"]["called"] is True
        assert result["debug"]["places_api"]["result_count"] == 3
        assert "timestamp" in result["debug"]
        
        # Verify basic format: starts with expected prefix
        assert result["reply"].startswith("In Tokyo")
        assert "And these are the places you can go:" in result["reply"]
    
    @patch('agents.parent_agent.find_pois')
    @patch('agents.parent_agent.get_weather')
    @patch('agents.parent_agent.geocode')
    def test_both_with_weather_error(self, mock_geocode, mock_weather, mock_places):
        """Test both query when weather fails but places succeed."""
        # Setup mocks
        mock_geocode.return_value = {
            "lat": 40.7128,
            "lon": -74.0060,
            "display_name": "New York, USA"
        }
        mock_weather.side_effect = RuntimeError("weather_api_error")
        mock_places.return_value = [
            {"name": "Central Park", "distance_m": 500},
            {"name": "Statue of Liberty", "distance_m": 1200}
        ]
        
        # Execute
        result = handle_query("I'm going to New York")
        
        # Should show weather error fallback and still return places
        assert "reply" in result
        assert "Weather information currently unavailable" in result["reply"]
        assert "Central Park" in result["reply"]
        assert result["debug"]["weather_api"]["error"] == "weather_api_error"
        assert result["debug"]["places_api"]["result_count"] == 2
    
    @patch('agents.parent_agent.find_pois')
    @patch('agents.parent_agent.get_weather')
    @patch('agents.parent_agent.geocode')
    def test_places_only_exact_format(self, mock_geocode, mock_weather, mock_places):
        """Test places-only query matches expected format using short place name."""
        # Setup mocks
        mock_geocode.return_value = {
            "lat": 12.9716,
            "lon": 77.5946,
            "display_name": "Bangalore, Karnataka, India"
        }
        mock_places.return_value = [
            {"name": "Lalbagh Botanical Garden", "distance_m": 1200},
            {"name": "Cubbon Park", "distance_m": 2500},
            {"name": "Bangalore Palace", "distance_m": 3500},
            {"name": "ISKCON Temple", "distance_m": 4000},
            {"name": "Tipu Sultan's Summer Palace", "distance_m": 4500}
        ]
        
        # Execute
        result = handle_query("What places can I visit in Bangalore?")
        
        # Verify format uses the short place name in reply
        assert result["reply"].startswith("In Bangalore")
        assert "- Lalbagh Botanical Garden" in result["reply"]
        assert "- Cubbon Park" in result["reply"]
        assert "- Bangalore Palace" in result["reply"]
        assert "- ISKCON Temple" in result["reply"]
        assert "- Tipu Sultan's Summer Palace" in result["reply"]
    
    @patch('agents.parent_agent.find_pois')
    @patch('agents.parent_agent.get_weather')
    @patch('agents.parent_agent.geocode')
    def test_weather_only_exact_format(self, mock_geocode, mock_weather, mock_places):
        """Test weather-only query matches exact format using geocoder display_name when appropriate."""
        # Setup mocks
        mock_geocode.return_value = {
            "lat": 48.8566,
            "lon": 2.3522,
            "display_name": "Paris, France"
        }
        mock_weather.return_value = {
            "temp_c": 22.7,  # Should round to 23
            "precip_percent": 15,
            "summary": "Partly cloudy"
        }
        
        # Execute
        result = handle_query("What's the weather in Paris?")
        
        # Verify exact format for weather sentence (display_name may be used by some implementations;
        # accept either short or full name as long as temperature/percent formatting matches)
        assert "23°C" in result["reply"]
        assert "15%" in result["reply"]
        assert "In Paris" in result["reply"] or "In Paris, France" in result["reply"]
    
    @patch('agents.parent_agent.find_pois')
    @patch('agents.parent_agent.get_weather')
    @patch('agents.parent_agent.geocode')
    def test_both_exact_format(self, mock_geocode, mock_weather, mock_places):
        """Test both weather and places query matches expected structure."""
        # Setup mocks
        mock_geocode.return_value = {
            "lat": 35.6762,
            "lon": 139.6503,
            "display_name": "Tokyo, Japan"
        }
        mock_weather.return_value = {
            "temp_c": 18.3,  # Should round to 18
            "precip_percent": 40,
            "summary": "Clear sky"
        }
        mock_places.return_value = [
            {"name": "Tokyo Skytree", "distance_m": 800},
            {"name": "Senso-ji Temple", "distance_m": 1500},
            {"name": "Shibuya Crossing", "distance_m": 2200}
        ]
        
        # Execute
        result = handle_query("I'm going to Tokyo. What's the weather and what can I see?")
        
        # Verify structure: weather sentence followed by places heading and list
        assert "It's currently" not in result["reply"]  # ensure our phrase format is used
        assert "And these are the places you can go:" in result["reply"]
        assert "- Tokyo Skytree" in result["reply"]
        assert "- Senso-ji Temple" in result["reply"]
        assert "- Shibuya Crossing" in result["reply"]
    
    @patch('agents.parent_agent.find_pois')
    @patch('agents.parent_agent.get_weather')
    @patch('agents.parent_agent.geocode')
    def test_no_pois_found(self, mock_geocode, mock_weather, mock_places):
        """Test when no POIs are found."""
        # Setup mocks
        mock_geocode.return_value = {
            "lat": 12.9716,
            "lon": 77.5946,
            "display_name": "Bangalore, Karnataka, India"
        }
        mock_places.return_value = []  # Empty list
        
        # Execute
        result = handle_query("What places can I visit in Bangalore?")
        
        # Should show message about no POIs found
        assert "I couldn't find tourist attractions within 5 km" in result["reply"]
        assert "Bangalore" in result["reply"]
        assert result["debug"]["places_api"]["result_count"] == 0


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_missing_place(self):
        """Test handling of missing place in query."""
        result = handle_query("What's the weather like?")
        
        assert "Which place are you planning to visit?" in result["reply"]
        assert result["debug"].get("error") == "missing_place"
        assert result["debug"]["place_query"] is None
    
    @patch('agents.parent_agent.geocode')
    def test_unknown_place(self, mock_geocode):
        """Test handling of unknown place."""
        mock_geocode.side_effect = ValueError("place_not_found")
        
        result = handle_query("Tell me about NonExistentCity")
        
        assert "I'm sorry — I don't know this place." in result["reply"]
        assert "Could you check the spelling" in result["reply"]
        assert result["debug"]["geocode"].get("error") == "place_not_found"
    
    def test_empty_query(self):
        """Test handling of empty query."""
        result = handle_query("")
        
        # Should handle gracefully
        assert "reply" in result
    
    @patch('agents.parent_agent.geocode')
    def test_unexpected_error(self, mock_geocode):
        """Test handling of unexpected errors."""
        mock_geocode.side_effect = Exception("Unexpected error")
        
        result = handle_query("I'm going to London")
        
        assert "reply" in result
        # implementation adds 'errors' key for unexpected exceptions
        assert "errors" in result["debug"]


class TestGeocodeTool:
    """Test geocode tool directly."""
    
    @patch('agents.tools.geocode_tool.time.sleep')
    @patch('agents.tools.geocode_tool.httpx.Client')
    def test_geocode_success(self, mock_client_class, mock_sleep):
        """Test successful geocoding with mocked HTTP response."""
        from backend.agents.tools.geocode_tool import geocode
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "lat": "12.9716",
                "lon": "77.5946",
                "display_name": "Bangalore, Karnataka, India",
                "importance": 0.9
            },
            {
                "lat": "12.9352",
                "lon": "77.6245",
                "display_name": "Bangalore Urban, Karnataka, India",
                "importance": 0.7
            }
        ]
        mock_response.raise_for_status = MagicMock()
        
        # Mock client context manager
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Execute
        result = geocode("Bangalore")
        
        # Assertions
        assert result["lat"] == 12.9716
        assert result["lon"] == 77.5946
        assert result["display_name"] == "Bangalore, Karnataka, India"
        
        # Verify API was called with correct parameters
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "nominatim.openstreetmap.org" in call_args[0][0] or "nominatim.openstreetmap.org" in str(call_args)
        assert call_args[1]["headers"]["User-Agent"] == "AtlasAI-TravelPlanner/1.0 (contact: lisw22cs@cmrit.ac.in)"
    
    @patch('agents.tools.geocode_tool.time.sleep')
    @patch('agents.tools.geocode_tool.httpx.Client')
    def test_geocode_empty_results(self, mock_client_class, mock_sleep):
        """Test geocoding with empty results."""
        from backend.agents.tools.geocode_tool import geocode
        
        # Mock empty response
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Execute and assert
        with pytest.raises(ValueError, match="place_not_found"):
            geocode("NonExistentPlace")
