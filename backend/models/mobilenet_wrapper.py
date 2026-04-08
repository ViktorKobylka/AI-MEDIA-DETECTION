"""
Wrapper for MobileNetV4 detector to integrate with Flask API.
Provides consistent interface matching the existing ensemble detector.
"""

import os
from pathlib import Path
from models.nn_detector import NNDetector


class MobileNetDetector:
    """
    Wrapper for MobileNetV4 deepfake detector.
    
    Provides unified interface for Flask integration.
    """
    
    def __init__(self, model_path="detector_model.pth"):
        """
        Initialize MobileNetV4 detector.
        
        Args:
            model_path: Path to the trained model checkpoint
        """
        self.model_path = Path(model_path)
        
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model checkpoint not found at {self.model_path}. "
                f"Please ensure detector_model.pth is in the backend directory."
            )
        
        print(f"Loading MobileNetV4 from {self.model_path}...")
        self.detector = NNDetector(model_path=self.model_path)
        
        # Get training metrics
        metrics = self.detector.training_metrics
        print(f"✓ MobileNetV4 loaded successfully!")
        if metrics.get('f1'):
            print(f"  - F1 Score: {metrics['f1']:.2f}%")
            print(f"  - Real Accuracy: {metrics.get('real_acc', 0):.2f}%")
            print(f"  - Fake Accuracy: {metrics.get('fake_acc', 0):.2f}%")
    
    def predict(self, image_path):
        """
        Detect if image is AI-generated.
        
        Args:
            image_path: Path to image file
            
        Returns:
            dict: Detection results in unified format
        """
        # Get prediction from MobileNetV4
        result = self.detector.predict(image_path)
        
        # Convert to unified format
        fake_prob = result['final_score']
        real_prob = 1 - fake_prob
        
        # Determine verdict
        verdict = result['prediction'].upper()  # "fake" -> "FAKE", "real" -> "REAL"
        
        # Confidence is the probability of the predicted class
        if verdict == 'FAKE':
            confidence = fake_prob * 100
        else:
            confidence = real_prob * 100
        
        return {
            'verdict': verdict,
            'confidence': round(confidence, 2),
            'fake_probability': round(fake_prob * 100, 2),
            'real_probability': round(real_prob * 100, 2),
            'model_name': 'MobileNetV4-Conv-Small',
            'raw_score': round(fake_prob, 6)
        }
    
    def get_model_info(self):
        """Get information about the loaded model."""
        metrics = self.detector.training_metrics
        return {
            'model_name': 'MobileNetV4-Conv-Small',
            'architecture': 'mobilenetv4_conv_small.e2400_r224_in1k',
            'training_metrics': {
                'f1_score': metrics.get('f1'),
                'real_accuracy': metrics.get('real_acc'),
                'fake_accuracy': metrics.get('fake_acc'),
                'epoch': metrics.get('epoch')
            }
        }


# Test script
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mobilenet_wrapper.py <image_path>")
        sys.exit(1)
    
    detector = MobileNetDetector()
    result = detector.predict(sys.argv[1])
    
    print("\n" + "="*50)
    print("MobileNetV4 Detection Result")
    print("="*50)
    print(f"Verdict: {result['verdict']}")
    print(f"Confidence: {result['confidence']:.2f}%")
    print(f"Fake Probability: {result['fake_probability']:.2f}%")
    print(f"Real Probability: {result['real_probability']:.2f}%")
    print("="*50)
