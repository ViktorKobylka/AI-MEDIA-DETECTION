/**
 * VideoResults Component
 * Displays for both fresh video detections and cached results
 */


import React from 'react';
import { Card, Badge, ProgressBar, Row, Col, Alert } from 'react-bootstrap';
import './Results.css';

// Detector Card Component 
const DetectorCard = ({ name, icon, data, bgClass }) => {
  const isAvailable = data && data.model;
  
  const getVerdictVariant = (fakePercent) => {
    if (fakePercent >= 50) return 'danger';
    return 'success';
  };
  
  const getVerdict = (fakePercent) => {
    if (fakePercent >= 50) return 'FAKE';
    return 'REAL';
  };
  
  return (
    <Card className={`h-100 border ${bgClass}`}>
      <Card.Body>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h6 className="mb-0">
            <i className={`${icon} me-2`}></i>
            {name}
          </h6>
          <Badge bg={isAvailable ? 'success' : 'secondary'} pill>
            {isAvailable ? 'Active' : 'Unavailable'}
          </Badge>
        </div>

        {isAvailable ? (
          <>
            <div className="text-center mb-3">
              <Badge 
                bg={getVerdictVariant(data.fake_percentage)}
                className="px-3 py-2"
                style={{ fontSize: '1rem' }}
              >
                {getVerdict(data.fake_percentage)}
              </Badge>
            </div>

            <div className="mb-2">
              <small className="text-muted d-block">Fake Frames</small>
              <h5 className="mb-1">{data.fake_frames}/{data.total_frames}</h5>
            </div>

            <div className="d-flex justify-content-between small text-muted mb-2">
              <span>Fake: {data.fake_percentage?.toFixed(1)}%</span>
              <span>Real: {(100 - data.fake_percentage)?.toFixed(1)}%</span>
            </div>

            <ProgressBar style={{ height: '8px' }}>
              <ProgressBar 
                variant="danger" 
                now={data.fake_percentage || 0} 
                key={1}
              />
              <ProgressBar 
                variant="success" 
                now={100 - (data.fake_percentage || 0)} 
                key={2}
              />
            </ProgressBar>
          </>
        ) : (
          <div className="text-center text-muted py-3">
            <i className="bi bi-x-circle" style={{ fontSize: '2rem' }}></i>
            <p className="mb-0 mt-2 small">Not available</p>
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

const VideoResults = ({ result }) => {
  console.log('=== VideoResults Component Debug ===');
  console.log('Full result:', result);
  console.log('====================================');

  // Safety check
  if (!result) {
    return (
      <Alert variant="warning">
        No video results to display
      </Alert>
    );
  }

  const isCached = result.cached || false;
  
  // Extract main verdict data
  const verdict = result.verdict || 'UNKNOWN';
  const confidence = result.confidence || 0;
  const fakeProb = result.fake_probability || 0;
  const realProb = result.real_probability || 0;
  const agreement = result.agreement_level || 'unknown';
  
  // Video info
  const videoInfo = result.video_info || {};
  const analysis = result.analysis || {};
  const modelBreakdown = result.model_breakdown || [];
  const suspiciousFrames = result.suspicious_frames || [];
  const confidenceTimeline = result.confidence_timeline || [];
  
  // Frame analysis
  const totalFrames = analysis.total_frames_analyzed || 0;
  const fakeFrames = analysis.fake_frames || 0;
  const realFrames = analysis.real_frames || 0;
  const fakePercent = analysis.fake_percentage || 0;
  const realPercent = analysis.real_percentage || 0;

  // Helper functions
  const getVerdictVariant = (v) => {
    if (!v) return 'secondary';
    const upper = v.toString().toUpperCase();
    if (upper === 'FAKE') return 'danger';
    if (upper === 'REAL') return 'success';
    return 'secondary';
  };
  
  const getAgreementBadge = (agree) => {
    if (!agree) return { variant: 'secondary', text: 'Unknown' };
    const badges = {
      'strong_agreement': { variant: 'success', text: 'Strong Agreement' },
      'agreement': { variant: 'info', text: 'Agreement' },
      'disagreement': { variant: 'warning', text: 'Disagreement' },
      'single_detector': { variant: 'secondary', text: 'Single Detector' }
    };
    return badges[agree] || { variant: 'secondary', text: 'Unknown' };
  };
  
  const agreementBadge = getAgreementBadge(agreement);

  return (
    <div className="results-container mt-4">
      {/* Cached Badge */}
      {isCached && (
        <Alert variant="info" className="mb-3">
          <i className="bi bi-database-check me-2"></i>
          <strong>Cached Result</strong> - Previously analyzed
        </Alert>
      )}

      {/* Main Verdict Card */}
      <Card className="mb-3 shadow-sm main-verdict-card">
        <Card.Body className="text-center py-4">
          <h3 className="mb-3">
            <i className="bi bi-film me-2"></i>
            Video Detection Result
          </h3>
          
          <div className="mb-4">
            <Badge 
              bg={getVerdictVariant(verdict)} 
              className="verdict-badge px-4 py-3"
              style={{ fontSize: '1.8rem' }}
            >
              {verdict}
            </Badge>
          </div>

          <div className="confidence-display mb-3">
            <small className="text-muted d-block mb-1">Overall Confidence</small>
            <h1 className="mb-0 fw-bold" style={{ fontSize: '3rem' }}>
              {confidence.toFixed(1)}%
            </h1>
          </div>

          {/* Probability Bar */}
          <div className="mb-3">
            <div className="d-flex justify-content-between mb-2">
              <span className="text-danger fw-bold">
                <i className="bi bi-x-circle me-1"></i>
                Fake: {fakeProb.toFixed(1)}%
              </span>
              <span className="text-success fw-bold">
                <i className="bi bi-check-circle me-1"></i>
                Real: {realProb.toFixed(1)}%
              </span>
            </div>
            
            <ProgressBar style={{ height: '30px' }}>
              <ProgressBar 
                variant="danger" 
                now={fakeProb} 
                label={fakeProb > 10 ? `${fakeProb.toFixed(1)}%` : ''}
                key={1}
                className="fw-bold"
              />
              <ProgressBar 
                variant="success" 
                now={realProb} 
                label={realProb > 10 ? `${realProb.toFixed(1)}%` : ''}
                key={2}
                className="fw-bold"
              />
            </ProgressBar>
          </div>

          {/* Agreement & Frames Badge */}
          <div className="mt-3">
            <Badge bg={agreementBadge.variant} className="px-3 py-2 me-2">
              <i className="bi bi-diagram-3 me-2"></i>
              {agreementBadge.text}
            </Badge>
            <Badge bg="info" className="px-3 py-2">
              <i className="bi bi-collection me-2"></i>
              {totalFrames} Frames
            </Badge>
          </div>
        </Card.Body>
      </Card>

      {/* Video Analysis Card */}
      <Card className="mb-3 shadow-sm">
        <Card.Header className="bg-light">
          <h5 className="mb-0">
            <i className="bi bi-graph-up me-2"></i>
            Video Analysis
          </h5>
        </Card.Header>
        <Card.Body>
          <Row>
            {/* Video Info */}
            <Col md={6} className="mb-3 mb-md-0">
              <h6 className="text-muted mb-3">Video Information</h6>
              
              <div className="d-flex justify-content-between mb-2">
                <span><i className="bi bi-clock me-2"></i>Duration:</span>
                <strong>{videoInfo.duration_seconds?.toFixed(1) || 'N/A'}s</strong>
              </div>
              
              <div className="d-flex justify-content-between mb-2">
                <span><i className="bi bi-speedometer2 me-2"></i>FPS:</span>
                <strong>{videoInfo.fps || 'N/A'}</strong>
              </div>
              
              <div className="d-flex justify-content-between mb-2">
                <span><i className="bi bi-aspect-ratio me-2"></i>Resolution:</span>
                <strong>{videoInfo.resolution || 'N/A'}</strong>
              </div>
              
              <div className="d-flex justify-content-between mb-2">
                <span><i className="bi bi-cpu me-2"></i>Processing:</span>
                <strong>{result.processing_time_seconds?.toFixed(2) || 'N/A'}s</strong>
              </div>
            </Col>
            
            {/* Frame Breakdown */}
            <Col md={6}>
              <h6 className="text-muted mb-3">Frame Breakdown</h6>
              
              <div className="mb-3">
                <div className="d-flex justify-content-between mb-2">
                  <span className="text-danger fw-bold">
                    <i className="bi bi-x-circle me-1"></i>
                    FAKE Frames
                  </span>
                  <strong>{fakeFrames} ({fakePercent.toFixed(1)}%)</strong>
                </div>
                <ProgressBar 
                  variant="danger" 
                  now={fakePercent} 
                  style={{ height: '12px' }}
                  label={fakePercent > 15 ? `${fakePercent.toFixed(0)}%` : ''}
                />
              </div>
              
              <div className="mb-3">
                <div className="d-flex justify-content-between mb-2">
                  <span className="text-success fw-bold">
                    <i className="bi bi-check-circle me-1"></i>
                    REAL Frames
                  </span>
                  <strong>{realFrames} ({realPercent.toFixed(1)}%)</strong>
                </div>
                <ProgressBar 
                  variant="success" 
                  now={realPercent} 
                  style={{ height: '12px' }}
                  label={realPercent > 15 ? `${realPercent.toFixed(0)}%` : ''}
                />
              </div>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Detector Breakdown */}
      <Card className="mb-3 shadow-sm">
        <Card.Header className="bg-light">
          <h5 className="mb-0">
            <i className="bi bi-cpu me-2"></i>
            Detector Breakdown
          </h5>
        </Card.Header>
        <Card.Body>
          <Row>
            {/* SightEngine */}
            <Col md={6} className="mb-3 mb-md-0">
              <DetectorCard
                name="SightEngine API"
                icon="bi bi-cloud-check"
                data={modelBreakdown.find(m => m.model === 'SightEngine')}
                bgClass="sightengine-card"
              />
            </Col>

            {/* MobileNetV4 */}
            <Col md={6}>
              <DetectorCard
                name="MobileNetV4"
                icon="bi bi-cpu"
                data={modelBreakdown.find(m => m.model === 'MobileNetV4')}
                bgClass="mobilenet-card"
              />
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Suspicious Frames */}
      {suspiciousFrames && suspiciousFrames.length > 0 && (
        <Card className="mb-3 shadow-sm border-danger">
          <Card.Header className="bg-danger text-white">
            <h5 className="mb-0">
              <i className="bi bi-exclamation-triangle me-2"></i>
              Suspicious Frames Detected
            </h5>
          </Card.Header>
          <Card.Body>
            <p className="mb-3">
              <strong>{suspiciousFrames.length}</strong> frames show high probability of manipulation (>70% fake confidence):
            </p>
            
            <div className="mb-3">
              {suspiciousFrames.slice(0, 10).map((frame, idx) => (
                <Badge 
                  key={idx} 
                  bg="danger" 
                  className="me-2 mb-2 px-3 py-2"
                >
                  Frame {frame.frame} @ {frame.timestamp}s ({frame.confidence?.toFixed(1)}%)
                </Badge>
              ))}
              {suspiciousFrames.length > 10 && (
                <Badge bg="secondary" className="px-3 py-2">
                  +{suspiciousFrames.length - 10} more
                </Badge>
              )}
            </div>
          </Card.Body>
        </Card>
      )}

      {/* Confidence Timeline */}
      {confidenceTimeline && confidenceTimeline.length > 0 && (
        <Card className="shadow-sm">
          <Card.Header className="bg-light">
            <h5 className="mb-0">
              <i className="bi bi-graph-up-arrow me-2"></i>
              Confidence Timeline
            </h5>
          </Card.Header>
          <Card.Body>
            <div 
              className="confidence-timeline mb-3" 
              style={{ 
                display: 'flex', 
                gap: '2px', 
                height: '100px', 
                alignItems: 'flex-end',
                backgroundColor: '#f8f9fa',
                padding: '10px',
                borderRadius: '8px'
              }}
            >
              {confidenceTimeline.map((item, idx) => {
                const conf = item.confidence || 0;
                const color = item.verdict === 'FAKE' ? '#dc3545' : '#198754';
                
                return (
                  <div
                    key={idx}
                    style={{
                      flex: 1,
                      height: `${conf}%`,
                      backgroundColor: color,
                      opacity: 0.8,
                      transition: 'opacity 0.2s, transform 0.2s',
                      cursor: 'pointer',
                      borderRadius: '2px'
                    }}
                    title={`Frame ${item.frame}: ${item.verdict} (${conf.toFixed(1)}%)`}
                    onMouseEnter={(e) => {
                      e.target.style.opacity = 1;
                      e.target.style.transform = 'scaleY(1.1)';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.opacity = 0.8;
                      e.target.style.transform = 'scaleY(1)';
                    }}
                  />
                );
              })}
            </div>
            
            <div className="d-flex justify-content-between text-muted small mb-2">
              <span>Frame 0</span>
              <span>Frame {confidenceTimeline.length - 1}</span>
            </div>
            
            <div className="text-center">
              <small className="text-muted">
                <i className="bi bi-info-circle me-1"></i>
                🔴 Red = FAKE | 🟢 Green = REAL | Hover for details
              </small>
            </div>
          </Card.Body>
        </Card>
      )}

      {/* Processing Info */}
      <div className="text-center mt-3">
        <small className="text-muted">
          <i className="bi bi-clock me-1"></i>
          Processed in {result.processing_time_seconds?.toFixed(2) || '0'}s
          {isCached && ' (from cache)'}
        </small>
      </div>
    </div>
  );
};

export default VideoResults;