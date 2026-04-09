"""
Aggregates frame-by-frame detection results for video analysis (SightEngine + MobileNetV4).
"""


class VideoAggregator:
    """
    Aggregates detection results across video frames.
    """
    
    def aggregate_frame_results(self, frame_results):
        """
        Aggregate detection results from multiple video frames.
        
        Args:
            frame_results: List of detection results, one per frame
                Each result has 'detectors' dict with sightengine/mobilenet
        
        Returns:
            dict: Aggregated video-level results
        """
        if not frame_results:
            return self._empty_result()
        
        # Collect verdicts and confidences from all frames
        sightengine_verdicts = []
        mobilenet_verdicts = []
        final_verdicts = []
        confidences = []
        
        # Timeline data
        confidence_timeline = []
        suspicious_frames = []
        
        for idx, frame_result in enumerate(frame_results):
            final = frame_result.get('final', {})
            detectors = frame_result.get('detectors', {})
            
            # Collect final verdicts
            if final.get('verdict'):
                final_verdicts.append(final['verdict'])
                confidences.append(final.get('confidence', 0))
                
                # Timeline
                confidence_timeline.append({
                    'frame': idx,
                    'confidence': final.get('confidence', 0),
                    'verdict': final.get('verdict')
                })
                
                # Mark suspicious frames (high fake confidence)
                if final.get('verdict') == 'FAKE' and final.get('confidence', 0) > 70:
                    suspicious_frames.append({
                        'frame': idx,
                        'confidence': final.get('confidence'),
                        'timestamp': round(idx * 1.0, 2)  # Assuming 1 FPS
                    })
            
            # Collect individual detector results
            if detectors.get('sightengine', {}).get('available'):
                sightengine_verdicts.append(detectors['sightengine'].get('verdict'))
            
            if detectors.get('mobilenet', {}).get('available'):
                mobilenet_verdicts.append(detectors['mobilenet'].get('verdict'))
        
        # Calculate overall verdict
        fake_count = final_verdicts.count('FAKE')
        real_count = final_verdicts.count('REAL')
        total_frames = len(final_verdicts)
        
        if total_frames == 0:
            return self._empty_result()
        
        fake_percentage = (fake_count / total_frames) * 100
        
        # Determine final verdict
        if fake_percentage >= 50:
            overall_verdict = 'FAKE'
            overall_confidence = fake_percentage
        else:
            overall_verdict = 'REAL'
            overall_confidence = 100 - fake_percentage
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Model breakdown
        model_breakdown = []
        
        if sightengine_verdicts:
            se_fake = sightengine_verdicts.count('FAKE')
            se_total = len(sightengine_verdicts)
            model_breakdown.append({
                'model': 'SightEngine',
                'fake_frames': se_fake,
                'real_frames': se_total - se_fake,
                'total_frames': se_total,
                'fake_percentage': round((se_fake / se_total) * 100, 2)
            })
        
        if mobilenet_verdicts:
            mn_fake = mobilenet_verdicts.count('FAKE')
            mn_total = len(mobilenet_verdicts)
            model_breakdown.append({
                'model': 'MobileNetV4',
                'fake_frames': mn_fake,
                'real_frames': mn_total - mn_fake,
                'total_frames': mn_total,
                'fake_percentage': round((mn_fake / mn_total) * 100, 2)
            })
        
        # Agreement analysis
        agreement_level = self._calculate_agreement(
            sightengine_verdicts,
            mobilenet_verdicts
        )
        
        # Detailed analysis
        analysis = {
            'total_frames_analyzed': total_frames,
            'fake_frames': fake_count,
            'real_frames': real_count,
            'fake_percentage': round(fake_percentage, 2),
            'real_percentage': round(100 - fake_percentage, 2),
            'average_confidence': round(avg_confidence, 2),
            'consistency_score': self._calculate_consistency(final_verdicts),
            'suspicious_frame_count': len(suspicious_frames)
        }
        
        return {
            'verdict': overall_verdict,
            'confidence': round(overall_confidence, 2),
            'fake_probability': round(fake_percentage, 2),
            'real_probability': round(100 - fake_percentage, 2),
            'agreement_level': agreement_level,
            'analysis': analysis,
            'confidence_timeline': confidence_timeline,
            'suspicious_frames': suspicious_frames[:10],  # Top 10 most suspicious
            'model_breakdown': model_breakdown
        }
    
    def _calculate_agreement(self, sightengine_verdicts, mobilenet_verdicts):
        """Calculate agreement between two detectors across frames"""
        if not sightengine_verdicts or not mobilenet_verdicts:
            return 'single_detector'
        
        # Compare verdicts frame by frame
        min_len = min(len(sightengine_verdicts), len(mobilenet_verdicts))
        agreements = 0
        
        for i in range(min_len):
            if sightengine_verdicts[i] == mobilenet_verdicts[i]:
                agreements += 1
        
        agreement_percentage = (agreements / min_len) * 100 if min_len > 0 else 0
        
        if agreement_percentage >= 80:
            return 'strong_agreement'
        elif agreement_percentage >= 60:
            return 'agreement'
        else:
            return 'disagreement'
    
    def _calculate_consistency(self, verdicts):
        """
        Calculate how consistent verdicts are across frames.
        Higher score = more consistent (all frames similar verdict)
        """
        if not verdicts:
            return 0
        
        fake_count = verdicts.count('FAKE')
        real_count = verdicts.count('REAL')
        total = len(verdicts)
        
        # Consistency is how dominant the majority verdict is
        majority = max(fake_count, real_count)
        consistency = (majority / total) * 100
        
        return round(consistency, 2)
    
    def _empty_result(self):
        """Return empty result structure"""
        return {
            'verdict': 'UNCERTAIN',
            'confidence': 0,
            'fake_probability': 0,
            'real_probability': 0,
            'agreement_level': 'unknown',
            'analysis': {
                'total_frames_analyzed': 0,
                'fake_frames': 0,
                'real_frames': 0,
                'fake_percentage': 0,
                'real_percentage': 0,
                'average_confidence': 0,
                'consistency_score': 0,
                'suspicious_frame_count': 0
            },
            'confidence_timeline': [],
            'suspicious_frames': [],
            'model_breakdown': []
        }