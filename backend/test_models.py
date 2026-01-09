"""
Test script for deepfake detection models
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from models.ensemble import EnsembleDetector


def test_single_image(image_path: str):
    
    print("\n" + "="*70)
    print(" DEEPFAKE DETECTION TEST")
    print("="*70)
    
    # Check if image exists
    if not Path(image_path).exists():
        print(f"\nError: Image not found: {image_path}")
        return
    
    print(f"\nImage: {image_path}")
    print(f"Size: {Path(image_path).stat().st_size / 1024:.1f} KB")
    
    # Initialize ensemble
    print("\nInitializing detector")
    ensemble = EnsembleDetector()
    
    # Run prediction
    result = ensemble.predict(image_path)
    
    # Display results
    print("\n" + "="*70)
    print(" FINAL RESULTS")
    print("="*70)
    
    # Verdict with color
    verdict_color = {
        'FAKE': '🔴',
        'REAL': '🟢',
        'UNCERTAIN': '🟡'
    }
    
    print(f"\n{verdict_color.get(result['verdict'], '⚪')} VERDICT: {result['verdict']}")
    print(f"   Confidence: {result['confidence']:.2f}%")
    print(f"   Agreement: {result['agreement_level']}")
    print(f"   Recommendation: {result['recommendation']}")
    
    print(f"\nProbabilities:")
    print(f"   Fake: {result['fake_probability']:.4f} ({result['fake_probability']*100:.2f}%)")
    print(f"   Real: {result['real_probability']:.4f} ({result['real_probability']*100:.2f}%)")
    
    print(f"\nIndividual Models:")
    for model in result['individual_results']:
        icon = '🔴' if model['prediction'] == 'FAKE' else '🟢'
        print(f"   {icon} {model['model']:12} → {model['prediction']:4} ({model['confidence']:6.2f}%)")
    
    print("\n" + "="*70)
    
    if result['is_uncertain']:
        print("\nWarning: Models show significant disagreement")
        print("Consider manual review or additional analysis")
    
    print()


def main():
    if len(sys.argv) < 2:
        print("\nError: No image provided")
        sys.exit(1)
    
    image_path = sys.argv[1]
    test_single_image(image_path)


if __name__ == "__main__":
    main()
