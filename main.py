"""
HardRAG API - FastAPI Backend

REST API for HardRAG validation service.
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import time
import logging

# Import from hardrag-core
try:
    from hardrag import HardRAGGuard
except ImportError:
    # For development, add parent path
    import sys
    sys.path.append('../hardrag-core')
    from hardrag import HardRAGGuard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HardRAG API",
    description="Evaluation-First Control Layer for Enterprise RAG Systems",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request/Response Models
# ============================================================================

class ValidationRequest(BaseModel):
    """Request model for validation endpoint"""
    query: str = Field(..., description="Original user query")
    retrieved_sources: List[str] = Field(..., description="Retrieved source chunks")
    llm_output: str = Field(..., description="LLM generated output")
    guardrails: List[str] = Field(
        default=["pii", "toxicity"],
        description="Guardrails to enable (pii, toxicity, grounding)"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional guardrail configuration"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata for audit trail"
    )
    strict: bool = Field(
        default=False,
        description="Strict mode: stop on first violation"
    )

    class Config:
        schema_extra = {
            "example": {
                "query": "What is our Q4 revenue?",
                "retrieved_sources": ["Q4 revenue was $10 million"],
                "llm_output": "The Q4 revenue was $10 million",
                "guardrails": ["pii", "toxicity"],
                "config": {
                    "pii": {"threshold": 0.7},
                    "toxicity": {"threshold": 0.7, "use_ml": False}
                },
                "strict": False
            }
        }


class BatchValidationRequest(BaseModel):
    """Request model for batch validation"""
    items: List[ValidationRequest] = Field(..., description="List of validation requests")

    class Config:
        schema_extra = {
            "example": {
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
        }


class ValidationResponse(BaseModel):
    """Response model for validation"""
    is_valid: bool = Field(..., description="Overall validation result")
    violations: List[Dict[str, Any]] = Field(..., description="List of violations")
    evaluation_scores: Dict[str, float] = Field(..., description="Evaluation scores")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    anonymized_output: Optional[str] = Field(None, description="Anonymized output if PII detected")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    audit_trail: Dict[str, Any] = Field(..., description="Audit trail")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "HardRAG API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/validate", response_model=ValidationResponse, tags=["Validation"])
async def validate_output(request: ValidationRequest):
    """
    Validate a single RAG output against configured guardrails.
    
    This endpoint runs the specified guardrails on the LLM output and returns
    validation results including violations, scores, and suggestions.
    """
    start_time = time.time()
    
    try:
        # Initialize guard
        guard = HardRAGGuard(
            guardrails=request.guardrails,
            config=request.config or {},
            strict=request.strict
        )
        
        # Validate
        result = guard.validate(
            query=request.query,
            retrieved_sources=request.retrieved_sources,
            llm_output=request.llm_output,
            metadata=request.metadata
        )
        
        # Build response
        response = ValidationResponse(
            is_valid=result.is_valid,
            violations=result.violations,
            evaluation_scores=result.evaluation_scores,
            execution_time_ms=result.execution_time_ms,
            anonymized_output=result.anonymized_output,
            suggestions=result.suggestions,
            audit_trail=result.audit_trail
        )
        
        logger.info(f"Validation completed in {result.execution_time_ms:.2f}ms - Valid: {result.is_valid}")
        
        return response
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@app.post("/validate/batch", tags=["Validation"])
async def validate_batch(request: BatchValidationRequest):
    """
    Validate multiple RAG outputs in batch.
    
    Processes multiple validation requests and returns results for each.
    """
    try:
        results = []
        
        for item in request.items:
            guard = HardRAGGuard(
                guardrails=item.guardrails,
                config=item.config or {},
                strict=item.strict
            )
            
            result = guard.validate(
                query=item.query,
                retrieved_sources=item.retrieved_sources,
                llm_output=item.llm_output,
                metadata=item.metadata
            )
            
            results.append({
                "is_valid": result.is_valid,
                "violations": result.violations,
                "evaluation_scores": result.evaluation_scores,
                "execution_time_ms": result.execution_time_ms,
                "anonymized_output": result.anonymized_output,
                "suggestions": result.suggestions
            })
        
        return {
            "total": len(results),
            "valid": sum(1 for r in results if r["is_valid"]),
            "invalid": sum(1 for r in results if not r["is_valid"]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch validation failed: {str(e)}"
        )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("HardRAG API starting up...")
    logger.info("API documentation available at /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("HardRAG API shutting down...")


# ============================================================================
# Main (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
