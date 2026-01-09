"""
Configuration settings for the AI, Deepfake Detector backend
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Upload settings
UPLOAD_FOLDER = BASE_DIR / 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Model settings
MODEL_CACHE_DIR = BASE_DIR / 'models' / 'cache'

# Model configurations
MODELS = {
    'siglip': {
        'name': 'prithivMLmods/deepfake-detector-model-v1',
        'type': 'SiglipForImageClassification',
        'processor': 'AutoImageProcessor',
        'input_size': 512,
        'description': 'SigLIP-based detector, best for modern AI-generated images'
    },
    'vit_v2': {
        'name': 'prithivMLmods/Deep-Fake-Detector-v2-Model',
        'type': 'ViTForImageClassification',
        'processor': 'ViTImageProcessor',
        'input_size': 224,
        'description': 'Vision Transformer v2, specializes in face deepfakes'
    },
    'vit_base': {
        'name': 'dima806/deepfake_vs_real_image_detection',
        'type': 'ViTForImageClassification',
        'processor': 'ViTImageProcessor',
        'input_size': 224,
        'description': 'ViT baseline, adds diversity to ensemble'
    }
}

# Ensemble weights (must sum to 1.0)
ENSEMBLE_WEIGHTS = {
    'siglip': 0.40,    # Highest weight - best overall performance
    'vit_v2': 0.35,    # good on face manipulations
    'vit_base': 0.25   # adds diversity
}

# Detection thresholds
FAKE_THRESHOLD = 0.6      # Above this = FAKE
REAL_THRESHOLD = 0.4      # Below this = REAL
# Between thresholds = UNCERTAIN

# Flask settings
DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
HOST = '0.0.0.0'
PORT = int(os.getenv('PORT', 5000))

# CORS settings (allowed origins)
CORS_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3000',
]

# Preprocessing settings
USE_SMART_RESIZE = True
LANCZOS_RESAMPLING = True  # High-quality downsampling

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Create necessary directories
def init_directories():
    """Create required directories if they don't exist"""
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep in uploads to track empty folder
    gitkeep = UPLOAD_FOLDER / '.gitkeep'
    if not gitkeep.exists():
        gitkeep.touch()

# Initialize on import
init_directories()
