/**
 * VideoPreview Component
 * Displays video with player controls
 */

import React from 'react';
import { Card } from 'react-bootstrap';

const VideoPreview = ({ file }) => {
  // Create object URL for video preview
  const videoUrl = URL.createObjectURL(file);

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <Card>
      <Card.Body>
        <h5 className="mb-3">Video Preview</h5>
        
        {/* Video Player */}
        <div className="mb-3" style={{ maxWidth: '100%' }}>
          <video
            controls
            style={{
              width: '100%',
              maxHeight: '400px',
              borderRadius: '8px',
              backgroundColor: '#000'
            }}
          >
            <source src={videoUrl} type={file.type} />
            Your browser does not support the video tag.
          </video>
        </div>

        {/* Video Info */}
        <div className="text-muted small">
          <div className="d-flex justify-content-between mb-1">
            <span>Filename:</span>
            <span>{file.name}</span>
          </div>
          <div className="d-flex justify-content-between mb-1">
            <span>Format:</span>
            <span>{file.type || 'Unknown'}</span>
          </div>
          <div className="d-flex justify-content-between">
            <span>Size:</span>
            <span>{formatFileSize(file.size)}</span>
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};

export default VideoPreview;
