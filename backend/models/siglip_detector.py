"""
SigLIP Model Wrapper for AI, Deepfake Detection
"""

import torch
from transformers import AutoImageProcessor, SiglipForImageClassification
from PIL import Image
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import MODELS, MODEL_CACHE_DIR


class SigLIPDetector:
    """
    SigLIP-based deepfake detector
    """
    
    def __init__(self, device: str = None):
        """
        Initialize SigLIP detector
        
        Args:
            device: Device to run model on ('cuda', 'cpu', or None for auto)
        """
        self.model_name = MODELS['siglip']['name']
        self.input_size = MODELS['siglip']['input_size']
        
        # Set device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        print(f"Loading model on {self.device}")
        
        # Load processor and model
        self.processor = AutoImageProcessor.from_pretrained(
            self.model_name,
            cache_dir=MODEL_CACHE_DIR
        )
        
        self.model = SiglipForImageClassification.from_pretrained(
            self.model_name,
            cache_dir=MODEL_CACHE_DIR
        )
        
        # Move model to device and set to eval mode
        self.model.to(self.device)
        self.model.eval()
    
    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """
        Preprocess image for SigLIP model
        
        Args:
            image: PIL Image
            
        Returns:
            Preprocessed tensor ready for model
        """
        # Resize to model's input size
        image = image.resize((self.input_size, self.input_size), Image.Resampling.LANCZOS)
        
        # Process with model's processor
        inputs = self.processor(images=image, return_tensors="pt")
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        return inputs
    
    @torch.no_grad()
    def predict(self, image_path: str) -> dict:
        """
        Predict if image is real or fake
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with prediction results:
            {
                'prediction': 'REAL' or 'FAKE',
                'confidence': float (0-100),
                'fake_probability': float (0-1),
                'real_probability': float (0-1),
                'logits': list of raw logits
            }
        """
        # Load image
        image = Image.open(image_path).convert('RGB')
        
        # Preprocess
        inputs = self.preprocess(image)
        
        # Run inference
        outputs = self.model(**inputs)
        logits = outputs.logits
        
        # Get probabilities
        probs = torch.softmax(logits, dim=-1)
        
        # Get predicted class (0 = Real, 1 = Fake typically)
        predicted_class = torch.argmax(probs, dim=-1).item()
        
        # Extract probabilities
        real_prob = probs[0][0].item()
        fake_prob = probs[0][1].item()
        
        # Determine prediction
        if predicted_class == 1:
            prediction = "FAKE"
            confidence = fake_prob * 100
        else:
            prediction = "REAL"
            confidence = real_prob * 100
        
        return {
            'model': 'SigLIP',
            'prediction': prediction,
            'confidence': round(confidence, 2),
            'fake_probability': round(fake_prob, 4),
            'real_probability': round(real_prob, 4),
            'logits': logits[0].cpu().numpy().tolist()
        }
    
    def predict_batch(self, image_paths: list) -> list:
        """
        Predict multiple images in batch
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of prediction dictionaries
        """
        results = []
        for image_path in image_paths:
            result = self.predict(image_path)
            results.append(result)
        return results
    
    def __repr__(self):
        return f"SigLIPDetector(model={self.model_name}, device={self.device})"


# Test function
if __name__ == "__main__":
    print("Testing current Detector")
    
    detector = SigLIPDetector()
    print(f"\nDetector initialized: {detector}")
    print(f"Input size: {detector.input_size}x{detector.input_size}")
    print(f"Device: {detector.device}")
    
    # Test with sample image 
    import sys
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"\nTesting with image: {image_path}")
        result = detector.predict(image_path)
        print(f"\nResults:")
        print(f"  Prediction: {result['prediction']}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Fake probability: {result['fake_probability']}")
        print(f"  Real probability: {result['real_probability']}")