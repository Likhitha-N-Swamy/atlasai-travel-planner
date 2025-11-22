# AtlasAI – Multi-Agent Travel Planner
## Project Structure

```
AtlasAI – Multi-Agent Travel Planner/
│
├── backend/
│   ├── app.py                          # FastAPI application with POST /plan endpoint
│   ├── requirements.txt                # Python dependencies
│   │
│   ├── agents/
│   │   ├── __init__.py                 # Package init
│   │   ├── parent_agent.py            # ✅ Orchestrator agent (IMPLEMENTED)
│   │   │
│   │   └── tools/                      # Child agent tools (stubs)
│   │       ├── __init__.py
│   │       ├── geocode_tool.py         # ⏳ TODO: Nominatim API
│   │       ├── weather_agent_stub.py   # ⏳ TODO: Open-Meteo API
│   │       └── places_agent_stub.py    # ⏳ TODO: Overpass API
│   │
│   └── utils/
│       ├── __init__.py                 # Package init
│       ├── haversine.py                # Distance calculations
│       └── cache.py                    # Caching utilities
│
├── tests/
│   ├── __init__.py                     # Package init
│   └── test_parent_agent.py           # ✅ Test suite (skeleton)
│
├── Dockerfile                          # ✅ Docker configuration
├── .gitignore                          # ✅ Git ignore rules
├── README.md                           # ✅ Project documentation
├── NEXT_STEPS.md                       # ✅ Implementation checklist
└── PROJECT_STRUCTURE.md                # This file

```

## File Descriptions

### Core Application Files

- **`backend/app.py`**: FastAPI application
  - POST `/plan` endpoint
  - Request: `{"query": "I'm going to Bangalore..."}`
  - Response: `{"reply": "...", "debug": {...}}`

- **`backend/agents/parent_agent.py`**: Parent orchestrator agent
  - `handle_query(user_input: str)` - Main handler
  - `detect_intent(user_input: str)` - Detects weather/places intent
  - `extract_place_name(user_input: str)` - Extracts place from text
  - `format_response(...)` - Formats response per assignment specs

### Tool Stubs (To Be Implemented)

- **`backend/agents/tools/geocode_tool.py`**
  - Function: `geocode(query: str) -> Tuple[float, float, str]`
  - Currently raises `ValueError` for all queries
  - TODO: Implement Nominatim API integration

- **`backend/agents/tools/weather_agent_stub.py`**
  - Function: `get_weather(lat: float, lon: float) -> Dict`
  - Currently returns stub data: `{"temperature": 0.0, "rain_probability": 0}`
  - TODO: Implement Open-Meteo API integration

- **`backend/agents/tools/places_agent_stub.py`**
  - Function: `find_pois(lat: float, lon: float, radius: int = 5000) -> List[str]`
  - Currently returns empty list
  - TODO: Implement Overpass API integration

### Utilities

- **`backend/utils/haversine.py`**: Distance calculations between coordinates
- **`backend/utils/cache.py`**: In-memory caching with TTL support

### Testing

- **`tests/test_parent_agent.py`**: Comprehensive test suite
  - Intent detection tests
  - Place extraction tests
  - Places-only query tests
  - Weather-only query tests
  - Both weather and places tests
  - Error handling tests

### Configuration

- **`requirements.txt`**: Python dependencies
  - FastAPI, uvicorn
  - httpx, requests (for future API calls)
  - pytest (for testing)

- **`Dockerfile`**: Container configuration
  - Python 3.10-slim base
  - Exposes port 8000

- **`.gitignore`**: Git ignore patterns
  - Python cache files
  - Virtual environments
  - IDE files
  - Environment variables

## Implementation Status

### ✅ Completed
- [x] Project scaffold
- [x] Parent agent with intent detection
- [x] Place name extraction
- [x] Response formatting (matches assignment examples)
- [x] FastAPI app with POST /plan
- [x] Test skeleton
- [x] Documentation
- [x] Dockerfile
- [x] All __init__.py files

### ⏳ Pending (Next Steps)
- [ ] Geocode tool (Nominatim API)
- [ ] Weather agent (Open-Meteo API)
- [ ] Places agent (Overpass API)
- [ ] Integration tests with real APIs
- [ ] Production deployment configuration

## Quick Start

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python app.py
   ```

3. **Test the endpoint:**
   ```bash
   curl -X POST "http://localhost:8000/plan" \
     -H "Content-Type: application/json" \
     -d '{"query": "I'\''m going to Bangalore. What'\''s the weather like?"}'
   ```

4. **Run tests:**
   ```bash
   cd backend
   pytest tests/ -v
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
```

### Both Weather and Places
```
In Bangalore it's currently 28°C with a chance of 30% to rain.
And these are the places you can go:
- Lalbagh Botanical Garden
- Cubbon Park
- Bangalore Palace
```

### Unknown Place
```
I'm sorry — I don't know this place.
```

