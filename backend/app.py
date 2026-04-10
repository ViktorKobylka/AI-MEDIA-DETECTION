"""
Flask API for AI-Generated Image Detection

REST API for deepfake detection using MobileNetV4 + SightEngine dual detector system.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from pathlib import Path
from datetime import datetime

from database import db_config
from models.db_models import DetectionResult
from utils.hash_utils import calculate_file_hash

# Initialize components
sightengine_api = None
mobilenet_detector = None
data_collector = None
db_connected = False

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for React frontend
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max for images
app.config['MAX_VIDEO_SIZE'] = 50 * 1024 * 1024  # 50MB max for videos
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webp'}
app.config['ALLOWED_VIDEO_EXTENSIONS'] = {'mp4', 'avi', 'mov'}

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
print("Connecting to database...")
db_connected = db_config.connect()
if not db_connected:
    print("⚠ Database not available")
else:
    print("✓ Connected to MongoDB")

# Initialize MobileNetV4 detector
print("Initializing MobileNetV4 detector...")
try:
    from models.mobilenet_wrapper import MobileNetDetector
    mobilenet_detector = MobileNetDetector()
    print("✓ MobileNetV4 ready!")
except Exception as e:
    print(f"✗ MobileNetV4 error: {e}")
    mobilenet_detector = None


# Initialize SightEngine API
print("Initializing SightEngine API...")
try:
    from services.sightengine_api import SightEngineAPI
    sightengine_api = SightEngineAPI()
    usage = sightengine_api.get_usage_info()
    print(f"✓ SightEngine ready! ({usage['calls_used']}/{usage['calls_limit']} calls used)")
except Exception as e:
    print(f"✗ SightEngine error: {e}")
    sightengine_api = None

# Initialize Data Collector
print("Initializing Data Collector...")
try:
    from services.data_collector import DataCollector
    data_collector = DataCollector()
    stats = data_collector.get_statistics()
    print(f"✓ Data Collector ready! ({stats['total_collected']}/100 files collected)")
except Exception as e:
    print(f"✗ Data Collector error: {e}")
    data_collector = None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def allowed_video(filename):
    """Check if video file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_VIDEO_EXTENSIONS']


def cleanup_old_files():
    """Clean up files older than 1 hour"""
    try:
        folder = Path(app.config['UPLOAD_FOLDER'])
        current_time = datetime.now().timestamp()
        
        for file in folder.glob('*'):
            if file.is_file() and (current_time - file.stat().st_mtime) > 3600:
                file.unlink()
    except:
        pass


def aggregate_dual_results(se_result, mn_result):
    """
    Aggregate results from both detectors with SightEngine priority.
    
    Args:
        se_result: SightEngine API result dict
        mn_result: MobileNetV4 result dict
    
    Returns:
        tuple: (verdict, confidence, agreement, fake_prob, real_prob)
    """
    se_available = se_result and se_result.get('available', False)
    mn_available = mn_result and mn_result.get('available', False)
    
    # Determine agreement
    if se_available and mn_available:
        se_verdict = se_result.get('verdict')
        mn_verdict = mn_result.get('verdict')
        
        if se_verdict == mn_verdict:
            agreement = 'strong_agreement'
        else:
            agreement = 'disagreement'
    elif se_available or mn_available:
        agreement = 'single_detector'
    else:
        agreement = 'unknown'
    
    # SightEngine priority
    if se_available:
        verdict = se_result.get('verdict')
        confidence = se_result.get('confidence')
        fake_prob = se_result.get('fake_probability', 0)
        real_prob = se_result.get('real_probability', 0)
        
        # If both agree, average the confidence and probabilities
        if mn_available and se_result.get('verdict') == mn_result.get('verdict'):
            confidence = (se_result.get('confidence', 0) + mn_result.get('confidence', 0)) / 2
            fake_prob = (se_result.get('fake_probability', 0) + mn_result.get('fake_probability', 0)) / 2
            real_prob = (se_result.get('real_probability', 0) + mn_result.get('real_probability', 0)) / 2
            
        return verdict, confidence, agreement, fake_prob, real_prob
    
    # Fallback to MobileNet
    elif mn_available:
        return (
            mn_result.get('verdict'),
            mn_result.get('confidence'),
            agreement,
            mn_result.get('fake_probability', 0),
            mn_result.get('real_probability', 0)
        )
    
    # Both unavailable
    return 'UNCERTAIN', 0, 'unknown', 0, 0

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'mobilenet_ready': mobilenet_detector is not None,
        'sightengine_ready': sightengine_api is not None,
        'database_connected': db_connected
    })


@app.route('/api/detect_mobilenet', methods=['POST'])
def detect_mobilenet():
    """
    Test endpoint for MobileNetV4 detector only
    
    Request: multipart/form-data with 'file'
    Response: JSON with detection results
    """
    if mobilenet_detector is None:
        return jsonify({
            'success': False,
            'error': 'MobileNetV4 detector not available'
        }), 503
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': f'Invalid format. Allowed: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
        }), 400
    
    filepath = None
    
    try:
        # Clean up old files
        cleanup_old_files()
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        file.save(filepath)
        
        # Run MobileNetV4 detection
        result = mobilenet_detector.predict(filepath)
        
        # Clean up
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'detector': 'MobileNetV4',
            'result': result
        })
        
    except Exception as e:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/detect_dual', methods=['POST'])
def detect_dual():
    """
    Dual detection endpoint: SightEngine + MobileNetV4
    
    Request: multipart/form-data with 'file'
    Response: JSON with both detector results
    """
    if not mobilenet_detector:
        return jsonify({
            'success': False,
            'error': 'MobileNetV4 detector not available'
        }), 503
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': f'Invalid format. Allowed: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
        }), 400
    
    filepath = None
    
    try:
        import time
        start_time = time.time()
        
        # Calculate file hash
        file_hash = calculate_file_hash(file)
        
        # Check cache (if database connected)
        if db_connected:
            existing_result = DetectionResult.find_by_hash(file_hash)
            if existing_result:
                print(f"✓ Cache hit for hash: {file_hash[:16]}...")
                
                # Reconstruct full response from cached data
                cached_response = {
                    'success': True,
                    'cached': True,
                    'content_type': 'image',
                    'verdict': existing_result.get('verdict'),
                    'confidence': existing_result.get('confidence'),
                    'fake_probability': existing_result.get('fake_probability', 0),
                    'real_probability': existing_result.get('real_probability', 0),
                    'agreement_level': existing_result.get('agreement_level'),
                    'detectors': existing_result.get('full_result', {}).get('detectors', {}),
                    'processing_time_seconds': existing_result.get('full_result', {}).get('processing_time_seconds', 0),
                    'timestamp': existing_result['timestamp'].isoformat()
                }
                
                return jsonify(cached_response)
        
        # Clean up old files
        cleanup_old_files()
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        file.save(filepath)
        
        # Run both detectors
        se_result = None
        
        # 1. SightEngine API
        if sightengine_api:
            se_result = sightengine_api.detect_fake(filepath)
        
        # 2. MobileNetV4
        mn_result = mobilenet_detector.predict(filepath)
        
        # 3. Aggregate results with new format
        final_verdict, final_confidence, agreement, fake_prob, real_prob = aggregate_dual_results(
            se_result if se_result else {'available': False},
            {
                'available': True,
                'verdict': mn_result['verdict'],
                'confidence': mn_result['confidence'],
                'fake_probability': mn_result['fake_probability'],
                'real_probability': mn_result['real_probability']
            }
        )
        
        # 4. Save for retraining (only if SightEngine available)
        save_result = None
        if data_collector and se_result and se_result.get('available'):
            save_result = data_collector.save_file(
                file_path=filepath,
                label=se_result['verdict'],
                confidence=se_result['confidence'],
                source='sightengine'
            )
            if save_result and save_result.get('saved'):
                print(f"✓ File saved for retraining: {save_result['hash']} ({save_result['label']})")
        
        # Prepare response
        response_data = {
            'success': True,
            'cached': False,
            'content_type': 'image',
            'verdict': final_verdict,
            'confidence': final_confidence,
            'fake_probability': fake_prob,
            'real_probability': real_prob,
            'agreement_level': agreement,
            'detectors': {
                'sightengine': se_result if se_result else {'available': False},
                'mobilenet': {
                    'available': True,
                    'verdict': mn_result['verdict'],
                    'confidence': mn_result['confidence'],
                    'fake_probability': mn_result['fake_probability'],
                    'real_probability': mn_result['real_probability']
                }
            },
            'processing_time_seconds': round(time.time() - start_time, 2),
            'data_collection': save_result
        }
        
        # Save to database (only if SightEngine returned valid result)
        if db_connected and se_result and se_result.get('available'):
            try:
                DetectionResult.create(
                    file_hash=file_hash,
                    filename=file.filename,
                    content_type='image',
                    result_data=response_data
                )
                print(f"✓ Saved to database: {file_hash[:16]}...")
            except Exception as db_error:
                print(f"⚠ Database save failed: {db_error}")
        
        # Clean up
        os.remove(filepath)
        
        return jsonify(response_data)
        
    except Exception as e:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        print(f"Error in detect_dual: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/detect_video', methods=['POST'])
def detect_video():
    """
    Video detection endpoint with dual detectors
    
    Request: multipart/form-data with 'video'
    Response: JSON with aggregated results
    """
    if not mobilenet_detector:
        return jsonify({'success': False, 'error': 'Detector not ready'}), 503
    
    if 'video' not in request.files:
        return jsonify({'success': False, 'error': 'No video file provided'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_video(file.filename):
        return jsonify({
            'success': False,
            'error': f'Invalid format. Allowed: {", ".join(app.config["ALLOWED_VIDEO_EXTENSIONS"])}'
        }), 400
    
    filepath = None
    
    try:
        from services.video_processor import VideoProcessor
        from services.video_aggregator import VideoAggregator
        import time
        
        video_processor = VideoProcessor()
        video_aggregator = VideoAggregator()
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        file.save(filepath)
        
        # Calculate video hash for caching
        video_hash = None
        if db_connected:
            with open(filepath, 'rb') as f:
                video_hash = calculate_file_hash(f)
            
            # Check cache
            existing_result = DetectionResult.find_by_hash(video_hash)
            if existing_result:
                print(f"✓ Cache hit for video hash: {video_hash[:16]}...")
                os.remove(filepath)
                
                cached_response = {
                    'success': True,
                    'cached': True,
                    'content_type': 'video',
                    'verdict': existing_result.get('verdict'),
                    'confidence': existing_result.get('confidence'),
                    'fake_probability': existing_result.get('fake_probability'),
                    'real_probability': existing_result.get('real_probability'),
                    'video_info': existing_result.get('full_result', {}).get('video_info', {}),
                    'analysis': existing_result.get('full_result', {}).get('analysis', {}),
                    'agreement_level': existing_result.get('agreement_level'),
                    'confidence_timeline': existing_result.get('full_result', {}).get('confidence_timeline', []),
                    'suspicious_frames': existing_result.get('full_result', {}).get('suspicious_frames', []),
                    'model_breakdown': existing_result.get('full_result', {}).get('model_breakdown', []),
                    'processing_time_seconds': existing_result.get('full_result', {}).get('processing_time_seconds', 0),
                    'frames_analyzed': existing_result.get('full_result', {}).get('frames_analyzed', 0),
                    'timestamp': existing_result['timestamp'].isoformat()
                }
                
                return jsonify(cached_response)
        
        # Validate
        file_size = os.path.getsize(filepath)
        is_valid, error_msg = video_processor.validate_video(filepath, file_size)
        
        if not is_valid:
            os.remove(filepath)
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Get info
        video_info = video_processor.get_video_info(filepath)
        print(f"Processing video: {video_info}")
        
        # Extract frames
        start_time = time.time()
        frames = video_processor.extract_frames(filepath, frames_per_second=0.1)
        
        if not frames:
            os.remove(filepath)
            return jsonify({'success': False, 'error': 'Failed to extract frames'}), 500
        
        print(f"Extracted {len(frames)} frames")
        
        # Analyze each frame with dual detection
        frame_results = []
        
        for idx, frame in enumerate(frames):
            print(f"Analyzing frame {idx + 1}/{len(frames)}...")
            
            # Save frame temporarily
            frame_path = os.path.join(app.config['UPLOAD_FOLDER'], f"frame_{timestamp}_{idx}.jpg")
            frame.save(frame_path)
            
            # Run dual detection on frame
            se_result = None
            if sightengine_api:
                se_result = sightengine_api.detect_fake(frame_path)
            
            mn_result = mobilenet_detector.predict(frame_path)
            
            # Aggregate frame result (returns 5 values)
            frame_verdict, frame_conf, frame_agreement, frame_fake_prob, frame_real_prob = aggregate_dual_results(
                se_result if se_result else {'available': False},
                {
                    'available': True,
                    'verdict': mn_result['verdict'],
                    'confidence': mn_result['confidence'],
                    'fake_probability': mn_result['fake_probability'],
                    'real_probability': mn_result['real_probability']
                }
            )
            
            frame_results.append({
                'frame_index': idx,
                'detectors': {
                    'sightengine': se_result if se_result else {'available': False},
                    'mobilenet': {
                        'available': True,
                        'verdict': mn_result['verdict'],
                        'confidence': mn_result['confidence']
                    }
                },
                'final': {
                    'verdict': frame_verdict,
                    'confidence': frame_conf,
                    'agreement': frame_agreement
                }
            })
            
            # Clean up frame
            os.remove(frame_path)
        
        # Aggregate all frames
        print("Aggregating results...")
        aggregated = video_aggregator.aggregate_frame_results(frame_results)
        
        processing_time = time.time() - start_time
        
        # Try to save first frame for retraining (only if SightEngine available)
        first_frame_saved = None
        if data_collector and sightengine_api and aggregated['confidence'] > 85:
            # Check if SightEngine was actually used
            first_frame_se = frame_results[0].get('detectors', {}).get('sightengine', {})
            if first_frame_se.get('available'):
                first_frame_path = os.path.join(app.config['UPLOAD_FOLDER'], f"first_{timestamp}.jpg")
                frames[0].save(first_frame_path)
                
                first_frame_saved = data_collector.save_file(
                    file_path=first_frame_path,
                    label=aggregated['verdict'],
                    confidence=aggregated['confidence'],
                    source='sightengine'
                )
                
                os.remove(first_frame_path)
                
                if first_frame_saved and first_frame_saved.get('saved'):
                    print(f"✓ First frame saved for retraining: {first_frame_saved['hash']} ({first_frame_saved['label']})")
        
        # Clean up video
        os.remove(filepath)
        
        # Prepare response
        response_data = {
            'success': True,
            'cached': False,
            'content_type': 'video',
            'verdict': aggregated['verdict'],
            'confidence': aggregated['confidence'],
            'fake_probability': aggregated['fake_probability'],
            'real_probability': aggregated['real_probability'],
            'video_info': video_info,
            'analysis': aggregated['analysis'],
            'agreement_level': aggregated['agreement_level'],
            'confidence_timeline': aggregated['confidence_timeline'],
            'suspicious_frames': aggregated['suspicious_frames'],
            'model_breakdown': aggregated['model_breakdown'],
            'processing_time_seconds': round(processing_time, 2),
            'frames_analyzed': len(frames),
            'first_frame_saved': first_frame_saved
        }
        
        # Check if any frame used SightEngine
        used_sightengine = any(
            fr.get('detectors', {}).get('sightengine', {}).get('available', False)
            for fr in frame_results
        )
        
        # Save to database (only if SightEngine was used)
        if db_connected and video_hash and used_sightengine:
            try:
                DetectionResult.create(
                    file_hash=video_hash,
                    filename=file.filename,
                    content_type='video',
                    result_data=response_data
                )
                print(f"✓ Saved video to database: {video_hash[:16]}...")
            except Exception as db_error:
                print(f"⚠ Database save failed: {db_error}")
        
        return jsonify(response_data)
        
    except Exception as e:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """
    Get detection history
    
    Query params:
    - limit: Number of results (default 50, max 100)
    - content_type: Filter by 'image' or 'video'
    - verdict: Filter by 'FAKE', 'REAL', or 'UNCERTAIN'
    
    Response: JSON with list of past detections
    """
    if not db_connected:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        }), 503
    
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        content_type = request.args.get('content_type')
        verdict = request.args.get('verdict')
        
        history = DetectionResult.get_history(
            limit=limit,
            content_type=content_type,
            verdict=verdict
        )
        
        return jsonify({
            'success': True,
            'count': len(history),
            'results': history
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve history: {str(e)}'
        }), 500


@app.route('/api/search', methods=['POST'])
def search_detections():
    """
    Search detection results by filename
    
    Request: JSON with 'query' field
    Response: JSON with matching results
    """
    if not db_connected:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        }), 503
    
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Query text required'
            }), 400
        
        query_text = data['query']
        limit = min(int(data.get('limit', 20)), 50)
        
        results = DetectionResult.search(query_text, limit=limit)
        
        return jsonify({
            'success': True,
            'query': query_text,
            'count': len(results),
            'results': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}'
        }), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    Get overall detection statistics + data collection stats
    
    Response: JSON with stats summary
    """
    try:
        stats_data = {}
        
        # Detection statistics (if database available)
        if db_connected:
            stats_data['detections'] = DetectionResult.get_statistics()
        else:
            stats_data['detections'] = None
        
        # Data collection statistics
        if data_collector:
            stats_data['collection'] = data_collector.get_statistics()
        else:
            stats_data['collection'] = None
        
        # API usage
        if sightengine_api:
            stats_data['api_usage'] = sightengine_api.get_usage_info()
        else:
            stats_data['api_usage'] = None
        
        return jsonify({
            'success': True,
            'statistics': stats_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve statistics: {str(e)}'
        }), 500


@app.errorhandler(413)
def file_too_large(error):
    """Handle file too large"""
    return jsonify({
        'success': False,
        'error': f'File too large. Max: {app.config["MAX_CONTENT_LENGTH"] / (1024*1024)}MB'
    }), 413


if __name__ == '__main__':
    print("\n" + "="*50)
    print("  AI Deepfake Detection API")
    print("="*50)
    print(f"  MobileNetV4: {'Ready ✓' if mobilenet_detector else 'Not Ready ✗'}")
    print(f"  SightEngine: {'Ready ✓' if sightengine_api else 'Not Ready ✗'}")
    print(f"  Database: {'Connected ✓' if db_connected else 'Disconnected ✗'}")
    print(f"  URL: http://localhost:5000")
    print("="*50 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )