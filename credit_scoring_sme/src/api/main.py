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
    try:
        # Load versioned model v1 by default
        engine = CreditDecisionEngine(model_version='v1')
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model during startup: {e}")
        # We don't raise here to allow the instance to stay up for debugging /health
        # but subsequent /credit-decision calls will handle engine being None

@app.get("/health")
def health_check():
    return {
        "status": "healthy" if engine is not None else "degraded",
        "model_version": "v1",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("RENDER", "local")
    }

@app.post("/credit-decision", response_model=CreditDecisionResponse)
def get_credit_decision(request: CreditDecisionRequest):
    if engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded or failed to initialize")
    
    # Transform Pydantic models to dict for the decision engine
    input_data = {
        "transactions": [t.dict() for t in request.transactions],
        "ad_spend": [a.dict() for a in request.ad_spend]
    }
    
    try:
        result = engine.credit_decision(input_data)
        result['sme_id'] = request.business_id
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Standard Render/Cloud port handling
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
