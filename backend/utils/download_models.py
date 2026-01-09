"""
Download and cache Hugging Face models for ai, deepfake detection
"""

import os
import sys
from pathlib import Path
from transformers import (
    AutoImageProcessor,
    SiglipForImageClassification,
    ViTForImageClassification,
    ViTImageProcessor
)

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from config import MODELS, MODEL_CACHE_DIR

def download_model(model_name, model_type, processor_type):
    """Download a single model and its processor"""
    print(f"\n{'='*60}")
    print(f"Downloading: {model_name}")
    print(f"{'='*60}")
    
    try:
        # Download processor
        if processor_type == 'AutoImageProcessor':
            processor = AutoImageProcessor.from_pretrained(
                model_name,
                cache_dir=MODEL_CACHE_DIR
            )
        else:  # ViTImageProcessor
            processor = ViTImageProcessor.from_pretrained(
                model_name,
                cache_dir=MODEL_CACHE_DIR
            )
        print("Processor downloaded")
        
        # Download model
        if model_type == 'SiglipForImageClassification':
            model = SiglipForImageClassification.from_pretrained(
                model_name,
                cache_dir=MODEL_CACHE_DIR
            )
        else:  # ViTForImageClassification
            model = ViTForImageClassification.from_pretrained(
                model_name,
                cache_dir=MODEL_CACHE_DIR
            )
        print("Model downloaded")
        
        return True
        
    except Exception as e:
        print("Error: {e}")
        return False

def main():
    """Download all models"""
    print(f"Cache directory: {MODEL_CACHE_DIR}")
    print(f"Downloading {len(MODELS)} models\n")
    
    success_count = 0
    
    for model_key, model_config in MODELS.items():
        success = download_model(
            model_config['name'],
            model_config['type'],
            model_config['processor']
        )
        
        if success:
            success_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Download Summary: {success_count}/{len(MODELS)} successful")
    print(f"{'='*60}")
    
    if success_count == len(MODELS):
        print("\nAll models downloaded successfully!")
    else:
        print("\nSome models failed to download.")
        sys.exit(1)

if __name__ == '__main__':
    main()
