"""
Extracts frames from video files for deepfake detection.
"""

import cv2
import os
from pathlib import Path
from PIL import Image
import tempfile


class VideoProcessor:
    """
    Handles video file processing and frame extraction.
    """
    
    def __init__(self):
        self.max_video_size = 50 * 1024 * 1024  # 50MB
        self.max_duration = 60  # 60 seconds
        self.supported_formats = ['.mp4', '.avi', '.mov']
    
    def validate_video(self, video_path, file_size):
        """
        Validate video file before processing.
        
        Args:
            video_path: Path to video file
            file_size: Size in bytes
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check file size
        if file_size > self.max_video_size:
            return False, f"Video too large. Max {self.max_video_size / (1024*1024)}MB"
        
        # Check format
        ext = Path(video_path).suffix.lower()
        if ext not in self.supported_formats:
            return False, f"Unsupported format. Allowed: {', '.join(self.supported_formats)}"
        
        # Check if file can be opened
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False, "Cannot open video file"
            
            # Check duration
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            if duration > self.max_duration:
                return False, f"Video too long. Max {self.max_duration} seconds"
            
            return True, None
            
        except Exception as e:
            return False, f"Error reading video: {str(e)}"
    
    def get_video_info(self, video_path):
        """
        Get video metadata.
        
        Returns:
            dict: Video information
        """
        cap = cv2.VideoCapture(video_path)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            'fps': round(fps, 2),
            'total_frames': frame_count,
            'duration_seconds': round(duration, 2),
            'resolution': f"{width}x{height}"
        }
    
    def extract_frames(self, video_path, frames_per_second=1.0):
        """
        Extract frames from video at specified rate.
        
        Args:
            video_path: Path to video file
            frames_per_second: How many frames to extract per second (default 1.0)
        
        Returns:
            list: List of PIL Images
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps / frames_per_second) if fps > 0 else 30
        
        frames = []
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Extract frame at interval
            if frame_idx % frame_interval == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image
                pil_image = Image.fromarray(frame_rgb)
                frames.append(pil_image)
            
            frame_idx += 1
        
        cap.release()
        
        return frames
    
    def extract_first_frame(self, video_path):
        """
        Extract only the first frame from video.
        
        Returns:
            PIL.Image or None
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return None
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        return Image.fromarray(frame_rgb)