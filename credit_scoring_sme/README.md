# Alternative Credit Scoring for SMEs

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Mellisa19/Alternative-credit-scoring)

A production-ready machine learning system designed to bridge the SME credit gap in emerging markets. By leveraging **alternative data** (cash flows, transaction logs, and digital marketing performance), this system provides reliable risk assessments for businesses that lack traditional credit history.

## 📌 Problem Statement
In many emerging markets, especially across Africa, Small and Medium Enterprises (SMEs) struggle to access formal credit. Traditional credit scoring fails these businesses because:
1.  **Invisible History**: Most SMEs operate outside the formal credit bureau ecosystem.
2.  **Asset-Light Operations**: Many high-growth digital businesses lack physical collateral.
3.  **Fragmented Data**: Financial health is often spread across transaction logs, mobile money, and digital platforms rather than centralized bank statements.

## 🚀 Solution Overview
This system bypasses traditional bureau dependency by engineering a "Digital Credit Identity." It analyzes raw business data to assess:
- **Operational Health**: Consistency of cash flows and transaction volumes.
- **Financial discipline**: Burn rates and margin sustainability.
- **Growth Potential**: Efficiency of marketing spend as a proxy for business savvy and market demand.

## 📊 Data & Feature Engineering
The model transforms granular transaction and marketing logs into high-signal risk features:

| Category | Feature | Business Significance |
| :--- | :--- | :--- |
| **Cash Flow** | `net_cash_flow` | Fundamental ability to service debt. |
| **Stability** | `txn_volatility` | Predictability of revenue; penalizes erratic income. |
| **Efficiency** | `burn_rate` | Measures cash sustainability and overhead control. |
| **Growth** | `ad_roi` | Validates product-market fit via marketing efficiency. |

## 🧠 Machine Learning Approach
We utilize a **Random Forest Classifier** as the core decision engine.
- **Why Random Forest?** It offers a superior balance of non-linear pattern recognition (captures complex risk interactions) and intrinsic explainability.
- **Explainability**: Every decision includes a **Decision Summary** that identifies the top 3 drivers of the risk tier, ensuring transparency for regulators and business owners.
- **Versioning**: A built-in **Model Registry** ensures reproducibility, enabling seamless rotation between versioned artifacts (e.g., `v1` to `v2`).

## ⚖️ Fairness & Ethics
Credit systems must be equitable. This project includes a dedicated **Fairness Analysis** module that monitors:
- **Business Size Bias**: Ensuring Micro-SMEs aren't systemically unfairly penalized vs larger counterparts.
- **Digital Divide**: Balancing scores for "Organic" businesses that may have stable revenue but zero ad spend data.
- **Transparency**: Clear, plain-English explanations for every "High Risk" rejection to prevent "Black Box" decisions.

## 📡 API Usage
The scoring engine is exposed via a high-performance **FastAPI** REST interface.

### 1. Start the API
```bash
uvicorn src.api.main:app --reload
```

### 2. Post a Scoring Request
```bash
curl -X POST "http://localhost:8000/credit-decision" \
     -H "Content-Type: application/json" \
     -d '{
       "business_id": "SME-001",
       "transactions": [{"date": "2024-01-01", "amount": 5000, "transaction_type": "Sales"}],
       "ad_spend": [{"date": "2024-01-01", "spend_amount": 500}]
     }'
```

### 3. Receive the Decision
```json
{
  "credit_score": 72,
  "risk_tier": "Low Risk",
  "decision_summary": "Low Risk score driven by strong cash flow and stable transactions."
}
```

## 📂 Project Structure
- `src/api/`: REST API implementation (FastAPI).
- `src/features/`: Core engineering logic for alternative data.
- `src/models/`: Training pipelines and the Model Registry.
- `src/validation/`: Bias, fairness, and stress-test suites.
- `notebooks/`: Experimental labs for feature discovery.

## 🔭 Future Improvements
- **Real-time Monitoring**: Drift detection for shifting SME spending patterns.
- **Web App Frontend**: A dashboard for loan officers to visualize risk drivers.
- **OAuth2 Integration**: Secure API access for external banking partners.
