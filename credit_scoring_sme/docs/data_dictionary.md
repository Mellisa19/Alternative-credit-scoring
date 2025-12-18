# Dataset Requirements

To build the credit scoring model, we require the following three datasets in CSV format. Please place them in `data/raw/`.

## 1. `transactions.csv`
Daily inflow and outflow of funds for the businesses.

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `business_id` | String | Unique identifier for the SME | "SME-001" |
| `date` | Date | Date of transaction (YYYY-MM-DD) | "2023-01-15" |
| `amount` | Float | Transaction value (use negative for expenses/outflows) | 50000.00 |
| `transaction_type` | String | Category (e.g., "Sales", "Inventory", "Utility") | "Sales" |
| `channel` | String | Payment channel (e.g., "POS", "Transfer", "Cash") | "POS" |

## 2. `ad_spend.csv`
Marketing expenditure and performance metrics. Used to gauge business aggressiveness and growth potential.

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `business_id` | String | Unique identifier for the SME | "SME-001" |
| `date` | Date | Date of ad run | "2023-01-15" |
| `platform` | String | Ad platform (Facebook, Instagram, Google) | "Instagram" |
| `spend_amount` | Float | Amount spent on ads | 2500.00 |
| `impressions` | Integer | Number of views | 1500 |
| `clicks` | Integer | Number of clicks | 120 |
| `conversions` | Integer | Sales attributable to the ad | 5 |

## 3. `loan_performance.csv`
Historical data on previous loans to train the model (Target variable).

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `loan_id` | String | Unique loan identifier | "LN-992" |
| `business_id` | String | Unique identifier for the SME | "SME-001" |
| `disbursement_date`| Date | Date money was given | "2022-06-10" |
| `principal_amount` | Float | Loan amount | 1000000.00 |
| `due_date` | Date | When it was supposed to be paid back | "2022-12-10" |
| `repaid_date` | Date | Actual repayment date (NaN if default) | "2022-12-05" |
| `status` | String | **Target Label**: "Repaid" or "Default" | "Repaid" |

> **Note**: If you do not have real data, we can generate a synthetic dataset matching this schema for development.
