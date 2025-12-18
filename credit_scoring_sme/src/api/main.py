from fastapi import FastAPI, HTTPException
from datetime import datetime
from src.api.models import CreditDecisionRequest, CreditDecisionResponse, HealthResponse
from src.decision_engine import CreditDecisionEngine
import uvicorn
import os

app = FastAPI(
    title="SME Credit Scoring API",
    description="REST API to predict SME credit worthiness using alternative data.",
    version="1.0.0"
)

# Global engine instance to load model at startup
engine = None

@app.on_event("startup")
def startup_event():
    global engine
    # Load versioned model v1 by default
    engine = CreditDecisionEngine(model_version='v1')

@app.get("/health", response_model=HealthResponse)
def health_check():
    return {
        "status": "healthy",
        "model_version": "v1",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/credit-decision", response_model=CreditDecisionResponse)
def get_credit_decision(request: CreditDecisionRequest):
    if not engine:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Transform Pydantic models to dict for the decision engine
    input_data = {
        "transactions": [t.dict() for t in request.transactions],
        "ad_spend": [a.dict() for a in request.ad_spend]
    }
    
    try:
        # Business ID is handled in the engine's internal logic
        # but the request contains it for traceability
        result = engine.credit_decision(input_data)
        
        # Override SME ID from request if provided
        result['sme_id'] = request.business_id
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
