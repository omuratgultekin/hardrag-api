"""
API Tests for HardRAG FastAPI Backend

Tests all endpoints with and without authentication.
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestPublicEndpoints:
    """Tests for public endpoints (no auth required)"""
    
    def test_root(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
    
    def test_validate_without_auth(self):
        """Test validation endpoint without authentication"""
        payload = {
            "query": "What is the revenue?",
            "retrieved_sources": ["Revenue was $10 million"],
            "llm_output": "The revenue was $10 million",
            "guardrails": ["pii", "toxicity"],
            "config": {
                "pii": {"threshold": 0.7},
                "toxicity": {"use_ml": False}
            }
        }
        
        response = client.post("/validate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "is_valid" in data
        assert "violations" in data
        assert "execution_time_ms" in data
        assert "audit_trail" in data
    
    def test_validate_with_pii(self):
        """Test that PII is detected"""
        payload = {
            "query": "What is the email?",
            "retrieved_sources": ["Email is john@example.com"],
            "llm_output": "The email is john@example.com",
            "guardrails": ["pii"]
        }
        
        response = client.post("/validate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_valid"] is False
        assert len(data["violations"]) > 0
        assert data["anonymized_output"] is not None
    
    def test_validate_batch_without_auth(self):
        """Test batch validation without authentication"""
        payload = {
            "items": [
                {
                    "query": "Query 1",
                    "retrieved_sources": ["Source 1"],
                    "llm_output": "Output 1",
                    "guardrails": ["toxicity"],
                    "config": {"toxicity": {"use_ml": False}}
                },
                {
                    "query": "Query 2",
                    "retrieved_sources": ["Source 2"],
                    "llm_output": "Output 2",
                    "guardrails": ["toxicity"],
                    "config": {"toxicity": {"use_ml": False}}
                }
            ]
        }
        
        response = client.post("/validate/batch", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 2
        assert "valid" in data
        assert "invalid" in data
        assert len(data["results"]) == 2


class TestValidationLogic:
    """Tests for validation logic"""
    
    def test_toxicity_detection(self):
        """Test toxicity detection"""
        payload = {
            "query": "Test",
            "retrieved_sources": ["Context"],
            "llm_output": "You are stupid and dumb",
            "guardrails": ["toxicity"],
            "config": {"toxicity": {"use_ml": False}}
        }
        
        response = client.post("/validate", json=payload)
        data = response.json()
        
        # Should detect toxicity
        assert data["is_valid"] is False
        assert len(data["violations"]) > 0
    
    def test_clean_output(self):
        """Test clean output passes"""
        payload = {
            "query": "What is 2+2?",
            "retrieved_sources": ["2 plus 2 equals 4"],
            "llm_output": "2 plus 2 equals 4",
            "guardrails": ["pii", "toxicity"],
            "config": {"toxicity": {"use_ml": False}}
        }
        
        response = client.post("/validate", json=payload)
        data = response.json()
        
        assert data["is_valid"] is True
        assert len(data["violations"]) == 0
    
    def test_strict_mode(self):
        """Test strict mode stops on first violation"""
        payload = {
            "query": "Test",
            "retrieved_sources": ["Context"],
            "llm_output": "Email john@test.com",
            "guardrails": ["pii", "toxicity"],
            "strict": True
        }
        
        response = client.post("/validate", json=payload)
        data = response.json()
        
        # Should have violations but might stop early
        assert data["is_valid"] is False
        assert len(data["violations"]) >= 1


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_invalid_guardrail(self):
        """Test with invalid guardrail name"""
        payload = {
            "query": "Test",
            "retrieved_sources": ["Context"],
            "llm_output": "Output",
            "guardrails": ["invalid_guardrail"]
        }
        
        # Should handle gracefully
        response = client.post("/validate", json=payload)
        # Might succeed but skip unknown guardrails
        assert response.status_code in [200, 422]
    
    def test_missing_required_fields(self):
        """Test with missing required fields"""
        payload = {
            "query": "Test"
            # Missing retrieved_sources and llm_output
        }
        
        response = client.post("/validate", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_empty_sources(self):
        """Test with empty sources"""
        payload = {
            "query": "Test",
            "retrieved_sources": [],
            "llm_output": "Output",
            "guardrails": ["pii"]
        }
        
        response = client.post("/validate", json=payload)
        # Should handle empty sources
        assert response.status_code == 200


class TestProtectedEndpoints:
    """Tests for protected endpoints (require auth)"""
    
    def test_me_without_auth(self):
        """Test /api/me without authentication"""
        response = client.get("/api/me")
        assert response.status_code == 401
    
    def test_stats_without_auth(self):
        """Test /api/stats without authentication"""
        response = client.get("/api/stats")
        assert response.status_code == 401
    
    def test_history_without_auth(self):
        """Test /api/history without authentication"""
        response = client.get("/api/history")
        assert response.status_code == 401
    
    # Note: Testing with auth requires Supabase setup
    # Add these tests after Supabase is configured
    
    def test_me_with_invalid_token(self):
        """Test /api/me with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/me", headers=headers)
        assert response.status_code == 401


class TestAPIDocumentation:
    """Tests for API documentation endpoints"""
    
    def test_swagger_docs(self):
        """Test Swagger UI is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc(self):
        """Test ReDoc is accessible"""
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_openapi_schema(self):
        """Test OpenAPI schema is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
