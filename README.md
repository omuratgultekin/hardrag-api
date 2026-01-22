# HardRAG API

**FastAPI Backend for HardRAG Validation Service**

REST API providing programmatic access to HardRAG guardrails and validation.

## Features

- ✅ **Validation Endpoints** - `/validate` for single, `/validate/batch` for multiple
- ✅ **Pydantic Models** - Type-safe request/response
- ✅ **API Documentation** - Auto-generated Swagger/ReDoc docs
- ✅ **Error Handling** - Comprehensive error responses
- ✅ **CORS Support** - Configurable cross-origin requests
- 🔜 **Authentication** - API key based (coming)
- 🔜 **Rate Limiting** - Request throttling (coming)
- 🔜 **Database** - PostgreSQL for persistence (coming)

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

Server starts at `http://localhost:8000`

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### POST /validate

Validate a single RAG output.

**Request:**
```json
{
  "query": "What is our Q4 revenue?",
  "retrieved_sources": ["Q4 revenue was $10 million"],
  "llm_output": "The Q4 revenue was $10 million",
  "guardrails": ["pii", "toxicity"],
  "config": {
    "pii": {"threshold": 0.7},
    "toxicity": {"threshold": 0.7, "use_ml": false}
  },
  "strict": false
}
```

**Response:**
```json
{
  "is_valid": true,
  "violations": [],
  "evaluation_scores": {
    "pii_free": 1.0,
    "toxicity": 0.0
  },
  "execution_time_ms": 45.2,
  "anonymized_output": null,
  "suggestions": [],
  "audit_trail": {
    "timestamp": "2026-01-23T00:00:00Z",
    "query": "What is our Q4 revenue?",
    "sources_count": 1,
    "output_length": 34,
    "guardrails_checked": ["pii", "toxicity"]
  }
}
```

### POST /validate/batch

Validate multiple outputs in batch.

**Request:**
```json
{
  "items": [
    {
      "query": "Query 1",
      "retrieved_sources": ["Source 1"],
      "llm_output": "Output 1",
      "guardrails": ["pii"]
    },
    {
      "query": "Query 2",
      "retrieved_sources": ["Source 2"],
      "llm_output": "Output 2",
      "guardrails": ["pii", "toxicity"]
    }
  ]
}
```

**Response:**
```json
{
  "total": 2,
  "valid": 2,
  "invalid": 0,
  "results": [
    {
      "is_valid": true,
      "violations": [],
      "evaluation_scores": {...},
      "execution_time_ms": 23.1
    },
    {
      "is_valid": true,
      "violations": [],
      "evaluation_scores": {...},
      "execution_time_ms": 34.5
    }
  ]
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-01-23T00:00:00Z"
}
```

## Usage Examples

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/validate",
    json={
        "query": "What is the revenue?",
        "retrieved_sources": ["Revenue was $10M"],
        "llm_output": "The revenue was $10M",
        "guardrails": ["pii", "toxicity"]
    }
)

result = response.json()
if result["is_valid"]:
    print("✓ Output is valid")
else:
    print(f"✗ Violations: {result['violations']}")
```

### cURL

```bash
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the revenue?",
    "retrieved_sources": ["Revenue was $10M"],
    "llm_output": "The revenue was $10M",
    "guardrails": ["pii"]
  }'
```

### JavaScript/TypeScript

```typescript
const response = await fetch('http://localhost:8000/validate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "What is the revenue?",
    retrieved_sources: ["Revenue was $10M"],
    llm_output: "The revenue was $10M",
    guardrails: ["pii", "toxicity"]
  })
});

const result = await response.json();
console.log(result.is_valid);
```

## Configuration

### Guardrails

Available guardrails:
- `pii` - PII detection 
- `toxicity` - Toxic content filtering
- `grounding` - Source grounding verification (requires DSPy config)

### Per-Guardrail Config

```json
{
  "config": {
    "pii": {
      "threshold": 0.7,
      "allow_list": ["@company.com"]
    },
    "toxicity": {
      "threshold": 0.7,
      "use_ml": false
    },
    "grounding": {
      "threshold": 0.8
    }
  }
}
```

## Development

### Run with auto-reload

```bash
uvicorn main:app --reload
```

### Run tests

```bash
pytest
```

## Deployment

### Docker

```bash
docker build -t hardrag-api .
docker run -p 8000:8000 hardrag-api
```

### Railway/Render

Deploy with one click (coming soon)

## Architecture

```
Client → FastAPI → HardRAGGuard → Guardrails → Response
                      ↓
                  PostgreSQL (audit logs)
                      ↓
                    Redis (caching)
```

## Coming Soon

- [ ] API key authentication
- [ ] Rate limiting
- [ ] PostgreSQL integration
- [ ] Async background processing
- [ ] Caching layer
- [ ] Metrics & monitoring
- [ ] Docker deployment
- [ ] Cloud deployment (Railway/Render)

## License

MIT
