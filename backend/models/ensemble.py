"""
Ensemble Detector - Combines 3 models for robust deepfake detection
SigLIP (40% weight) - Best for modern AI-generated images
ViT-v2 (35% weight) - Best for face deepfakes
ViT-Base (25% weight) - Adds diversity
"""

import torch
import numpy as np
from typing import Dict, List
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import ENSEMBLE_WEIGHTS, FAKE_THRESHOLD, REAL_THRESHOLD

from .siglip_detector import SigLIPDetector
from .vit_v2_detector import ViTv2Detector
from .vit_base_detector import ViTBaseDetector


class EnsembleDetector:
    """
    Ensemble deepfake detector combining 3 specialized models.
    Uses weighted majority voting with uncertainty detection
    to provide robust and transparent predictions.
    """
    
    def __init__(self, device: str = None):
        """
        Initialize ensemble detector
        
        Args:
            device: Device to run models on ('cuda', 'cpu', or None for auto)
        """
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        
        print(f"\n{'='*60}")
        print("Initializing Ensemble Detector")
        print(f"{'='*60}")
        print(f"Device: {self.device}")
        print(f"Weights: SigLIP={ENSEMBLE_WEIGHTS['siglip']}, "
              f"ViT-v2={ENSEMBLE_WEIGHTS['vit_v2']}, "
              f"ViT-Base={ENSEMBLE_WEIGHTS['vit_base']}")
        print(f"{'='*60}\n")
        
        # Initialize all three models
        self.siglip = SigLIPDetector(device=self.device)
        self.vit_v2 = ViTv2Detector(device=self.device)
        self.vit_base = ViTBaseDetector(device=self.device)
        
        print(f"\n{'='*60}")
        print("All models loaded successfully")
        print(f"{'='*60}\n")
    
    def detect_disagreement(self, results: List[Dict]) -> bool:
        """
        Detect if models significantly disagree
        
        Args:
            results: List of individual model results
            
        Returns:
            True if models disagree significantly
        """
        fake_probs = [r['fake_probability'] for r in results]
        std_dev = np.std(fake_probs)
        
        # If standard deviation > 0.25, models disagree significantly
        return std_dev > 0.25
    
    def calculate_agreement_level(self, results: List[Dict]) -> str:
        """
        Calculate how much models agree
        
        Args:
            results: List of individual model results
            
        Returns:
            'HIGH', 'MEDIUM', or 'LOW' agreement
        """
        fake_probs = [r['fake_probability'] for r in results]
        std_dev = np.std(fake_probs)
        
        if std_dev < 0.15:
            return 'HIGH'
        elif std_dev < 0.30:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def predict(self, image_path: str) -> Dict:
        """
        Predict if image is real or fake using ensemble
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with ensemble prediction:
            {
                'verdict': 'REAL', 'FAKE', or 'UNCERTAIN',
                'confidence': float (0-100),
                'fake_probability': float (0-1),
                'individual_results': list of model results,
                'agreement_level': 'HIGH', 'MEDIUM', or 'LOW',
                'is_uncertain': bool,
                'recommendation': str
            }
        """
        print(f"\nAnalyzing: {Path(image_path).name}")
        print("-" * 60)
        
        # Get predictions from all models
        results = []
        
        print("Running SigLIP model")
        siglip_result = self.siglip.predict(image_path)
        results.append(siglip_result)
        print(f"{siglip_result['prediction']} ({siglip_result['confidence']:.1f}%)")
        
        print("Running ViT-v2 model")
        vit_v2_result = self.vit_v2.predict(image_path)
        results.append(vit_v2_result)
        print(f"{vit_v2_result['prediction']} ({vit_v2_result['confidence']:.1f}%)")
        
        print("Running ViT-Base model")
        vit_base_result = self.vit_base.predict(image_path)
        results.append(vit_base_result)
        print(f"{vit_base_result['prediction']} ({vit_base_result['confidence']:.1f}%)")
        
        # Calculate weighted ensemble probability
        weighted_fake_prob = (
            siglip_result['fake_probability'] * ENSEMBLE_WEIGHTS['siglip'] +
            vit_v2_result['fake_probability'] * ENSEMBLE_WEIGHTS['vit_v2'] +
            vit_base_result['fake_probability'] * ENSEMBLE_WEIGHTS['vit_base']
        )
        
        # Determine verdict
        if weighted_fake_prob > FAKE_THRESHOLD:
            verdict = "FAKE"
            confidence = weighted_fake_prob * 100
        elif weighted_fake_prob < REAL_THRESHOLD:
            verdict = "REAL"
            confidence = (1 - weighted_fake_prob) * 100
        else:
            verdict = "UNCERTAIN"
            confidence = 50.0
        
        # Check for disagreement
        is_uncertain = self.detect_disagreement(results)
        agreement_level = self.calculate_agreement_level(results)
        
        # Generate recommendation
        if agreement_level == 'HIGH' and confidence > 80:
            recommendation = f"High confidence {verdict.lower()} detection"
        elif agreement_level == 'MEDIUM':
            recommendation = f"Moderate confidence - {verdict.lower()} detected but with some uncertainty"
        elif is_uncertain or agreement_level == 'LOW':
            recommendation = "Models disagree - manual review recommended"
        else:
            recommendation = f"{verdict} detected"
        
        print("\n" + "=" * 60)
        print(f"ENSEMBLE VERDICT: {verdict}")
        print(f"Confidence: {confidence:.2f}%")
        print(f"Agreement: {agreement_level}")
        print("=" * 60)
        
        return {
            'verdict': verdict,
            'confidence': round(confidence, 2),
            'fake_probability': round(weighted_fake_prob, 4),
            'real_probability': round(1 - weighted_fake_prob, 4),
            'individual_results': results,
            'agreement_level': agreement_level,
            'is_uncertain': is_uncertain,
            'recommendation': recommendation,
            'weights_used': ENSEMBLE_WEIGHTS
        }
    
    def predict_batch(self, image_paths: List[str]) -> List[Dict]:
        """
        Predict multiple images
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of prediction dictionaries
        """
        results = []
        total = len(image_paths)
        
        print(f"\nProcessing {total} images...")
        print("=" * 60)
        
        for i, image_path in enumerate(image_paths, 1):
            print(f"\n[{i}/{total}] Processing: {Path(image_path).name}")
            result = self.predict(image_path)
            results.append(result)
        
        # Calculate summary statistics
        fake_count = sum(1 for r in results if r['verdict'] == 'FAKE')
        real_count = sum(1 for r in results if r['verdict'] == 'REAL')
        uncertain_count = sum(1 for r in results if r['verdict'] == 'UNCERTAIN')
        
        print(f"\n{'='*60}")
        print("BATCH SUMMARY")
        print(f"{'='*60}")
        print(f"Total: {total} images")
        print(f"FAKE: {fake_count} ({fake_count/total*100:.1f}%)")
        print(f"REAL: {real_count} ({real_count/total*100:.1f}%)")
        print(f"UNCERTAIN: {uncertain_count} ({uncertain_count/total*100:.1f}%)")
        print(f"{'='*60}\n")
        
        return results
    
    def __repr__(self):
        return (f"EnsembleDetector(models=3, device={self.device}, "
                f"weights={ENSEMBLE_WEIGHTS})")


