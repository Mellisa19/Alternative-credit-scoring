from fastapi import FastAPI, HTTPException, Request, Form, Depends, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, date, timedelta
from src.api.models import CreditDecisionRequest, CreditDecisionResponse, HealthResponse, TransactionInput, AdSpendInput
from src.decision_engine import CreditDecisionEngine
from src.api.auth import get_current_user, verify_password, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from src.api.database import init_db, get_user_by_email, create_user, save_assessment, get_latest_assessments, update_user_profile
import uvicorn
import os
import json
from pathlib import Path

app = FastAPI(
    title="SME Credit Scoring API",
    description="REST API to predict SME credit worthiness using alternative data.",
    version="1.0.0"
)

# Setup Templates and Static Files - Render Compatible Absolute Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Expects structure:
# credit_scoring_sme/
#   src/
#     api/
#       main.py
#   static/
#   templates/

# Ensure directories exist
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"

print(f"DEBUG: BASE_DIR: {BASE_DIR}")
print(f"DEBUG: templates_dir: {templates_dir} (Exists: {templates_dir.exists()})")
print(f"DEBUG: static_dir: {static_dir} (Exists: {static_dir.exists()})")
if not templates_dir.exists():
    print(f"WARNING: Templates directory NOT found at {templates_dir}")
    # Fallback to current directory for local dev if structure differs
    if Path("templates").exists():
        templates_dir = Path("templates").resolve()
        print(f"DEBUG: Fallback templates_dir: {templates_dir}")

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Global engine instance to load model at startup
engine = None

@app.get("/debug-info")
async def debug_info():
    return {
        "base_dir": str(BASE_DIR),
        "templates_dir": str(templates_dir),
        "templates_exists": templates_dir.exists(),
        "static_dir": str(static_dir),
        "static_exists": static_dir.exists(),
        "cwd": os.getcwd(),
        "files_in_templates": [f.name for f in templates_dir.iterdir()] if templates_dir.exists() else []
    }

@app.on_event("startup")
def startup_event():
    global engine
    # Initialize Database
    init_db()
    try:
        # Load versioned model v1 by default
        engine = CreditDecisionEngine(model_version='v1')
        print("Model and Database loaded successfully.")
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

# --- Web Routes ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/join-vision", response_class=HTMLResponse)
async def join_vision(request: Request):
    try:
        return templates.TemplateResponse("join_vision.html", {"request": request})
    except Exception as e:
        # Fallback friendly error or return a simple error dict
        return HTMLResponse(content=f"<h1>Something went wrong loading the vision page.</h1><p>Error: {str(e)}</p><p>Check <a href='/debug-info'>/debug-info</a></p>", status_code=500)

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    try:
        return templates.TemplateResponse("signup.html", {"request": request})
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading signup page.</h1><p>Error: {str(e)}</p><p>Check <a href='/debug-info'>/debug-info</a></p>", status_code=500)

@app.post("/signup")
async def signup_process(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    if get_user_by_email(email):
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Email already registered."
        })
    
    hashed_pwd = get_password_hash(password)
    user_id = create_user(email, hashed_pwd)
    
    if not user_id:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Failed to create account. Please try again."
        })
    
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_process(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...)
):
    user = get_user_by_email(email)
    if not user or not verify_password(password, user["hashed_password"]):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password."
        })
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["id"])}, expires_delta=access_token_expires
    )
    
    redirect_resp = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    redirect_resp.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True, samesite="lax"
    )
    return redirect_resp

@app.get("/logout")
async def logout(response: Response):
    resp = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie("access_token")
    return resp

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Fetch recent history for momentum
    latest = get_latest_assessments(user["id"], limit=2)
    current_snapshot = latest[0] if len(latest) > 0 else None
    previous_snapshot = latest[1] if len(latest) > 1 else None
    
    momentum = "Stable"
    if current_snapshot and previous_snapshot:
        if current_snapshot["score"] > previous_snapshot["score"]:
            momentum = "Improved"
        elif current_snapshot["score"] < previous_snapshot["score"]:
            momentum = "Declined"

    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": user, 
        "snapshot": current_snapshot,
        "momentum": momentum
    })

@app.get("/assessment", response_class=HTMLResponse)
async def assessment_form(request: Request, user=Depends(get_current_user)):
    # Pre-fill logic for members
    inputs = None
    if user:
        latest = get_latest_assessments(user["id"], limit=1)
        if latest:
            inputs = json.loads(latest[0]["inputs_json"])
            # Add profile context to inputs for pre-filling Phase IV
            inputs["loan_purpose"] = user["loan_purpose"]
            inputs["business_age"] = user["business_age"]
            inputs["repayment_confidence"] = user["repayment_confidence"]
            
    return templates.TemplateResponse("assessment.html", {
        "request": request, 
        "user": user,
        "inputs": inputs # For pre-filling
    })

@app.post("/assessment", response_class=HTMLResponse)
async def process_assessment(
    request: Request,
    daily_revenue: float = Form(...),
    daily_expenses: float = Form(...),
    ad_spend: float = Form(...),
    num_transactions: int = Form(...),
    loan_purpose: str = Form(None),
    business_age: str = Form(None),
    repayment_confidence: str = Form(None),
    user=Depends(get_current_user)
):
    if engine is None:
        return templates.TemplateResponse("assessment.html", {
            "request": request,
            "error": "Model not loaded or failed to initialize. Please try again later."
        })
    
    # Map simplified inputs to CreditDecisionEngine format
    # We simulate a balanced mix of sales and expenses to meet num_transactions
    transactions = []
    num_sales = max(1, num_transactions // 2)
    num_expenses = max(1, num_transactions - num_sales)
    
    avg_sale = daily_revenue / num_sales
    avg_expense = daily_expenses / num_expenses
    
    for _ in range(num_sales):
        transactions.append(TransactionInput(
            date=date.today(),
            amount=avg_sale,
            transaction_type="Sales"
        ))
    
    for _ in range(num_expenses):
        transactions.append(TransactionInput(
            date=date.today(),
            amount=-avg_expense,
            transaction_type="Expense"
        ))
        
    ad_spend_list = [AdSpendInput(
        date=date.today(),
        spend_amount=ad_spend,
        clicks=int(ad_spend * 0.1), # Placeholder logic for clicks
        conversions=int(ad_spend * 0.01) # Placeholder logic for conversions
    )]
    
    # Pack into the internal request format
    api_request = CreditDecisionRequest(
        business_id="WEB-APP-USER",
        transactions=transactions,
        ad_spend=ad_spend_list
    )
    
    # Call internal API logic
    input_data = {
        "transactions": [t.dict() for t in api_request.transactions],
        "ad_spend": [a.dict() for a in api_request.ad_spend]
    }
    
    try:
        # Extract Loan Readiness Context ONLY if user is logged in
        loan_readiness = None
        if user:
            loan_readiness = {
                "loan_purpose": loan_purpose,
                "business_age": business_age,
                "repayment_confidence": repayment_confidence
            }
        
        result = engine.credit_decision(input_data, loan_readiness=loan_readiness)
        
        # --- LENDER REASONING ENGINE (Phase IV) ---
        # The engine now returns the summary with lender context baked in if provided.
        # We also want to extract the lender_insight part for the UI display if it exists.
        lender_insight = ""
        if "[Lender Perspective: " in result["decision_summary"]:
            lender_insight = result["decision_summary"].split("[Lender Perspective: ")[1].rstrip("]")

        # PERSISTENCE: Save for members
        if user:
            # Save the point-in-time assessment
            save_assessment(
                user_id=user["id"],
                score=result["credit_score"],
                risk_tier=result["risk_tier"],
                summary=result["decision_summary"],
                inputs={
                    "daily_revenue": daily_revenue,
                    "daily_expenses": daily_expenses,
                    "ad_spend": ad_spend,
                    "num_transactions": num_transactions
                },
                loan_purpose=loan_purpose,
                business_age=business_age,
                repayment_confidence=repayment_confidence
            )
            # Update core user profile for future pre-filling
            update_user_profile(user["id"], loan_purpose, business_age, repayment_confidence)

        return templates.TemplateResponse("assessment.html", {
            "request": request,
            "result": result,
            "user": user,
            "lender_insight": lender_insight, # Explicitly pass but also baked into summary
            "inputs": {
                "daily_revenue": daily_revenue,
                "daily_expenses": daily_expenses,
                "ad_spend": ad_spend,
                "num_transactions": num_transactions,
                "loan_purpose": loan_purpose,
                "business_age": business_age,
                "repayment_confidence": repayment_confidence
            }
        })
    except Exception as e:
        return templates.TemplateResponse("assessment.html", {
            "request": request,
            "error": f"Assessment Error: {str(e)}"
        })

# --- Existing API Routes ---

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
