/**
 * UploadArea Component
 * Handles image upload with drag & drop support
 */

import React, { useState } from 'react';
import { Card } from 'react-bootstrap';

const UploadArea = ({ onFileSelect }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    // Check if file is image or video
    const isImage = file.type.startsWith('image/');
    const isVideo = file.type.startsWith('video/');

    // Validate file type
    if (!isImage && !isVideo) {
      alert('Please select an image or video file');
      return;
    }
    
    // Validate file size
    const maxSize = isVideo ? 50 * 1024 * 1024 : 16 * 1024 * 1024; // 50MB for video, 16MB for image
    const maxSizeText = isVideo ? '50MB' : '16MB';

    if (file.size > maxSize) {
      alert(`File too large. Maximum size is ${maxSizeText}`);
      return;
    }

    onFileSelect(file);
  };

  return (
    <Card 
      className={`upload-area ${isDragging ? 'dragging' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => document.getElementById('fileInput').click()}
      style={{ cursor: 'pointer' }}
    >
      <Card.Body className="text-center p-5">
        <div className="upload-icon mb-3">
          <i className="bi bi-cloud-upload" style={{ fontSize: '3rem' }}></i>
        </div>
        <h5>Upload Image or Video</h5>
        <p className="text-muted">
          Click to browse or drag and drop
        </p>
        <small className="text-muted">
          PNG, JPG, JPEG, WEBP (max 16MB)<br/>
          Videos: MP4, AVI, MOV (max 50MB)
        </small>
        <input
          id="fileInput"
          type="file"
          accept="image/*,video/*"
          onChange={handleFileInput}
          style={{ display: 'none' }}
        />
      </Card.Body>
    </Card>
  );
};

export default UploadArea;
