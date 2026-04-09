"""
Manages collection of user-uploaded files for model retraining.

Limits:
- 100 files total (50 real + 50 fake)
- High confidence only (>85%)
- Hash-based duplicate detection
- Labels from SightEngine API
"""

import os
import shutil
from pathlib import Path
import json
from datetime import datetime
from utils.hash_utils import calculate_file_hash


class DataCollector:
    """
    Collects user-uploaded files for future model retraining.
    """
    
    def __init__(self, storage_dir='storage/training_data'):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.storage_dir / 'metadata.json'
        self.load_metadata()
    
    def load_metadata(self):
        """Load collection metadata"""
        if self.metadata_file.exists():
            self.metadata = json.loads(self.metadata_file.read_text())
        else:
            self.metadata = {
                'current_round': 1,
                'rounds': {},
                'total_collected': 0
            }
            self.save_metadata()
        
        # Ensure current round exists
        round_num = str(self.metadata['current_round'])
        if round_num not in self.metadata['rounds']:
            self.metadata['rounds'][round_num] = {
                'real_count': 0,
                'fake_count': 0,
                'total': 0,
                'hashes': [],
                'started': datetime.now().isoformat(),
                'status': 'collecting'
            }
            self.save_metadata()
    
    def save_metadata(self):
        """Save metadata to file"""
        self.metadata_file.write_text(json.dumps(self.metadata, indent=2))
    
    def get_current_round_info(self):
        """Get info about current collection round"""
        round_num = str(self.metadata['current_round'])
        return self.metadata['rounds'][round_num]
    
    def can_save_file(self, label):
        """Check if we can save more files of this label"""
        info = self.get_current_round_info()
        
        REAL_LIMIT = 50
        FAKE_LIMIT = 50
        
        if label == 'REAL':
            return info['real_count'] < REAL_LIMIT
        else:  # FAKE
            return info['fake_count'] < FAKE_LIMIT
    
    def is_duplicate(self, file_hash):
        """Check if file already saved"""
        info = self.get_current_round_info()
        return file_hash in info['hashes']
    
    def save_file(self, file_path, label, confidence, source='sightengine'):
        """
        Save file for future retraining.
        
        Args:
            file_path: Path to image file
            label: 'REAL' or 'FAKE'
            confidence: Detection confidence (0-100)
            source: Which detector provided the label
        
        Returns:
            dict: Save status and info
        """
        # Calculate hash
        with open(file_path, 'rb') as f:
            file_hash = calculate_file_hash(f)
        
        # Check if duplicate
        if self.is_duplicate(file_hash):
            return {
                'saved': False,
                'reason': 'duplicate',
                'hash': file_hash[:16]
            }
        
        # Check if can save
        if not self.can_save_file(label):
            info = self.get_current_round_info()
            return {
                'saved': False,
                'reason': 'limit_reached',
                'current_count': info[f'{label.lower()}_count'],
                'limit': 50
            }
        
        # Check confidence threshold
        CONFIDENCE_THRESHOLD = 85.0
        if confidence < CONFIDENCE_THRESHOLD:
            return {
                'saved': False,
                'reason': 'low_confidence',
                'confidence': confidence,
                'threshold': CONFIDENCE_THRESHOLD
            }
        
        # Save file
        round_num = self.metadata['current_round']
        label_folder = self.storage_dir / f'round_{round_num}' / label.lower()
        label_folder.mkdir(parents=True, exist_ok=True)
        
        # Filename: timestamp_hash.jpg
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file_hash[:8]}.jpg"
        dest_path = label_folder / filename
        
        shutil.copy(file_path, dest_path)
        
        # Update metadata
        info = self.get_current_round_info()
        info['hashes'].append(file_hash)
        info[f'{label.lower()}_count'] += 1
        info['total'] += 1
        self.metadata['total_collected'] += 1
        
        self.save_metadata()
        
        return {
            'saved': True,
            'path': str(dest_path),
            'hash': file_hash[:16],
            'round': round_num,
            'label': label,
            'count': info['total']
        }
    
    def is_ready_for_retraining(self):
        """Check if we have 100 files (50 real + 50 fake)"""
        info = self.get_current_round_info()
        return info['real_count'] >= 50 and info['fake_count'] >= 50
    
    def start_new_round(self):
        """Start new collection round after retraining"""
        # Mark current round as completed
        current_round = str(self.metadata['current_round'])
        self.metadata['rounds'][current_round]['status'] = 'completed'
        self.metadata['rounds'][current_round]['completed'] = datetime.now().isoformat()
        
        # Start new round
        self.metadata['current_round'] += 1
        new_round = str(self.metadata['current_round'])
        
        self.metadata['rounds'][new_round] = {
            'real_count': 0,
            'fake_count': 0,
            'total': 0,
            'hashes': [],
            'started': datetime.now().isoformat(),
            'status': 'collecting'
        }
        
        self.save_metadata()
    
    def get_statistics(self):
        """Get collection statistics"""
        info = self.get_current_round_info()
        
        return {
            'current_round': self.metadata['current_round'],
            'real_collected': info['real_count'],
            'real_limit': 50,
            'real_percentage': round((info['real_count'] / 50) * 100, 1),
            'fake_collected': info['fake_count'],
            'fake_limit': 50,
            'fake_percentage': round((info['fake_count'] / 50) * 100, 1),
            'total_collected': info['total'],
            'total_limit': 100,
            'percentage': round((info['total'] / 100) * 100, 1),
            'ready_for_retraining': self.is_ready_for_retraining(),
            'all_time_total': self.metadata['total_collected'],
            'status': info['status']
        }


# Test
if __name__ == "__main__":
    collector = DataCollector()
    stats = collector.get_statistics()
    
    print("\n" + "="*50)
    print("Data Collection Statistics")
    print("="*50)
    print(f"Round: {stats['current_round']}")
    print(f"Real: {stats['real_collected']}/50 ({stats['real_percentage']}%)")
    print(f"Fake: {stats['fake_collected']}/50 ({stats['fake_percentage']}%)")
    print(f"Total: {stats['total_collected']}/100 ({stats['percentage']}%)")
    print(f"Ready: {stats['ready_for_retraining']}")
    print("="*50)