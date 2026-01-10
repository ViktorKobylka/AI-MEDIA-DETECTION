import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Button, Alert, Spinner } from 'react-bootstrap';
import UploadArea from './components/UploadArea';
import ImagePreview from './components/ImagePreview';
import Results from './components/Results';
import { checkHealth, detectImage } from './services/api';
import './App.css';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState('checking');

  // Check API health on mount
  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      const health = await checkHealth();
      if (health.status === 'ok' && health.detector_ready) {
        setApiStatus('ready');
      } else {
        setApiStatus('not-ready');
      }
    } catch (err) {
      setApiStatus('offline');
    }
  };

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

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const detectionResult = await detectImage(selectedFile);
      
      if (detectionResult.success) {
        setResult(detectionResult);
      } else {
        setError(detectionResult.error || 'Detection failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      {/* Header */}
      <div className="header bg-primary text-white py-4 mb-4">
        <Container>
          <h1 className="text-center mb-2">
            AI Media Detector
          </h1>
          <p className="text-center mb-0">
            Upload an image to detect if it's AI-generated 
          </p>
        </Container>
      </div>

      <Container>
        <Row>
          <Col lg={6} className="mx-auto">
            {/* Upload Area */}
            {!selectedFile && (
              <UploadArea onFileSelect={handleFileSelect} />
            )}

            {/* Image Preview */}
            {selectedFile && (
              <ImagePreview 
                file={selectedFile}
                imageUrl={imageUrl}
                onRemove={handleRemove}
              />
            )}

            {/* Analyze Button */}
            {selectedFile && !result && (
              <div className="d-grid mt-4">
                <Button 
                  variant="primary" 
                  size="lg"
                  onClick={handleAnalyze}
                  disabled={loading || apiStatus !== 'ready'}
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
                      Analyzing...
                    </>
                  ) : (
                    'Analyze Image'
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
                <Results result={result} />
                <div className="d-grid mt-3">
                  <Button 
                    variant="outline-primary"
                    onClick={handleRemove}
                  >
                    Analyze Another Image
                  </Button>
                </div>
              </>
            )}
          </Col>
        </Row>

        {/* Footer */}
        <div className="text-center mt-5 mb-4">
          <div className="mb-3">
            <h6 className="text-muted mb-2">About This Application</h6>
            <p className="text-muted mb-1" style={{ fontSize: '0.9rem' }}>
              This system detects AI-generated images and deepfakes using advanced ensemble learning.
            </p>
            <p className="text-muted mb-1" style={{ fontSize: '0.9rem' }}>
              <strong>Detects:</strong> StyleGAN faces, face swaps, GAN-generated images, and photorealistic deepfakes
            </p>
          </div>
        </div>
      </Container>
    </div>
  );
}

export default App;