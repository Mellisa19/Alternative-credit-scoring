from fastapi.testclient import TestClient
from src.api.main import app
import json

client = TestClient(app)

def test_health_check(client):
    print("\nTesting /health endpoint...")
    response = client.get("/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200

def test_credit_decision(client):
    print("\nTesting /credit-decision endpoint...")
    
    # Sample payload
    payload = {
        "business_id": "SME-TEST-001",
        "transactions": [
            {"date": "2023-01-01", "amount": 5000.0, "transaction_type": "Sales"},
            {"date": "2023-01-02", "amount": -2000.0, "transaction_type": "Expense"},
            {"date": "2023-01-03", "amount": 4000.0, "transaction_type": "Sales"}
        ],
        "ad_spend": [
            {"date": "2023-01-01", "spend_amount": 500.0, "clicks": 50, "conversions": 2}
        ]
    }
    
    response = client.post("/credit-decision", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    assert response.status_code == 200
    data = response.json()
    assert "credit_score" in data
    assert "risk_tier" in data
    assert data["sme_id"] == "SME-TEST-001"

if __name__ == "__main__":
    try:
        with TestClient(app) as client:
            test_health_check(client)
            test_credit_decision(client)
        print("\nAPI Verification Successful!")
    except Exception as e:
        print(f"\nAPI Verification Failed: {e}")
