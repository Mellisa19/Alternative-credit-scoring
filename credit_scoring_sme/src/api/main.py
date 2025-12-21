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
import secrets
from collections import OrderedDict
import time

app = FastAPI(
    title="SME Credit Scoring API",
    description="REST API to predict SME credit worthiness using alternative data.",
    version="1.0.0"
)

# Global exception handler to catch all errors gracefully
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to prevent unhandled errors from crashing the app.
    Returns user-friendly error pages instead of 500 errors.
    """
    print(f"GLOBAL ERROR HANDLER: {type(exc).__name__}: {str(exc)}")
    
    # If it's an HTML request, return a friendly error page
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            "error.html" if (BASE_DIR / "templates" / "error.html").exists() else "index.html",
            {"request": request, "error": "An unexpected error occurred. Please try again."},
            status_code=500
        )
    
    # Otherwise return JSON error for API calls
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
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

# Simple in-memory cache for assessment results (expires after 10 min)
results_cache = OrderedDict()
CACHE_MAX_ITEMS = 100
CACHE_EXPIRY_SECONDS = 600  # 10 minutes

def store_result(result_data):
    """Store result with unique ID and return the ID"""
    result_id = secrets.token_urlsafe(16)
    timestamp = time.time()
    
    # Clean old entries
    current_time = time.time()
    expired_keys = [k for k, v in results_cache.items() if current_time - v['timestamp'] > CACHE_EXPIRY_SECONDS]
    for k in expired_keys:
        del results_cache[k]
    
    # Limit cache size
    while len(results_cache) >= CACHE_MAX_ITEMS:
        results_cache.popitem(last=False)
    
    results_cache[result_id] = {'data': result_data, 'timestamp': timestamp}
    return result_id

def get_result(result_id):
    """Retrieve and remove result from cache"""
    entry = results_cache.pop(result_id, None)
    if entry and (time.time() - entry['timestamp']) < CACHE_EXPIRY_SECONDS:
        return entry['data']
    return None

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
    # Initialize Database with error handling
    try:
        init_db()
    except Exception as e:
        print(f"CRITICAL: Database initialization failed: {e}")
        # Continue startup so we can at least serve the error/debug page
    try:
        # Load versioned model v1 by default
        engine = CreditDecisionEngine(model_version='v1')
        print("Model and Database loaded successfully.")
    except Exception as e:
        print(f"CRITICAL: Error loading model during startup: {e}")
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
    """
    Display assessment form. Pre-fills data for authenticated users.
    """
    try:
        # Pre-fill logic for members
        inputs = None
        if user:
            try:
                latest = get_latest_assessments(user["id"], limit=1)
                if latest:
                    inputs = json.loads(latest[0]["inputs_json"])
                    # Add profile context to inputs for pre-filling Phase IV
                    inputs["loan_purpose"] = user.get("loan_purpose")
                    inputs["business_age"] = user.get("business_age")
                    inputs["repayment_confidence"] = user.get("repayment_confidence")
            except Exception as db_error:
                # Log but continue - just don't pre-fill
                print(f"WARNING: Failed to load user's previous assessments: {db_error}")
                
        return templates.TemplateResponse("assessment.html", {
            "request": request, 
            "user": user,
            "inputs": inputs # For pre-filling
        })
    except Exception as e:
        print(f"ERROR in assessment_form: {type(e).__name__}: {str(e)}")
        # Return minimal assessment page
        return templates.TemplateResponse("assessment.html", {
            "request": request, 
            "user": user,
            "inputs": None
        })

@app.get("/results", response_class=HTMLResponse)
async def show_results(request: Request, id: str, user=Depends(get_current_user)):
    """
    Display assessment results. Shows error message if result expired/invalid.
    NEVER redirects to /assessment to prevent loops.
    """
    try:
        # Retrieve result from cache
        cached_data = get_result(id)
        
        if not cached_data:
            # Result expired or invalid ID - show error in results page
            expired_result = {
                "credit_score": "--",
                "risk_tier": "Session Expired",
                "decision_summary": "Your assessment session has expired. Please run a new assessment.",
                "error": "session_expired"
            }
            return templates.TemplateResponse("results.html", {
                "request": request,
                "result": expired_result,
                "user": user,
                "lender_insight": "",
                "inputs": {"daily_revenue": 0, "daily_expenses": 0, "ad_spend": 0, "num_transactions": 0}
            })
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "result": cached_data["result"],
            "user": cached_data.get("user"),
            "lender_insight": cached_data.get("lender_insight", ""),
            "inputs": cached_data.get("inputs", {})
        })
    except Exception as e:
        print(f"ERROR in show_results: {type(e).__name__}: {str(e)}")
        # Return fallback results page
        error_result = {
            "credit_score": "--",
            "risk_tier": "Error",
            "decision_summary": "Unable to load results. Please try running a new assessment.",
            "error": "load_error"
        }
        return templates.TemplateResponse("results.html", {
            "request": request,
            "result": error_result,
            "user": user,
            "lender_insight": "",
            "inputs": {"daily_revenue": 0, "daily_expenses": 0, "ad_spend": 0, "num_transactions": 0}
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
    """
    CRITICAL: This endpoint ALWAYS redirects to /results, even on errors.
    It never re-renders assessment.html to prevent form submission loops.
    """
    
    # Initialize fallback result structure
    fallback_result = {
        "credit_score": "N/A",
        "risk_tier": "Unknown",
        "decision_summary": "Unable to complete assessment. Please try again.",
        "error": None
    }
    
    try:
        # Validate inputs
        if daily_revenue < 0 or daily_expenses < 0 or ad_spend < 0 or num_transactions < 1:
            raise ValueError("Invalid input values. All financial values must be positive and transactions must be at least 1.")
        
        # Check if engine is loaded
        if engine is None:
            fallback_result["error"] = "Model not loaded. Our system is temporarily unavailable."
            result_id = store_result({
                "result": fallback_result,
                "user": user,
                "lender_insight": "",
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
            return RedirectResponse(url=f"/results?id={result_id}", status_code=status.HTTP_303_SEE_OTHER)
        
        # Map simplified inputs to CreditDecisionEngine format
        # We simulate a balanced mix of sales and expenses to meet num_transactions
        transactions = []
        num_sales = max(1, num_transactions // 2)
        num_expenses = max(1, num_transactions - num_sales)
        
        avg_sale = daily_revenue / num_sales if num_sales > 0 else 0
        avg_expense = daily_expenses / num_expenses if num_expenses > 0 else 0
        
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
            try:
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
            except Exception as db_error:
                # Log but don't fail - we still show results
                print(f"WARNING: Failed to save assessment to database: {db_error}")

        # Store result in cache and redirect to results page
        result_id = store_result({
            "result": result,
            "user": user,
            "lender_insight": lender_insight,
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
        return RedirectResponse(url=f"/results?id={result_id}", status_code=status.HTTP_303_SEE_OTHER)
        
    except ValueError as ve:
        # Validation error - return fallback with error message
        fallback_result["error"] = str(ve)
        fallback_result["decision_summary"] = f"Validation Error: {str(ve)}"
        
    except Exception as e:
        # Any other error - return fallback with generic error message
        print(f"ERROR in process_assessment: {type(e).__name__}: {str(e)}")
        fallback_result["error"] = "An unexpected error occurred during assessment."
        fallback_result["decision_summary"] = "Unable to complete assessment due to a technical issue. Please verify your inputs and try again."
    
    # CRITICAL: Always store and redirect, even on errors
    result_id = store_result({
        "result": fallback_result,
        "user": user,
        "lender_insight": "",
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
    return RedirectResponse(url=f"/results?id={result_id}", status_code=status.HTTP_303_SEE_OTHER)

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
