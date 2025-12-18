import pandas as pd
import numpy as np
import joblib
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.data.loader import DataLoader
from src.features.engineering import FeatureEngineer

class CreditScoringEngine:
    def __init__(self, model_path='models/rf_advanced.pkl'):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}. Please train the model first.")
        
        self.model = joblib.load(model_path)
        
    def generate_scores(self):
        """
        Loads data, extracts features, and generates credit scores for all businesses.
        """
        print("Loading current data...")
        loader = DataLoader()
        t, a, l = loader.load_all()
        
        print("Extracting features...")
        fe = FeatureEngineer()
        # Note: In production, we might not have labels (l) for new applicants.
        # But our build_dataset needs labels to drop them. 
        # For this demo, we'll straightforwardly use the same pipeline but pretend we don't know the outcome.
        
        data = fe.build_dataset(t, a, l)
        
        # businesses are the index
        X = data.drop('is_default', axis=1)
        
        print("Predicting probabilities...")
        # predict_proba returns [prob_class_0 (Repaid), prob_class_1 (Default)]
        # We want probability of repayment for the score.
        probs = self.model.predict_proba(X)
        prob_repay = probs[:, 0]
        
        results = pd.DataFrame(index=X.index)
        results['prob_repay'] = prob_repay
        
        # transform to Score (0-100)
        # Simple linear scaling: Score = Probability * 100
        results['credit_score'] = (results['prob_repay'] * 100).astype(int)
        
        # Risk Categorization
        results['risk_category'] = results['credit_score'].apply(self._get_risk_category)
        
        # Generate Human-Readable Decision Summary
        print("Generating decision summaries...")
        results['decision_summary'] = self._generate_summaries(results, X)
        
        return results
        
    def _get_risk_category(self, score):
        if score >= 70:
            return 'Low Risk'
        elif score >= 50:
            return 'Medium Risk'
        else:
            return 'High Risk'

    def _generate_summaries(self, results, X):
        """
        Generates a text explanation for each business based on their score and key feature deviations.
        """
        summaries = []
        
        # Calculate percentiles to identify "extreme" values
        # We compare each business against the population
        stats = X.rank(pct=True)
        
        for business_id, row in results.iterrows():
            score = row['credit_score']
            risk = row['risk_category']
            
            reasons = []
            
            # Get feature percentiles for this business
            # Note: We need to handle cases where business_id might not be in stats if indexes didn't align, 
            # but here they should align.
            feat_ranks = stats.loc[business_id]
            feat_vals = X.loc[business_id]
            
            # Logic: Identify why the score is NOT perfect.
            # If Low Risk (Good), highlight strengths.
            # If High/Medium Risk, highlight weaknesses.
            
            if risk == 'Low Risk':
                # Look for good indicators
                if feat_ranks.get('net_cash_flow', 0) > 0.5:
                    reasons.append("strong cash flow")
                if feat_ranks.get('txn_volatility', 1) < 0.5:
                    reasons.append("stable transaction volume")
                if feat_ranks.get('ad_roi', 0) > 0.5:
                    reasons.append("efficient marketing")
                    
                if not reasons:
                    explanation = "This business shows consistent performance across all metrics."
                else:
                    explanation = f"This business has a {risk} score driven by {', '.join(reasons)}."
                    
            else: # Medium or High Risk
                # Look for red flags (Bad indicators)
                if feat_ranks.get('net_cash_flow', 0) < 0.4:
                    reasons.append("low profitability")
                if feat_ranks.get('txn_volatility', 0) > 0.6:
                    reasons.append("unstable cash flow")
                if feat_ranks.get('burn_rate', 0) > 0.6:
                    reasons.append("high burn rate")
                if feat_ranks.get('ad_cpa', 0) > 0.6:
                    reasons.append("inefficient ad spend")
                if feat_ranks.get('ad_spend_total', 0) < 0.2:
                    reasons.append("low market presence")
                
                if not reasons:
                    # Fallback if no specific feature is extreme but model gave low score
                    explanation = f"This business is flagged as {risk} due to a combination of moderate risk factors."
                else:
                    explanation = f"This business has a {risk} score due to {', '.join(reasons)}."
            
            summaries.append(explanation)
            
        return summaries

if __name__ == "__main__":
    engine = CreditScoringEngine()
    scores = engine.generate_scores()
    
    # Save to reports
    if not os.path.exists('reports'):
        os.makedirs('reports')
    
    scores.to_csv('reports/final_scores.csv')
    
    print("\n--- Sample Credit Scores ---")
    print(scores[['credit_score', 'risk_category']].head(10))
    
    print("\nScore Distribution:")
    print(scores['risk_category'].value_counts())
    print(f"\nFull report saved to reports/final_scores.csv")
