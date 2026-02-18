"""
Video Aggregator Module
Aggregates frame-by-frame detection results into final video verdict
"""

from typing import List, Dict, Tuple
import statistics


class VideoAggregator:
    """Aggregates frame detection results for video verdict"""
    
    # Thresholds
    FAKE_THRESHOLD = 0.6  # >60% = FAKE
    REAL_THRESHOLD = 0.4  # <40% = REAL
    # Between 0.4-0.6 = UNCERTAIN
    
    def __init__(self):
        """Initialize aggregator"""
        pass
    
    def aggregate_frame_results(self, frame_results: List[Dict]) -> Dict:
        """
        Aggregate individual frame results into video verdict
        
        Args:
            frame_results: List of detection results, each containing:
                {
                    'frame_index': int,
                    'verdict': str,
                    'confidence': float,
                    'fake_probability': float,
                    'real_probability': float,
                    'individual_results': list
                }
        
        Returns:
            Aggregated video result
        """
        if not frame_results:
            return {
                'verdict': 'ERROR',
                'confidence': 0,
                'message': 'No frames to analyze'
            }
        
        total_frames = len(frame_results)
        
        # Count verdicts
        fake_count = sum(1 for r in frame_results if r['verdict'] == 'FAKE')
        real_count = sum(1 for r in frame_results if r['verdict'] == 'REAL')
        uncertain_count = sum(1 for r in frame_results if r['verdict'] == 'UNCERTAIN')
        
        # Calculate average probabilities
        avg_fake_prob = sum(r['fake_probability'] for r in frame_results) / total_frames
        avg_real_prob = sum(r['real_probability'] for r in frame_results) / total_frames
        
        # Determine video verdict based on majority and average probability
        fake_ratio = fake_count / total_frames
        
        if avg_fake_prob > self.FAKE_THRESHOLD:
            verdict = 'FAKE'
            confidence = avg_fake_prob * 100
        elif avg_fake_prob < self.REAL_THRESHOLD:
            verdict = 'REAL'
            confidence = avg_real_prob * 100
        else:
            verdict = 'UNCERTAIN'
            confidence = 50 + abs(avg_fake_prob - 0.5) * 100
        
        # Calculate agreement across frames
        agreement_level = self._calculate_frame_agreement(frame_results)
        
        # Get confidence timeline
        confidence_timeline = [r['confidence'] for r in frame_results]
        
        # Identify suspicious frames (high fake probability)
        suspicious_frames = self._detect_suspicious_frames(frame_results)
        
        # Calculate model-level aggregation
        model_aggregation = self._aggregate_model_results(frame_results)
        
        return {
            'verdict': verdict,
            'confidence': round(confidence, 2),
            'fake_probability': round(avg_fake_prob, 4),
            'real_probability': round(avg_real_prob, 4),
            'analysis': {
                'total_frames_analyzed': total_frames,
                'fake_frames': fake_count,
                'real_frames': real_count,
                'uncertain_frames': uncertain_count,
                'fake_frame_ratio': round(fake_ratio, 4)
            },
            'agreement_level': agreement_level,
            'confidence_timeline': confidence_timeline,
            'suspicious_frames': suspicious_frames,
            'model_breakdown': model_aggregation,
            'frame_results': frame_results  # Include detailed frame results
        }
    
    def _calculate_frame_agreement(self, frame_results: List[Dict]) -> str:
        """
        Calculate how much frames agree with each other
        
        Args:
            frame_results: List of frame results
            
        Returns:
            'HIGH', 'MEDIUM', or 'LOW'
        """
        if len(frame_results) < 2:
            return 'HIGH'
        
        # Calculate standard deviation of fake probabilities
        fake_probs = [r['fake_probability'] for r in frame_results]
        
        try:
            std_dev = statistics.stdev(fake_probs)
            
            if std_dev < 0.15:
                return 'HIGH'
            elif std_dev < 0.30:
                return 'MEDIUM'
            else:
                return 'LOW'
        except:
            return 'MEDIUM'
    
    def _detect_suspicious_frames(self, frame_results: List[Dict], threshold: float = 0.7) -> List[int]:
        """
        Identify frames with high fake probability
        
        Args:
            frame_results: List of frame results
            threshold: Fake probability threshold (default: 0.7)
            
        Returns:
            List of frame indices
        """
        suspicious = []
        
        for result in frame_results:
            if result['fake_probability'] >= threshold:
                suspicious.append(result['frame_index'])
        
        return suspicious
    
    def _aggregate_model_results(self, frame_results: List[Dict]) -> List[Dict]:
        """
        Aggregate results for each individual model across all frames
        
        Args:
            frame_results: List of frame results
            
        Returns:
            List of model-level aggregated results
        """
        if not frame_results or 'individual_results' not in frame_results[0]:
            return []
        
        # Get model names from first frame
        models = frame_results[0]['individual_results']
        model_aggregation = []
        
        for model_info in models:
            model_name = model_info['model']
            
            # Collect predictions for this model across all frames
            model_predictions = []
            
            for frame_result in frame_results:
                # Find this model's result in the frame
                for m in frame_result['individual_results']:
                    if m['model'] == model_name:
                        model_predictions.append(m)
                        break
            
            if not model_predictions:
                continue
            
            # Calculate averages
            avg_confidence = sum(m['confidence'] for m in model_predictions) / len(model_predictions)
            fake_count = sum(1 for m in model_predictions if m['prediction'] == 'FAKE')
            
            # Determine overall prediction
            if fake_count / len(model_predictions) > 0.6:
                prediction = 'FAKE'
            elif fake_count / len(model_predictions) < 0.4:
                prediction = 'REAL'
            else:
                prediction = 'UNCERTAIN'
            
            model_aggregation.append({
                'model': model_name,
                'prediction': prediction,
                'confidence': round(avg_confidence, 2),
                'fake_frame_count': fake_count,
                'real_frame_count': len(model_predictions) - fake_count
            })
        
        return model_aggregation
    
    def calculate_confidence_timeline(self, frame_results: List[Dict]) -> List[float]:
        """
        Extract confidence timeline from frame results
        
        Args:
            frame_results: List of frame results
            
        Returns:
            List of confidence scores
        """
        return [r['confidence'] for r in frame_results]
    
    def get_frame_statistics(self, frame_results: List[Dict]) -> Dict:
        """
        Calculate statistical measures across frames
        
        Args:
            frame_results: List of frame results
            
        Returns:
            Dictionary with statistics
        """
        if not frame_results:
            return {}
        
        confidences = [r['confidence'] for r in frame_results]
        fake_probs = [r['fake_probability'] for r in frame_results]
        
        return {
            'confidence': {
                'mean': round(statistics.mean(confidences), 2),
                'median': round(statistics.median(confidences), 2),
                'std_dev': round(statistics.stdev(confidences), 2) if len(confidences) > 1 else 0,
                'min': round(min(confidences), 2),
                'max': round(max(confidences), 2)
            },
            'fake_probability': {
                'mean': round(statistics.mean(fake_probs), 4),
                'median': round(statistics.median(fake_probs), 4),
                'std_dev': round(statistics.stdev(fake_probs), 4) if len(fake_probs) > 1 else 0
            }
        }


# Helper function for easy use
def aggregate_video_results(frame_results: List[Dict]) -> Dict:
    """
    Aggregate frame results into video verdict
    
    Args:
        frame_results: List of detection results
        
    Returns:
        Aggregated video result
    """
    aggregator = VideoAggregator()
    return aggregator.aggregate_frame_results(frame_results)
