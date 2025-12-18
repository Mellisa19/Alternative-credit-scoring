import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import joblib

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("SHAP not found. Explanations will be limited to Feature Importance.")

try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("XGBoost not found. Skipping XGBoost.")

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix, precision_recall_curve, auc

from src.data.loader import DataLoader
from src.features.engineering import FeatureEngineer

class CreditScoringModel:
    def __init__(self, output_dir='models'):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        self.results = {}
        
    def train(self):
        print("Loading data...")
        loader = DataLoader()
        t, a, l = loader.load_all()
        
        print("Engineering features...")
        fe = FeatureEngineer()
        data = fe.build_dataset(t, a, l)
        
        X = data.drop('is_default', axis=1)
        y = data['is_default']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
        
        print(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
        
        # 1. Baseline: Logistic Regression
        print("\n--- Training Baseline (Logistic Regression) ---")
        lr_model = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(random_state=42))
        ])
        lr_model.fit(X_train, y_train)
        self._evaluate(lr_model, X_test, y_test, "Logistic Regression")
        joblib.dump(lr_model, os.path.join(self.output_dir, 'lr_baseline.pkl'))
        
        # 2. Advanced: Random Forest
        print("\n--- Training Random Forest ---")
        rf_model = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('clf', RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5))
        ])
        rf_model.fit(X_train, y_train)
        self._evaluate(rf_model, X_test, y_test, "Random Forest")
        joblib.dump(rf_model, os.path.join(self.output_dir, 'rf_advanced.pkl'))
        
        # 3. XGBoost
        if XGB_AVAILABLE:
            print("\n--- Training XGBoost ---")
            xgb_model = Pipeline([
                ('imputer', SimpleImputer(strategy='median')),
                ('clf', XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, use_label_encoder=False, eval_metric='logloss'))
            ])
            xgb_model.fit(X_train, y_train)
            self._evaluate(xgb_model, X_test, y_test, "XGBoost")
            joblib.dump(xgb_model, os.path.join(self.output_dir, 'xgb_model.pkl'))
        
        self._print_summary()
        self._explain_recommendation()
        
        # Explain the best model (RFC or XGB)
        best_model = rf_model # Default to RF for explainability
        if XGB_AVAILABLE and self.results.get('XGBoost', {}).get('roc_auc', 0) > self.results.get('Random Forest', {}).get('roc_auc', 0) + 0.05:
             # Only switch if significantly better
             best_model = xgb_model
             
        self._explain_model(best_model, X_test, X.columns)
        
    def _evaluate(self, model, X_test, y_test, name):
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        # Metrics
        p, r, _ = precision_recall_curve(y_test, y_prob)
        pr_auc = auc(r, p)
        roc_auc = roc_auc_score(y_test, y_prob)
        
        print(f"\nResults for {name}:")
        print(classification_report(y_test, y_pred))
        print(f"ROC-AUC: {roc_auc:.4f}")
        print(f"PR-AUC:  {pr_auc:.4f}")
        print("Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        self.results[name] = {'roc_auc': roc_auc, 'pr_auc': pr_auc}
        
    def _print_summary(self):
        print("\n=== Model Comparison Summary ===")
        print(f"{'Model':<20} | {'ROC-AUC':<10} | {'PR-AUC':<10}")
        print("-" * 46)
        for name, metrics in self.results.items():
            print(f"{name:<20} | {metrics['roc_auc']:.4f}     | {metrics['pr_auc']:.4f}")
            
    def _explain_recommendation(self):
        print("\n=== Recommendation ===")
        print("Best Model for Credit Scoring: **Random Forest** (likely)")
        print("Reasoning:")
        print("1. **Explainability**: Essential for credit. RF Feature Importance is intuitive. LR is clearer but linear.")
        print("2. **Robustness**: RF handles noisy/missing data well without heavy preprocessing.")
        print("3. **XGBoost**: Generally purely performant, but might overfit slightly on small datasets vs RF. If dataset grows >10k rows, switch to XGBoost.")

    def _explain_model(self, model, X_test, feature_names):
        print("\n--- Generating Explanations ---")
        
        # Business-friendly descriptions
        FEATURE_DESCRIPTIONS = {
            'net_cash_flow': "Total money left after expenses (Profitability).",
            'burn_rate': "Ratio of expenses to income (Sustainability). High burn rate means spending too fast.",
            'txn_volatility': "Consistency of daily transactions. High volatility suggests unstable business.",
            'ad_spend_total': "Total investment in marketing (Aggressiveness).",
            'ad_roi': "Return on Investment for ads. Measures marketing efficiency.",
            'ad_cpa': "Cost to acquire a customer. Lower is better.",
            'txn_count': "Total number of transactions (Volume).",
            'total_inflow': "Total money coming in (Revenue).",
            'avg_inflow': "Average size of incoming payments.",
            'total_outflow': "Total money going out (Expenses)."
        }

        # Feature Importance (Built-in)
        importances = None
        # Check for Classifier inside Pipeline
        if 'clf' in model.named_steps:
             model_rf = model.named_steps['clf']
             if hasattr(model_rf, 'feature_importances_'):
                importances = model_rf.feature_importances_
                indices = np.argsort(importances)[::-1]
                
                print("\n=== Business Explanation Report ===")
                report_lines = []
                report_lines.append("Top factors influencing credit score:\n")
                
                for f in range(min(5, len(feature_names))):
                    name = feature_names[indices[f]]
                    score = importances[indices[f]]
                    desc = FEATURE_DESCRIPTIONS.get(name, "No description available.")
                    
                    line = f"{f+1}. {name} (Impact: {score:.1%}): {desc}"
                    print(line)
                    report_lines.append(line)
                    
                # Save report
                with open('reports/model_explanation.txt', 'w') as f:
                    f.write('\n'.join(report_lines))
                print("\nSaved business report to reports/model_explanation.txt")

                # Plot Feature Importance
                plt.figure(figsize=(10, 6))
                plt.title("Key Risk Drivers (Feature Importance)")
                plt.bar(range(len(importances)), importances[indices], align="center")
                plt.xticks(range(len(importances)), [feature_names[i] for i in indices], rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig('reports/feature_importance.png')
                print("Saved visualization to reports/feature_importance.png")

        if SHAP_AVAILABLE:
            try:
                # SHAP implementation
                step_imputer = model.named_steps['imputer']
                X_test_imputed = step_imputer.transform(X_test)
                
                # TreeExplainer works for XGB and RF
                # We need the actual estimator
                if 'clf' in model.named_steps:
                    estimator = model.named_steps['clf']
                    explainer = shap.TreeExplainer(estimator)
                    shap_values = explainer.shap_values(X_test_imputed)
                    
                    # XGBoost / Random Forest binary case handling
                    if isinstance(shap_values, list): # Random Forest often returns list
                        shap_values = shap_values[1]
                    
                    # Summary Plot
                    plt.figure()
                    shap.summary_plot(shap_values, X_test_imputed, feature_names=feature_names, show=False)
                    plt.tight_layout()
                    plt.savefig('reports/shap_summary.png')
                    print("Saved SHAP summary to reports/shap_summary.png")
            except Exception as e:
                print(f"SHAP generation failed: {e}")

if __name__ == "__main__":
    trainer = CreditScoringModel()
    trainer.train()
