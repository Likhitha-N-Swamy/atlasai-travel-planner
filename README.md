# AtlasAI – Multi-Agent Travel Planner

A multi-agent system for intelligent travel planning that provides weather information and points of interest (POIs) for destinations around the world.

## Overview

AtlasAI is a multi-agent orchestration system that coordinates specialized child agents to answer travel-related queries. The system can:

- **Detect user intent** (weather, places, or both)
- **Geocode place names** to coordinates
- **Fetch current weather** conditions
- **Find points of interest** near a location
- **Format responses** in a user-friendly way

## Architecture

```
┌─────────────────┐
│   FastAPI App   │  (app.py)
│   POST /plan    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Parent Agent   │  (parent_agent.py)
│  Orchestrator   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│Geocode │ │Weather │ ┌─────────┐
│  Tool  │ │ Agent  │ │ Places  │
└────────┘ └────────┘ │  Agent  │
                      └─────────┘
```

### Components

1. **Parent Agent** (`backend/agents/parent_agent.py`)
   - Orchestrates the entire query processing pipeline
   - Detects user intent (weather/places/both)
   - Extracts place names from natural language
   - Coordinates child agents
   - Formats final responses

2. **Child Agents** (stubs, to be implemented)
   - **Geocode Tool**: Converts place names to coordinates (Nominatim API)
   - **Weather Agent**: Fetches current weather (Open-Meteo API)
   - **Places Agent**: Finds points of interest (Overpass API)

3. **Utilities**
   - `haversine.py`: Distance calculations
   - `cache.py`: Response caching

## Project Structure

```
AtlasAI – Multi-Agent Travel Planner/
├── backend/
│   ├── app.py                      # FastAPI application
│   ├── agents/
│   │   ├── parent_agent.py         # Orchestrator agent
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── geocode_tool.py     # Geocoding (stub)
│   │       ├── weather_agent_stub.py  # Weather (stub)
│   │       └── places_agent_stub.py   # Places (stub)
│   ├── utils/
│   │   ├── haversine.py            # Distance calculations
│   │   └── cache.py                # Caching utilities
│   └── requirements.txt
├── tests/
│   └── test_parent_agent.py        # Test suite
├── Dockerfile
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd "AtlasAI – Multi-Agent Travel Planner"
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Running Locally

1. Start the FastAPI server:
```bash
cd backend
python app.py
```

Or using uvicorn directly:
```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

2. The API will be available at:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

3. Test the endpoint:
```bash
curl -X POST "http://localhost:8000/plan" \
  -H "Content-Type: application/json" \
  -d '{"query": "I'\''m going to Bangalore. What'\''s the weather like?"}'
```

### Running with Docker

1. Build the Docker image:
```bash
docker build -t atlasai .
```

2. Run the container:
```bash
docker run -p 8000:8000 atlasai
```

## API Endpoints

### POST /plan

Process a travel planning query.

**Request:**
```json
{
  "query": "I'm going to Bangalore. What's the weather like?"
}
```

**Response:**
```json
{
  "reply": "In Bangalore it's currently 28°C with a chance of 30% to rain.",
  "debug": {
    "input": "I'm going to Bangalore. What's the weather like?",
    "intent": {
      "wants_weather": true,
      "wants_places": false
    },
    "geocode": {
      "query": "Bangalore",
      "result": {
        "lat": 12.9716,
        "lon": 77.5946,
        "display_name": "Bangalore, Karnataka, India"
      }
    },
    "weather": {
      "temperature": 28.0,
      "rain_probability": 30
    },
    "places": {},
    "errors": []
  }
}
```

## Response Format Examples

### Weather Only
```
In Bangalore it's currently 28°C with a chance of 30% to rain.
```

### Places Only
```
In Bangalore these are the places you can go:
- Lalbagh Botanical Garden
- Cubbon Park
- Bangalore Palace
- ISKCON Temple
```

### Both Weather and Places
```
In Bangalore it's currently 28°C with a chance of 30% to rain.
And these are the places you can go:
- Lalbagh Botanical Garden
- Cubbon Park
- Bangalore Palace
```

## Next Steps: API Implementations

The following child agent tools are currently stubs and need to be implemented:

### 1. Geocode Tool (Nominatim API)

**File:** `backend/agents/tools/geocode_tool.py`

**Implementation:**
- Use Nominatim API: `https://nominatim.openstreetmap.org/search`
- Format: `?q=<query>&format=json&limit=1`
- Extract `lat`, `lon`, `display_name` from response
- Handle rate limiting (1 request/second recommended)
- Cache results to reduce API calls

**Reference:** https://nominatim.org/release-docs/develop/api/Search/

### 2. Weather Agent (Open-Meteo API)

**File:** `backend/agents/tools/weather_agent_stub.py`

**Implementation:**
- Use Open-Meteo API: `https://api.open-meteo.com/v1/forecast`
- Endpoint: `?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation_probability`
- Parse `current.temperature_2m` for temperature
- Parse `current.precipitation_probability` for rain probability
- Handle API errors gracefully

**Reference:** https://open-meteo.com/en/docs

### 3. Places Agent (Overpass API)

**File:** `backend/agents/tools/places_agent_stub.py`

**Implementation:**
- Use Overpass API: `https://overpass-api.de/api/interpreter`
- Query for tourist attractions, restaurants, museums, parks, etc.
- Overpass QL example:
  ```
  [out:json];
  (node[~"^(tourism|amenity|leisure)"~"."](around:5000,{lat},{lon}););
  out;
  ```
- Extract `name` tags from results
- Limit to top 10-15 results
- Filter duplicates

**Reference:** https://wiki.openstreetmap.org/wiki/Overpass_API

## Testing

Run tests with pytest:

```bash
cd backend
pytest tests/ -v
```

## Development

### Code Style

- Use type hints for all functions
- Follow PEP 8 style guide
- Use docstrings for all modules, classes, and functions
- Keep functions modular and focused

### Logging

The system uses Python's `logging` module. Debug information is included in API responses for development purposes.

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

