/**
 * Home Page Component
 * 
 * Main upload and detection page
 */

import React, { useState } from 'react';
import { Container, Row, Col, Button, Alert, Spinner } from 'react-bootstrap';
import UploadArea from '../components/UploadArea';
import ImagePreview from '../components/ImagePreview';
import VideoPreview from '../components/VideoPreview';
import Results from '../components/Results';
import VideoResults from '../components/VideoResults';
import { detectImage, detectVideo } from '../services/api';

const Home = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setImageUrl(URL.createObjectURL(file));
    setResult(null);
    setError(null);
  };

  const handleRemove = () => {
    if (imageUrl) {
      URL.revokeObjectURL(imageUrl);
    }
    setSelectedFile(null);
    setImageUrl(null);
    setResult(null);
    setError(null);
  };

  // Check if file is video
  const isVideo = selectedFile && selectedFile.type.startsWith('video/');

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let response;
      
      // Choose API based on file type
      if (isVideo) {
        response = await detectVideo(selectedFile);
      } else {
        response = await detectImage(selectedFile);
      }

      if (response.success) {
        setResult(response);
      } else {
        setError(response.error || 'Detection failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      <Row>
        <Col lg={6} className="mx-auto">
          {/* Upload Area */}
          {!selectedFile && (
            <UploadArea onFileSelect={handleFileSelect} />
          )}

          {/* Image/Video Preview */}
          {selectedFile && (
            <>
              {isVideo ? (
                <VideoPreview file={selectedFile} />
              ) : (
                <ImagePreview 
                  file={selectedFile}
                  imageUrl={imageUrl}
                  onRemove={handleRemove}
                />
              )}
            </>
          )}

          {/* Analyze Button */}
          {selectedFile && !result && (
            <div className="d-grid mt-4">
              <Button 
                variant="primary" 
                size="lg"
                onClick={handleAnalyze}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Spinner
                      as="span"
                      animation="border"
                      size="sm"
                      role="status"
                      aria-hidden="true"
                      className="me-2"
                    />
                    {isVideo ? 'Analyzing Video...' : 'Analyzing...'}
                  </>
                ) : (
                  `Analyze ${isVideo ? 'Video' : 'Image'}`
                )}
              </Button>
            </div>
          )}

          {/* Error Alert */}
          {error && (
            <Alert variant="danger" className="mt-4">
              <strong>Error:</strong> {error}
            </Alert>
          )}

          {/* Results */}
          {result && (
            <>
              {isVideo ? (
                <VideoResults result={result} />
              ) : (
                <Results result={result} />
              )}
              <div className="d-grid mt-3">
                <Button 
                  variant="outline-primary"
                  onClick={handleRemove}
                >
                  Analyze Another {isVideo ? 'Video' : 'Image'}
                </Button>
              </div>
            </>
          )}
        </Col>
      </Row>
    </Container>
  );
};

export default Home;
