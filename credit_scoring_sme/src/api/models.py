from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class TransactionInput(BaseModel):
    date: date
    amount: float
    transaction_type: str = Field(..., description="Category (e.g., 'Sales', 'Inventory', 'Utility')")
    channel: Optional[str] = "Online"

class AdSpendInput(BaseModel):
    date: date
    spend_amount: float
    clicks: Optional[int] = 0
    conversions: Optional[int] = 0

class LoanReadinessInput(BaseModel):
    loan_purpose: str = Field(..., description="Purpose of the loan")
    business_age: str = Field(..., description="Age of the business")
    repayment_confidence: str = Field(..., description="Confidence level in repayment")

class CreditDecisionRequest(BaseModel):
    business_id: str = Field(..., example="SME-001")
    transactions: List[TransactionInput]
    ad_spend: Optional[List[AdSpendInput]] = []
    loan_readiness: Optional[LoanReadinessInput] = None

class MetricsDetails(BaseModel):
    total_inflow: float
    avg_inflow: float
    txn_volatility: float
    ad_spend_total: float
    ad_roi: float
    # Add other metrics if needed

class CreditDecisionResponse(BaseModel):
    sme_id: str
    timestamp: str
    credit_score: int = Field(..., ge=0, le=100)
    risk_tier: str
    decision_summary: str
    probability_repay: float
    key_metrics: MetricsDetails

class HealthResponse(BaseModel):
    status: str
    model_version: str
    timestamp: str
