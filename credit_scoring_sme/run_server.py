import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to the python path to fix import errors
# We are in credit_scoring_sme/run_server.py
# We want credit_scoring_sme/ to be the import root because main.py does "from src.api..."
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

print(f"Starting Credit Scoring App...")
print(f"Working Directory: {os.getcwd()}")
print(f"Python Path[0]: {sys.path[-1]}")

if __name__ == "__main__":
    # Ensure we bind to localhost specifically
    print("\n" + "="*50)
    print("   OPEN THIS LINK IN YOUR BROWSER:")
    print("   http://127.0.0.1:8000/assessment")
    print("="*50 + "\n")
    
    try:
        # Run the app - using the import string "src.api.main:app"
        # The working directory MUST be credit_scoring_sme for this to work
        uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
    except Exception as e:
        print(f"\nCRITICAL STARTUP ERROR: {e}")
        input("Press Enter to exit...")
