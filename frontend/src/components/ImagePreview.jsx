/**
 * ImagePreview Component
 * Displays uploaded image preview
 */

import React from 'react';
import { Card, Button } from 'react-bootstrap';

const ImagePreview = ({ file, imageUrl, onRemove }) => {
  return (
    <Card className="mt-4">
      <Card.Body>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h6 className="mb-0">Preview</h6>
          <Button 
            variant="outline-danger" 
            size="sm"
            onClick={onRemove}
          >
            Remove
          </Button>
        </div>
        <div className="text-center">
          <img 
            src={imageUrl} 
            alt="Preview" 
            className="img-fluid rounded"
            style={{ maxHeight: '400px' }}
          />
        </div>
        <div className="mt-3 text-muted small">
          <div><strong>File:</strong> {file.name}</div>
          <div><strong>Size:</strong> {(file.size / 1024).toFixed(2)} KB</div>
          <div><strong>Type:</strong> {file.type}</div>
        </div>
      </Card.Body>
    </Card>
  );
};

export default ImagePreview;
