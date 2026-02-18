"""
Flask API for AI-Generated Image Detection

REST API for deepfake detection using ensemble model.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from pathlib import Path
from datetime import datetime

from models.ensemble import EnsembleDetector
from video_processor import VideoProcessor
from video_aggregator import VideoAggregator
import time

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

# Initialize detector once on startup
print("Initializing detector...")
try:
    detector = EnsembleDetector()
    video_processor = VideoProcessor()
    video_aggregator = VideoAggregator()
    print("✓ Detector ready!")
except Exception as e:
    print(f"✗ Error: {e}")
    detector = None
    video_processor = None
    video_aggregator = None


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
        'status': 'ok' if detector else 'error',
        'detector_ready': detector is not None
    })


@app.route('/api/detect', methods=['POST'])
def detect():
    """
    Image detection endpoint
    
    Request: multipart/form-data with 'file'
    Response: JSON with detection results
    """
    # Check detector
    if not detector:
        return jsonify({'success': False, 'error': 'Detector not ready'}), 503
    
    # Check file
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
    
    try:
        # Clean up old files
        cleanup_old_files()
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        
        file.save(filepath)
        
        # Run detection
        result = detector.predict(filepath)
        
        # Clean up
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify({
            'success': True,
            'verdict': result['verdict'],
            'confidence': result['confidence'],
            'fake_probability': result['fake_probability'],
            'real_probability': result['real_probability'],
            'agreement_level': result['agreement_level'],
            'individual_results': result['individual_results'],
            'recommendation': result['recommendation']
        })
    
    except Exception as e:
        # Clean up on error
        try:
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': f'Processing failed: {str(e)}'
        }), 500


@app.route('/api/detect_video', methods=['POST'])
def detect_video():
    """
    Video detection endpoint
    
    Request: multipart/form-data with 'video'
    Response: JSON with detection results
    """
    # Check if components are ready
    if not detector or not video_processor or not video_aggregator:
        return jsonify({'success': False, 'error': 'System not ready'}), 503
    
    # Check file
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
        # Clean up old files
        cleanup_old_files()
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        
        file.save(filepath)
        
        # Get file size
        file_size = os.path.getsize(filepath)
        
        # Validate video
        is_valid, error_msg = video_processor.validate_video(filepath, file_size)
        
        if not is_valid:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Get video info
        video_info = video_processor.get_video_info(filepath)
        print(f"\nProcessing video: {video_info}")
        
        # Extract frames
        start_time = time.time()
        frames = video_processor.extract_frames(filepath, frames_per_second=1.0)
        
        if not frames:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({
                'success': False,
                'error': 'Failed to extract frames from video'
            }), 500
        
        print(f"Extracted {len(frames)} frames")
        
        # Analyze each frame
        frame_results = []
        
        for idx, frame in enumerate(frames):
            print(f"Analyzing frame {idx + 1}/{len(frames)}...")
            
            # Save frame temporarily
            frame_path = os.path.join(app.config['UPLOAD_FOLDER'], f"frame_{timestamp}_{idx}.jpg")
            frame.save(frame_path)
            
            # Run detection
            result = detector.predict(frame_path)
            
            # Add frame index
            result['frame_index'] = idx
            frame_results.append(result)
            
            # Clean up frame
            try:
                os.remove(frame_path)
            except:
                pass
        
        # Aggregate results
        print("Aggregating results...")
        aggregated = video_aggregator.aggregate_frame_results(frame_results)
        
        processing_time = time.time() - start_time
        
        # Clean up video file
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass
        
        # Return results
        return jsonify({
            'success': True,
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
            'frames_analyzed': len(frames)
        })
    
    except Exception as e:
        # Clean up on error
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
            # Clean up any frame files
            folder = Path(app.config['UPLOAD_FOLDER'])
            for file in folder.glob(f"frame_{timestamp}_*.jpg"):
                file.unlink()
        except:
            pass
        
        print(f"Error processing video: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'Video processing failed: {str(e)}'
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
    print("  AI Detection API")
    print("="*50)
    print(f"  Status: {'Ready' if detector else 'Not Ready'}")
    print(f"  URL: http://localhost:5000")
    print("="*50 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
