"""
SightEngine API wrapper with rate limiting and usage tracking.
"""

import requests
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class SightEngineAPI:
    """
    SightEngine API client with 10k/month limit tracking.
    """
    
    def __init__(self):
        self.api_user = os.getenv('SIGHTENGINE_API_USER')
        self.api_secret = os.getenv('SIGHTENGINE_API_SECRET')
        self.base_url = "https://api.sightengine.com/1.0"
        self.usage_file = Path('api_usage.json')
        self.monthly_limit = 10000
        
        if not self.api_user or not self.api_secret:
            raise ValueError(
                "SightEngine credentials not found. "
            )
        
        self.load_usage()
    
    def load_usage(self):
        """Load usage tracking from file"""
        if self.usage_file.exists():
            data = json.loads(self.usage_file.read_text())
            self.calls_this_month = data.get('calls', 0)
            self.reset_date = datetime.fromisoformat(data.get('reset_date'))
            
            # Reset if new month
            if datetime.now().month != self.reset_date.month:
                self.calls_this_month = 0
                self.reset_date = self._get_next_reset_date()
                self.save_usage()
        else:
            self.calls_this_month = 0
            self.reset_date = self._get_next_reset_date()
            self.save_usage()
    
    def save_usage(self):
        """Save usage tracking to file"""
        self.usage_file.write_text(json.dumps({
            'calls': self.calls_this_month,
            'reset_date': self.reset_date.isoformat(),
            'limit': self.monthly_limit
        }, indent=2))
    
    def _get_next_reset_date(self):
        """Calculate next monthly reset date"""
        now = datetime.now()
        if now.month == 12:
            return datetime(now.year + 1, 1, 1)
        else:
            return datetime(now.year, now.month + 1, 1)
    
    def is_available(self):
        """Check if API is available (under limit)"""
        return self.calls_this_month < self.monthly_limit
    
    def get_usage_info(self):
        """Get current usage statistics"""
        return {
            'calls_used': self.calls_this_month,
            'calls_limit': self.monthly_limit,
            'calls_remaining': self.monthly_limit - self.calls_this_month,
            'percentage': round((self.calls_this_month / self.monthly_limit) * 100, 2),
            'reset_date': self.reset_date.isoformat(),
            'available': self.is_available()
        }
    
    def detect_fake(self, image_path):
        """
        Detect AI-generated content using SightEngine.
        
        Args:
            image_path: Path to image file
            
        Returns:
            dict: Detection results or error info
        """
        # Check availability
        if not self.is_available():
            return {
                'available': False,
                'reason': 'monthly_limit_reached',
                'reset_date': self.reset_date.isoformat(),
                'calls_used': self.calls_this_month,
                'calls_limit': self.monthly_limit
            }
        
        try:
            # Make API request
            with open(image_path, 'rb') as f:
                response = requests.post(
                    f'{self.base_url}/check.json',
                    files={'media': f},
                    data={
                        'models': 'genai',
                        'api_user': self.api_user,
                        'api_secret': self.api_secret
                    },
                    timeout=30
                )
            
            # Check response
            if response.status_code == 200:
                # Increment counter
                self.calls_this_month += 1
                self.save_usage()
                
                result = response.json()
                
                # Parse SightEngine response
                # AI-generated probability from 'type.ai_generated'
                ai_prob = result.get('type', {}).get('ai_generated', 0)
                
                # Determine verdict
                is_fake = ai_prob > 0.5
                confidence = ai_prob if is_fake else (1 - ai_prob)
                
                return {
                    'available': True,
                    'verdict': 'FAKE' if is_fake else 'REAL',
                    'confidence': round(confidence * 100, 2),
                    'fake_probability': round(ai_prob * 100, 2),
                    'real_probability': round((1 - ai_prob) * 100, 2),
                    'model_name': 'SightEngine',
                    'raw_response': result
                }
            
            elif response.status_code == 429:
                # Rate limit hit
                return {
                    'available': False,
                    'reason': 'rate_limit',
                    'error': 'API rate limit exceeded'
                }
            
            else:
                # Other error
                return {
                    'available': False,
                    'reason': 'api_error',
                    'status_code': response.status_code,
                    'error': response.text
                }
        
        except requests.exceptions.Timeout:
            return {
                'available': False,
                'reason': 'timeout',
                'error': 'API request timed out'
            }
        
        except Exception as e:
            return {
                'available': False,
                'reason': 'exception',
                'error': str(e)
            }


# Test script
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python sightengine_api.py <image_path>")
        sys.exit(1)
    
    api = SightEngineAPI()
    
    print("\nAPI Usage Info:")
    usage = api.get_usage_info()
    print(f"  Calls used: {usage['calls_used']} / {usage['calls_limit']}")
    print(f"  Percentage: {usage['percentage']}%")
    print(f"  Reset date: {usage['reset_date']}")
    
    print("\nRunning detection...")
    result = api.detect_fake(sys.argv[1])
    
    if result['available']:
        print(f"\n✓ Verdict: {result['verdict']}")
        print(f"  Confidence: {result['confidence']:.2f}%")
        print(f"  Fake probability: {result['fake_probability']:.2f}%")
    else:
        print(f"\n✗ API unavailable: {result['reason']}")