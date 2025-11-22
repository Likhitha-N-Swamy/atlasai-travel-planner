# Next Steps Checklist

## ✅ Completed (Scaffold + Parent Agent)

- [x] Project structure created
- [x] Parent agent implemented with intent detection
- [x] Place name extraction
- [x] Response formatting (weather-only, places-only, both)
- [x] FastAPI app with POST /plan endpoint
- [x] Test skeleton created
- [x] Documentation (README.md)
- [x] Dockerfile for containerization
- [x] Requirements.txt with dependencies

## 🔨 To Implement Next

### 1. Geocode Tool (Nominatim API) ✅ COMPLETED
**File:** `backend/agents/tools/geocode_tool.py`

**Implementation Status:**
- [x] Implement HTTP request to Nominatim API
- [x] Parse JSON response
- [x] Extract lat, lon, display_name
- [x] Handle rate limiting (1 req/sec with sleep)
- [x] Best match selection based on importance
- [x] Handle API errors gracefully
- [x] Update tests to use real geocoding

**API Details:**
- Endpoint: `https://nominatim.openstreetmap.org/search`
- Parameters: `?q=<query>&format=json&limit=5&addressdetails=1`
- Response: Array with `lat`, `lon`, `display_name`, `importance`
- Returns: `{"lat": float, "lon": float, "display_name": str}`

**Reference:** https://nominatim.org/release-docs/develop/api/Search/

---

### 2. Weather Agent (Open-Meteo API) ✅ COMPLETED
**File:** `backend/agents/tools/weather_agent_stub.py`

**Implementation Status:**
- [x] Implement HTTP request to Open-Meteo API
- [x] Parse JSON response
- [x] Extract `current_weather.temperature`
- [x] Extract `hourly.precipitation_probability` (closest hour)
- [x] Map weathercode to human-readable summary
- [x] Handle API errors gracefully
- [x] Update tests with comprehensive test suite

**API Details:**
- Endpoint: `https://api.open-meteo.com/v1/forecast`
- Parameters: `?latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation_probability&timezone=auto`
- Response: `current_weather.temperature`, `current_weather.weathercode`, `hourly.precipitation_probability`
- Returns: `{"temp_c": float, "precip_percent": int, "summary": str}`

**Reference:** https://open-meteo.com/en/docs

---

### 3. Places Agent (Overpass API) ✅ COMPLETED
**File:** `backend/agents/tools/places_agent_stub.py`

**Implementation Status:**
- [x] Implement HTTP request to Overpass API (POST)
- [x] Construct Overpass QL query with tourism, historic, parks, museums
- [x] Parse JSON response
- [x] Extract POI names and coordinates from results
- [x] Calculate distances using Haversine formula
- [x] Filter duplicates (case-insensitive)
- [x] Sort by priority (tourism > historic > parks/museums) and distance
- [x] Limit to max_results (default: 5)
- [x] Handle API errors gracefully
- [x] Rate limiting retry logic (429 handling)
- [x] Add caching (24-hour TTL)
- [x] Update tests with comprehensive test suite

**API Details:**
- Endpoint: `https://overpass-api.de/api/interpreter` (POST)
- Query format (Overpass QL):
  ```
  [out:json][timeout:25];
  (
    node(around:{radius},{lat},{lon})[tourism];
    node(around:{radius},{lat},{lon})[historic];
    node(around:{radius},{lat},{lon})[leisure=park];
    node(around:{radius},{lat},{lon})[amenity=museum];
    way(around:{radius},{lat},{lon})[tourism];
    way(around:{radius},{lat},{lon})[historic];
    relation(around:{radius},{lat},{lon})[tourism];
  );
  out center;
  ```
- Response: JSON with `elements` array containing nodes/ways/relations with `tags.name`

**Features:**
- Returns list of dicts: `[{"name": str, "distance_m": int}, ...]`
- Caching with 24-hour TTL to reduce API load
- Rate limiting handling with retry logic (1s wait, then broader radius)
- Priority-based sorting (tourism > historic > parks/museums)

**Reference:** https://wiki.openstreetmap.org/wiki/Overpass_API

---

## 🧪 Testing

- [ ] Run existing tests: `pytest tests/ -v`
- [ ] Add integration tests with real API calls (optional, use mocks for CI)
- [ ] Test error handling for each API
- [ ] Test rate limiting behavior
- [ ] Test caching functionality

---

## 🚀 Deployment

- [ ] Set up environment variables for API keys (if needed)
- [ ] Configure CORS properly (currently allows all origins)
- [ ] Add rate limiting middleware
- [ ] Set up logging to file
- [ ] Add health check monitoring
- [ ] Deploy to cloud platform (AWS, GCP, Azure, etc.)

---

## 📝 Documentation

- [ ] Add API documentation examples
- [ ] Document environment variables
- [ ] Add deployment guide
- [ ] Create architecture diagram
- [ ] Add troubleshooting guide

---

## 🔒 Security & Performance

- [ ] Add input validation and sanitization
- [ ] Implement request rate limiting
- [ ] Add API key management (if required)
- [ ] Optimize caching strategy
- [ ] Add monitoring and alerting
- [ ] Performance testing under load

---

## 📋 Quick Start for Next Developer

1. **Implement Geocode Tool:**
   ```python
   # In backend/agents/tools/geocode_tool.py
   import httpx
   from utils.cache import cached
   
   @cached(ttl=86400)  # Cache for 24 hours
   def geocode(query: str) -> Tuple[float, float, str]:
       # Implementation here
   ```

2. **Implement Weather Agent:**
   ```python
   # In backend/agents/tools/weather_agent_stub.py
   import httpx
   from utils.cache import cached
   
   @cached(ttl=1800)  # Cache for 30 minutes
   def get_weather(lat: float, lon: float) -> Dict[str, any]:
       # Implementation here
   ```

3. **Implement Places Agent:**
   ```python
   # In backend/agents/tools/places_agent_stub.py
   import httpx
   from utils.cache import cached
   
   @cached(ttl=86400)  # Cache for 24 hours
   def find_pois(lat: float, lon: float, radius: int = 5000) -> List[str]:
       # Implementation here
   ```

4. **Test each implementation:**
   ```bash
   cd backend
   pytest tests/test_parent_agent.py -v
   ```

5. **Run the server and test:**
   ```bash
   python app.py
   curl -X POST "http://localhost:8000/plan" \
     -H "Content-Type: application/json" \
     -d '{"query": "I'\''m going to Bangalore. What'\''s the weather like?"}'
   ```

