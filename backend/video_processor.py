"""
Video Processor Module
Handles video file validation, frame extraction, and metadata retrieval
"""

import cv2
import numpy as np
from PIL import Image
import os
from typing import List, Tuple, Dict, Optional


class VideoProcessor:
    """Processes video files for deepfake detection"""
    
    # Configuration
    MAX_VIDEO_DURATION = 30  # seconds
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov']
    TARGET_FRAME_SIZE = (224, 224)  # ViT input size
    
    def __init__(self):
        """Initialize video processor"""
        pass
    
    def validate_video(self, file_path: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validate video file
        
        Args:
            file_path: Path to video file
            file_size: Size of file in bytes
            
        Returns:
            (is_valid, error_message)
        """
        # Check file size
        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File size exceeds maximum of {max_mb}MB"
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported format. Please use: {', '.join(self.SUPPORTED_FORMATS)}"
        
        # Try to open video
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return False, "Unable to open video file. File may be corrupted."
            
            # Check duration
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if fps == 0:
                cap.release()
                return False, "Invalid video: FPS is 0"
            
            duration = frame_count / fps
            
            if duration > self.MAX_VIDEO_DURATION:
                cap.release()
                return False, f"Video exceeds maximum duration of {self.MAX_VIDEO_DURATION} seconds"
            
            cap.release()
            return True, None
            
        except Exception as e:
            return False, f"Error validating video: {str(e)}"
    
    def get_video_info(self, file_path: str) -> Dict:
        """
        Get video metadata
        
        Args:
            file_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        try:
            cap = cv2.VideoCapture(file_path)
            
            if not cap.isOpened():
                return {}
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            return {
                'duration': round(duration, 2),
                'fps': round(fps, 2),
                'frame_count': frame_count,
                'resolution': f"{width}x{height}",
                'width': width,
                'height': height
            }
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return {}
    
    def extract_frames(self, file_path: str, frames_per_second: float = 1.0) -> List[Image.Image]:
        """
        Extract frames from video
        
        Args:
            file_path: Path to video file
            frames_per_second: How many frames to extract per second (default: 1)
            
        Returns:
            List of PIL Images (RGB, 224x224)
        """
        frames = []
        
        try:
            cap = cv2.VideoCapture(file_path)
            
            if not cap.isOpened():
                raise ValueError("Unable to open video file")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if fps == 0:
                cap.release()
                raise ValueError("Invalid video FPS")
            
            # Calculate frame interval
            frame_interval = int(fps / frames_per_second)
            
            if frame_interval < 1:
                frame_interval = 1
            
            print(f"Extracting frames: FPS={fps}, Interval={frame_interval}, Total={total_frames}")
            
            frame_idx = 0
            extracted_count = 0
            
            while True:
                # Set frame position
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                
                # Read frame
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Convert BGR to RGB (OpenCV uses BGR)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize to target size
                frame_resized = cv2.resize(frame_rgb, self.TARGET_FRAME_SIZE)
                
                # Convert to PIL Image
                pil_image = Image.fromarray(frame_resized)
                
                frames.append(pil_image)
                extracted_count += 1
                
                # Move to next frame
                frame_idx += frame_interval
                
                # Stop if we've reached the end
                if frame_idx >= total_frames:
                    break
            
            cap.release()
            
            print(f"Extracted {extracted_count} frames from video")
            
            return frames
            
        except Exception as e:
            print(f"Error extracting frames: {e}")
            return []
    
    def extract_keyframes(self, file_path: str, max_frames: int = 30) -> List[Image.Image]:
        """
        Extract key frames from video (smart sampling)
        
        Args:
            file_path: Path to video file
            max_frames: Maximum number of frames to extract
            
        Returns:
            List of PIL Images
        """
        try:
            cap = cv2.VideoCapture(file_path)
            
            if not cap.isOpened():
                raise ValueError("Unable to open video file")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames == 0:
                cap.release()
                return []
            
            # Calculate frame indices to extract
            if total_frames <= max_frames:
                # Extract all frames
                frame_indices = list(range(0, total_frames, max(1, total_frames // max_frames)))
            else:
                # Extract evenly spaced frames
                step = total_frames / max_frames
                frame_indices = [int(i * step) for i in range(max_frames)]
            
            frames = []
            
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize
                frame_resized = cv2.resize(frame_rgb, self.TARGET_FRAME_SIZE)
                
                # Convert to PIL
                pil_image = Image.fromarray(frame_resized)
                frames.append(pil_image)
            
            cap.release()
            
            print(f"Extracted {len(frames)} keyframes from {total_frames} total frames")
            
            return frames
            
        except Exception as e:
            print(f"Error extracting keyframes: {e}")
            return []


# Helper function for easy use
def process_video(file_path: str, frames_per_second: float = 1.0) -> Tuple[List[Image.Image], Dict]:
    """
    Process video file and extract frames with metadata
    
    Args:
        file_path: Path to video file
        frames_per_second: Frames to extract per second
        
    Returns:
        (frames, video_info)
    """
    processor = VideoProcessor()
    
    # Get video info
    video_info = processor.get_video_info(file_path)
    
    # Extract frames
    frames = processor.extract_frames(file_path, frames_per_second)
    
    return frames, video_info
