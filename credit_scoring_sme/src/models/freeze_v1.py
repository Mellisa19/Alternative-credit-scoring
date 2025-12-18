from src.models.registry import ModelRegistry
import os

def freeze_model():
    print("Freezing current best model as 'v1'...")
    registry = ModelRegistry()
    
    # We want the Random Forest model we validated
    source_model = 'models/rf_advanced.pkl'
    
    if not os.path.exists(source_model):
        print(f"Error: {source_model} not found. Ensure you are in project root.")
        return
        
    registry.promote_latest(source_model, "v1")
    print("Success! Model v1 is ready.")

if __name__ == "__main__":
    freeze_model()
