import os
import joblib
import json
import shutil
from datetime import datetime

class ModelRegistry:
    """
    Manages model versioning, saving, and loading.
    """
    def __init__(self, base_path=None):
        if base_path is None:
            # Default to 'models' directory in the project root (credit_scoring_sme/models)
            # This file is in src/models/registry.py
            self.base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../models'))
        else:
            self.base_path = base_path
            
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
            
    def save_model(self, model, version_tag, metadata=None):
        """
        Saves a model component with a specific version.
        Structure: models/v1/model.pkl
        """
        version_dir = os.path.join(self.base_path, version_tag)
        if not os.path.exists(version_dir):
            os.makedirs(version_dir)
            
        # Save Pickle
        model_path = os.path.join(version_dir, 'credit_model.pkl')
        joblib.dump(model, model_path)
        
        # Save Metadata
        if metadata:
            meta_path = os.path.join(version_dir, 'metadata.json')
            metadata['timestamp'] = datetime.now().isoformat()
            metadata['version'] = version_tag
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        print(f"Model saved to {version_dir}")
        return model_path

    def load_model(self, version_tag):
        """
        Loads a specific model version.
        """
        model_path = os.path.join(self.base_path, version_tag, 'credit_model.pkl')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Version {version_tag} not found.")
            
        return joblib.load(model_path)
        
    def promote_latest(self, source_path, version_tag="v1"):
        """
        Promotes an existing .pkl file to a versioned artifact.
        """
        if not os.path.exists(source_path):
             raise FileNotFoundError(f"Source model {source_path} not found.")
             
        # Load to verify
        model = joblib.load(source_path)
        
        # Save as version
        return self.save_model(model, version_tag, metadata={"source": source_path, "promoted": True})

def load_credit_model(version='v1'):
    """
    Helper function to load the standard credit model.
    """
    registry = ModelRegistry() # Defaults to 'models' relative to CWD usually
    # Robust path handling needed dependent on where this is called
    # For now assume CWD is project root
    return registry.load_model(version)
