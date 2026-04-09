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
        # Calculate file hash
        file_hash = calculate_file_hash(file)
        
        # Check cache (if database connected)
        if db_connected:
            existing_result = DetectionResult.find_by_hash(file_hash)
            if existing_result:
                print(f"✓ Cache hit for hash: {file_hash[:16]}...")
                return jsonify({
                    'success': True,
                    'cached': True,
                    'verdict': existing_result['verdict'],
                    'confidence': existing_result['confidence'],
                    'detectors': existing_result.get('detectors', {}),
                    'final': existing_result.get('final', {}),
                    'api_usage': existing_result.get('api_usage'),
                    'timestamp': existing_result['timestamp'].isoformat()
                })
        
        # Clean up old files
        cleanup_old_files()
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        file.save(filepath)
        
        # Run both detectors
        results = {}
        
        # 1. SightEngine API
        if sightengine_api:
            sightengine_result = sightengine_api.detect_fake(filepath)
            results['sightengine'] = sightengine_result
        else:
            results['sightengine'] = {
                'available': False,
                'reason': 'not_initialized'
            }
        
        # 2. MobileNetV4
        mobilenet_result = mobilenet_detector.predict(filepath)
        results['mobilenet'] = {
            'available': True,
            'verdict': mobilenet_result['verdict'],
            'confidence': mobilenet_result['confidence'],
            'fake_probability': mobilenet_result['fake_probability'],
            'real_probability': mobilenet_result['real_probability']
        }
        
        # 3. Aggregate results
        final_verdict, final_confidence, agreement = aggregate_dual_results(
            results['sightengine'],
            results['mobilenet']
        )

        save_result = None
        if data_collector and results['sightengine'].get('available'):
            se_result = results['sightengine']
            save_result = data_collector.save_file(
                file_path=filepath,
                label=se_result['verdict'],
                confidence=se_result['confidence'],
                source='sightengine'
            )
            if save_result['saved']:
                print(f"✓ File saved for retraining: {save_result['hash']} ({save_result['label']})") 
        
        
        # Prepare response
        response_data = {
            'success': True,
            'cached': False,
            'detectors': {
                'sightengine': results['sightengine'],
                'mobilenet': results['mobilenet']
            },
            'final': {
                'verdict': final_verdict,
                'confidence': final_confidence,
                'agreement': agreement
            },
            'api_usage': sightengine_api.get_usage_info() if sightengine_api else None,
            'data_collection': save_result
        }
        
        # Save to database (if connected)
        if db_connected:
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
        return jsonify({'success': False, 'error': str(e)}), 500


def aggregate_dual_results(sightengine_result, mobilenet_result):
    """
    Aggregate results from both detectors.
    SightEngine has priority when available.
    
    Returns:
        tuple: (verdict, confidence, agreement_level)
    """
    # If SightEngine unavailable, use MobileNet only
    if not sightengine_result.get('available'):
        return (
            mobilenet_result['verdict'],
            mobilenet_result['confidence'],
            'single_detector'
        )
    
    # SightEngine available - it has priority
    se_verdict = sightengine_result['verdict']
    mn_verdict = mobilenet_result['verdict']
    se_conf = sightengine_result['confidence']
    mn_conf = mobilenet_result['confidence']
    
    # Check agreement
    if se_verdict == mn_verdict:
        # Both agree - use SightEngine verdict with averaged confidence
        avg_conf = (se_conf + mn_conf) / 2
        conf_diff = abs(se_conf - mn_conf)
        
        if conf_diff < 10:
            agreement = 'strong_agreement'
        else:
            agreement = 'agreement'
        
        return (se_verdict, round(avg_conf, 2), agreement)
    else:
        # Disagree - SightEngine takes priority
        return (se_verdict, se_conf, 'disagreement')


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
    Get overall detection statistics
    
    Response: JSON with stats summary
    """
    if not db_connected:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        }), 503
    
    try:
        stats = DetectionResult.get_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
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