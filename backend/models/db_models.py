"""
Database Models
"""

from datetime import datetime
from database import get_detections_collection
from pymongo.errors import DuplicateKeyError


class DetectionResult:
    
    @staticmethod
    def create(file_hash, filename, content_type, result_data):
        """
        Create a new detection result
        """
        collection = get_detections_collection()
        
        # Prepare document
        document = {
            'file_hash': file_hash,
            'filename': filename,
            'content_type': content_type,
            'verdict': result_data.get('verdict'),
            'confidence': result_data.get('confidence'),
            'fake_probability': result_data.get('fake_probability'),
            'real_probability': result_data.get('real_probability'),
            'timestamp': datetime.utcnow(),
            'full_result': result_data
        }
        
        # Add content-specific fields
        if content_type == 'image':
            document['agreement_level'] = result_data.get('agreement_level')
            document['individual_results'] = result_data.get('individual_results', [])
            
        elif content_type == 'video':
            document['video_info'] = result_data.get('video_info', {})
            document['analysis'] = result_data.get('analysis', {})
            document['frames_analyzed'] = result_data.get('frames_analyzed', 0)
            document['agreement_level'] = result_data.get('agreement_level')
            document['suspicious_frames'] = result_data.get('suspicious_frames', [])
            document['processing_time'] = result_data.get('processing_time_seconds', 0)
        
        try:
            # Insert document
            result = collection.insert_one(document)
            document['_id'] = str(result.inserted_id)
            return document
            
        except DuplicateKeyError:
            # File already exists
            print(f"Duplicate file detected: {file_hash}")
            return None
    
    @staticmethod
    def find_by_hash(file_hash):
        """
        Find detection result by file hash
        """
        collection = get_detections_collection()
        result = collection.find_one({'file_hash': file_hash})
        
        if result:
            result['_id'] = str(result['_id'])
        
        return result
    
    @staticmethod
    def get_history(limit=50, content_type=None, verdict=None):
        """
        Get detection history
        """
        collection = get_detections_collection()
        
        # Build query
        query = {}
        if content_type:
            query['content_type'] = content_type
        if verdict:
            query['verdict'] = verdict
        
        # Get results sorted by timestamp
        cursor = collection.find(query).sort('timestamp', -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
        
        return results
    
    @staticmethod
    def get_statistics():
        """
        Get overall statistics
        """
        collection = get_detections_collection()
        
        # Total counts
        total_detections = collection.count_documents({})
        total_images = collection.count_documents({'content_type': 'image'})
        total_videos = collection.count_documents({'content_type': 'video'})
        
        # Verdict counts
        fake_count = collection.count_documents({'verdict': 'FAKE'})
        real_count = collection.count_documents({'verdict': 'REAL'})
        uncertain_count = collection.count_documents({'verdict': 'UNCERTAIN'})
        
        # Average confidence
        pipeline = [
            {'$group': {
                '_id': None,
                'avg_confidence': {'$avg': '$confidence'}
            }}
        ]
        avg_result = list(collection.aggregate(pipeline))
        avg_confidence = avg_result[0]['avg_confidence'] if avg_result else 0
        
        return {
            'total_detections': total_detections,
            'total_images': total_images,
            'total_videos': total_videos,
            'fake_count': fake_count,
            'real_count': real_count,
            'uncertain_count': uncertain_count,
            'average_confidence': round(avg_confidence, 2) if avg_confidence else 0
        }
    
    @staticmethod
    def search(query_text, limit=20):
        """
        Search detection results by filename
        """
        collection = get_detections_collection()
        
        # Search by filename (case-insensitive regex)
        regex_query = {'filename': {'$regex': query_text, '$options': 'i'}}
        
        cursor = collection.find(regex_query).sort('timestamp', -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
        
        return results
    
    @staticmethod
    def delete_by_hash(file_hash):
        """
        Delete detection result by hash
        """
        collection = get_detections_collection()
        result = collection.delete_one({'file_hash': file_hash})
        return result.deleted_count > 0
    
    @staticmethod
    def clear_all():
        """
        Clear all detection results 
        """
        collection = get_detections_collection()
        result = collection.delete_many({})
        return result.deleted_count
