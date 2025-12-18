# Alternative Credit Scoring System for SMEs

A machine learning system that predicts loan repayment probability for small and medium businesses using non-traditional data sources, with focus on African/Nigerian markets.

## 🎯 Project Goal

Build an explainable ML system that outputs:
- **Credit Score**: 0-100 scale
- **Risk Category**: Low (70-100), Medium (40-69), High (0-39)
- **Key Factors**: Explainable features influencing the score

## 📊 Dataset Requirements

The system uses **non-traditional data sources** instead of traditional credit bureau data. Place all CSV files in the `data/raw/` directory.

### 1. Business Basic Information (`business_basic_info.csv`)

Core business attributes and demographics.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| business_id | string | Unique business identifier | BUS_001 |
| business_age_months | int | Age of business in months | 24 |
| industry_sector | string | Business sector | retail, manufacturing, services |
| location_state | string | Nigerian state | Lagos, Kano, Abuja |
| business_size | string | Size category | micro, small, medium |
| registration_status | string | Formal registration | registered, informal |
| num_employees | int | Number of employees | 5 |

### 2. Business Transaction History (`business_transactions.csv`)

Daily/weekly transaction records showing revenue patterns.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| business_id | string | Business identifier | BUS_001 |
| transaction_date | date | YYYY-MM-DD | 2023-01-15 |
| transaction_amount | float | Revenue amount (NGN) | 25000.50 |
| transaction_type | string | sale, service, refund | sale |
| payment_method | string | cash, transfer, pos, mobile_money | transfer |
| customer_type | string | new, returning, bulk | returning |

### 3. Cash Flow Patterns (`cash_flow_patterns.csv`)

Monthly cash flow and expense tracking.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| business_id | string | Business identifier | BUS_001 |
| month_year | date | YYYY-MM | 2023-01 |
| monthly_revenue | float | Total monthly revenue | 500000.00 |
| monthly_expenses | float | Total monthly expenses | 350000.00 |
| operating_expenses | float | Rent, utilities, salaries | 200000.00 |
| cost_of_goods | float | Inventory/supply costs | 150000.00 |
| cash_balance_start | float | Starting cash balance | 100000.00 |
| cash_balance_end | float | Ending cash balance | 250000.00 |

### 4. Advertising Performance (`advertising_performance.csv`)

Digital and traditional advertising spend and ROI.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| business_id | string | Business identifier | BUS_001 |
| campaign_date | date | YYYY-MM-DD | 2023-02-01 |
| platform | string | facebook, google, instagram, local_media | facebook |
| campaign_type | string | awareness, conversion, retention | conversion |
| spend_amount | float | Advertising spend (NGN) | 15000.00 |
| impressions | int | Number of ad impressions | 50000 |
| clicks | int | Number of clicks | 1200 |
| conversions | int | Sales/conversions from ads | 45 |
| campaign_duration_days | int | Length of campaign | 14 |

### 5. Loan Repayment History (`loan_repayment_history.csv`)

Historical loan performance (target variable).

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| business_id | string | Business identifier | BUS_001 |
| loan_id | string | Unique loan identifier | LOAN_001 |
| loan_amount | float | Loan amount requested | 100000.00 |
| loan_date | date | YYYY-MM-DD | 2023-03-01 |
| repayment_due_date | date | YYYY-MM-DD | 2023-09-01 |
| actual_repayment_date | date | YYYY-MM-DD or NULL | 2023-08-15 |
| loan_repaid | int | Target: 1=repaid, 0=defaulted | 1 |
| repayment_amount | float | Amount actually repaid | 105000.00 |

## 🏗️ Project Structure

```
alternative-credit-scoring/
├── src/                          # Source code
│   ├── data/                     # Data loading & preprocessing
│   ├── features/                 # Feature engineering
│   ├── models/                   # ML models & training
│   └── utils/                    # Utilities
├── data/
│   ├── raw/                      # Raw CSV datasets
│   ├── processed/                # Cleaned & processed data
│   └── external/                 # External data sources
├── models/
│   ├── checkpoints/              # Model checkpoints
│   └── artifacts/                # Model artifacts & metrics
├── notebooks/                    # Jupyter notebooks
├── tests/                        # Unit & integration tests
├── config/                       # Configuration files
├── docs/                         # Documentation
└── scripts/                      # Utility scripts
```

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Place datasets in `data/raw/`** according to specifications above

3. **Run the training pipeline:**
   ```bash
   python scripts/train.py
   ```

4. **Start the API server:**
   ```bash
   python scripts/serve.py
   ```

## 🧠 Model Approach

### Baseline Models
- **Logistic Regression**: Interpretable baseline with feature importance
- **Random Forest**: Handles non-linear relationships

### Advanced Models
- **XGBoost**: Gradient boosting with regularization
- **LightGBM**: Fast and memory-efficient

### Explainability
- **SHAP values**: Global and local feature explanations
- **Feature importance**: Model-agnostic importance scores
- **Partial dependence plots**: Feature effect visualization

## 📈 Key Features Engineered

### Cash Flow Features
- Monthly cash flow volatility
- Operating cash flow ratio
- Cash burn rate
- Revenue growth trends
- Expense stability metrics

### Advertising ROI Features
- Cost per acquisition (CPA)
- Return on ad spend (ROAS)
- Conversion rates by platform
- Campaign effectiveness trends

### Business Stability Features
- Revenue consistency score
- Transaction frequency patterns
- Seasonal adjustment factors
- Growth trajectory indicators

## 🔍 Evaluation Metrics

- **Primary**: ROC-AUC (handles class imbalance)
- **Secondary**: Precision, Recall, F1-Score
- **Business**: Cost-sensitive metrics for lending decisions

## 🛡️ Production Considerations

- **Data Validation**: Pydantic schemas for data quality
- **Model Monitoring**: Drift detection and retraining triggers
- **API Security**: Input validation and rate limiting
- **Scalability**: Containerization with Docker
- **Logging**: Comprehensive logging for debugging

## 🤝 Contributing

1. Follow the established project structure
2. Add unit tests for new features
3. Update documentation
4. Ensure code follows PEP 8 standards

## 📄 License

MIT License - see LICENSE file for details.
