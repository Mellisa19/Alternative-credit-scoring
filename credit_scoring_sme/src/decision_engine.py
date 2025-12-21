import pandas as pd
import numpy as np
import joblib
import os
import sys
import datetime
from typing import Dict, List, Any

# Ensure we can import from src
# We need to add the directory CONTAINING 'src' to the path.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.features.engineering import FeatureEngineer
from src.data.loader import DataLoader
from src.models.registry import load_credit_model

class CreditDecisionEngine:
    """
    Production-ready Credit Decision Engine.
    Exposes a single API-like function to score a SME based on raw data.
    """
    
    def __init__(self, model_version: str = 'v1'):
        try:
            # Load from Registry
            self.model = load_credit_model(model_version)
        except FileNotFoundError:
             raise FileNotFoundError(f"Model version {model_version} not found. Please run src/models/freeze_v1.py")
        
        # Load Reference Data (Raw Values) for Percentile Calculation
        self.ref_df = self._load_reference_features()

    def _load_reference_features(self):
        try:
            # Resolve data directory absolute path
            # This file is in src/decision_engine.py
            data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/raw'))
            loader = DataLoader(data_dir=data_dir)
            t, a, l = loader.load_all()
            fe = FeatureEngineer()
            df = fe.build_dataset(t, a, l)
            return df.drop('is_default', axis=1) # Keep raw features
        except Exception as e:
            # Reference data is optional - used only for percentile comparisons in summaries
            # Deployment environments (like Render) typically don't include training data
            print(f"INFO: Reference features not available (percentile comparisons disabled). This is expected in production.")
            return pd.DataFrame() # Fallback

    def credit_decision(self, input_data: Dict[str, List[Dict[str, Any]]], loan_readiness: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Decides credit worthiness for a single SME.
        """
        # 1. Validation
        if not input_data.get('transactions'):
             return self._error_response("Missing transaction data")

        # 2. DataFrame Construction
        df_trans = pd.DataFrame(input_data['transactions'])
        df_ads = pd.DataFrame(input_data.get('ad_spend', []))
        
        df_trans['business_id'] = 'New_SME'
        if not df_ads.empty: df_ads['business_id'] = 'New_SME'
        
        # 3. Feature Engineering
        fe = FeatureEngineer()
        try:
            feat_trans = fe.preprocess_transactions(df_trans)
            feat_ads = fe.preprocess_ad_spend(df_ads)
            
            if feat_ads.empty:
                 feat_ads = pd.DataFrame({'business_id': ['New_SME'], 'ad_spend_total': [0], 'ad_roi': [0], 'ad_cpa': [0]})
                 
            X_new = feat_trans.merge(feat_ads, on='business_id', how='left').fillna(0)
            X_new = X_new.set_index('business_id')
            
            # Align Definitions
            if hasattr(self.model.named_steps['clf'], 'feature_names_in_'):
                 cols = self.model.named_steps['clf'].feature_names_in_
                 # Reindex to match model schema exactly
                 X_new = X_new.reindex(columns=cols, fill_value=0)
                 
        except Exception as e:
            return self._error_response(f"Feature Engineering Error: {e}")

        # 4. Prediction
        try:
            prob_repay = self.model.predict_proba(X_new)[:, 0][0] # Class 0 is Repaid
            
            credit_score = int(prob_repay * 100)
            risk_tier = self._get_risk_tier(credit_score)
            
        except Exception as e:
            return self._error_response(f"Model Inference Error: {e}")

        # 5. Explanation
        summary = self._generate_summary(X_new, credit_score, risk_tier, loan_readiness)

        return {
            "sme_id": "New_SME",
            "timestamp": datetime.datetime.now().isoformat(),
            "credit_score": credit_score,
            "risk_tier": risk_tier,
            "decision_summary": summary,
            "probability_repay": round(prob_repay, 4),
            "key_metrics": X_new.round(2).to_dict(orient='records')[0]
        }

    def _get_risk_tier(self, score):
        if score >= 70: return "Low Risk"
        elif score >= 50: return "Medium Risk"
        return "High Risk"

    def _generate_summary(self, X_row, score, tier, loan_readiness=None):
        reasons = []
        
        # Compare against reference population
        if not self.ref_df.empty:
            pcts = (self.ref_df < X_row.iloc[0]).mean()
            
            if tier == 'Low Risk':
                if pcts.get('net_cash_flow', 0) > 0.7: reasons.append("strong cash flow")
                if pcts.get('txn_volatility', 1) < 0.3: reasons.append("stable transactions")
                if pcts.get('ad_roi', 0) > 0.7: reasons.append("marketing efficiency")
            else:
                if pcts.get('net_cash_flow', 0) < 0.3: reasons.append("weak cash flow")
                if pcts.get('txn_volatility', 0) > 0.7: reasons.append("volatile transactions")
                if pcts.get('burn_rate', 0) > 0.7: reasons.append("high burn rate")
        
        # --- PREMIUM LENDER-STYLE REASONING ---
        lender_context = ""
        if loan_readiness:
            context_reasons = []
            purpose = loan_readiness.get('loan_purpose')
            age = loan_readiness.get('business_age')
            conf = loan_readiness.get('repayment_confidence')

            if purpose in ["Business expansion", "Marketing / advertising"] and score > 50:
                context_reasons.append(f"Clear intent for {purpose.lower()} aligns with growth momentum")
            
            if age == "Over 3 years":
                context_reasons.append("Operational maturity of 3+ years provides a stability premium")
            elif age == "Less than 6 months":
                context_reasons.append("Early-stage status suggests a conservative credit approach")
            
            if conf == "Very confident":
                context_reasons.append("High repayment confidence is a strong borrower commitment signal")

            if context_reasons:
                lender_context = ". [Lender Perspective: " + " | ".join(context_reasons) + "]"

        if not reasons:
            base_summary = f"This business is categorized as {tier} based on aggregate risk factors"
        else:
            joiner = "driven by" if tier == 'Low Risk' else "due to"
            base_summary = f"This business has a {tier} score {joiner} {', '.join(reasons)}"
            
        return base_summary + lender_context

    def _error_response(self, msg):
        return {"error": msg, "risk_tier": "Unknown", "credit_score": 0}

if __name__ == "__main__":
    engine = CreditDecisionEngine()
    
    # Mock Input
    sample_data = {
        "transactions": [
            {"date": "2023-01-01", "amount": 5000, "transaction_type": "Sales"},
            {"date": "2023-01-02", "amount": -2000, "transaction_type": "Expense"},
        ],
        "ad_spend": [
            {"date": "2023-01-01", "spend_amount": 500, "clicks": 50, "conversions": 2}
        ]
    }
    
    result = engine.credit_decision(sample_data)
    import json
    print(json.dumps(result, indent=2))
