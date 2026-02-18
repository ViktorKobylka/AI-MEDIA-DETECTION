/**
 * VideoResults Component
 * Displays video deepfake detection results with frame analysis
 */

import React from 'react';
import { Card, ProgressBar, Badge, Row, Col, Table } from 'react-bootstrap';

const VideoResults = ({ result }) => {
  // Get verdict color
  const getVerdictColor = (verdict) => {
    switch (verdict) {
      case 'FAKE': return 'danger';
      case 'REAL': return 'success';
      case 'UNCERTAIN': return 'warning';
      default: return 'secondary';
    }
  };

  // Get verdict icon
  const getVerdictIcon = (verdict) => {
    switch (verdict) {
      case 'FAKE': return '⚠️';
      case 'REAL': return '✓';
      case 'UNCERTAIN': return '?';
      default: return '';
    }
  };

  // Get agreement badge color
  const getAgreementColor = (level) => {
    switch (level) {
      case 'HIGH': return 'success';
      case 'MEDIUM': return 'warning';
      case 'LOW': return 'danger';
      default: return 'secondary';
    }
  };

  // Calculate frame percentages
  const totalFrames = result.analysis?.total_frames_analyzed || 0;
  const fakeFrames = result.analysis?.fake_frames || 0;
  const realFrames = result.analysis?.real_frames || 0;
  const uncertainFrames = result.analysis?.uncertain_frames || 0;

  const fakePercent = totalFrames > 0 ? (fakeFrames / totalFrames * 100).toFixed(1) : 0;
  const realPercent = totalFrames > 0 ? (realFrames / totalFrames * 100).toFixed(1) : 0;

  return (
    <div className="video-results">
      {/* Main Verdict Card */}
      <Card className="mb-3">
        <Card.Body>
          <div className="text-center">
            <div style={{ fontSize: '3rem' }} className="mb-2">
              {getVerdictIcon(result.verdict)}
            </div>
            <h2 className={`text-${getVerdictColor(result.verdict)}`}>
              {result.verdict} VIDEO
            </h2>
            <h4 className="mb-3">{result.confidence}% Confidence</h4>
            
            {/* Confidence Bar */}
            <ProgressBar 
              now={result.confidence} 
              variant={getVerdictColor(result.verdict)}
              className="mb-3"
              style={{ height: '25px' }}
              label={`${result.confidence}%`}
            />

            {/* Agreement Badge */}
            <div>
              <Badge bg={getAgreementColor(result.agreement_level)} className="me-2">
                {result.agreement_level} Frame Agreement
              </Badge>
              <Badge bg="info">
                {totalFrames} Frames Analyzed
              </Badge>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Video Analysis Card */}
      <Card className="mb-3">
        <Card.Header>
          <h5 className="mb-0">Video Analysis</h5>
        </Card.Header>
        <Card.Body>
          <Row>
            <Col md={6}>
              <h6>Video Information</h6>
              <div className="mb-3">
                <div className="d-flex justify-content-between mb-2">
                  <span>Duration:</span>
                  <strong>{result.video_info?.duration || 'N/A'}s</strong>
                </div>
                <div className="d-flex justify-content-between mb-2">
                  <span>FPS:</span>
                  <strong>{result.video_info?.fps || 'N/A'}</strong>
                </div>
                <div className="d-flex justify-content-between mb-2">
                  <span>Resolution:</span>
                  <strong>{result.video_info?.resolution || 'N/A'}</strong>
                </div>
                <div className="d-flex justify-content-between">
                  <span>Processing Time:</span>
                  <strong>{result.processing_time_seconds || 'N/A'}s</strong>
                </div>
              </div>
            </Col>
            
            <Col md={6}>
              <h6>Frame Breakdown</h6>
              <div className="mb-2">
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="text-danger"> FAKE Frames:</span>
                  <strong>{fakeFrames} ({fakePercent}%)</strong>
                </div>
                <ProgressBar 
                  variant="danger" 
                  now={fakePercent} 
                  className="mb-3" 
                  style={{ height: '10px' }}
                />
              </div>
              
              <div>
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="text-success"> REAL Frames:</span>
                  <strong>{realFrames} ({realPercent}%)</strong>
                </div>
                <ProgressBar 
                  variant="success" 
                  now={realPercent} 
                  className="mb-3" 
                  style={{ height: '10px' }}
                />
              </div>

              {uncertainFrames > 0 && (
                <div>
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <span className="text-warning"> UNCERTAIN Frames:</span>
                    <strong>{uncertainFrames}</strong>
                  </div>
                </div>
              )}
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Model Breakdown Card */}
      {result.model_breakdown && result.model_breakdown.length > 0 && (
        <Card className="mb-3">
          <Card.Header>
            <h5 className="mb-0">Model Breakdown</h5>
          </Card.Header>
          <Card.Body>
            <Table responsive className="mb-0">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Prediction</th>
                  <th>Avg Confidence</th>
                  <th>Fake Frames</th>
                  <th>Real Frames</th>
                </tr>
              </thead>
              <tbody>
                {result.model_breakdown.map((model, idx) => (
                  <tr key={idx}>
                    <td><strong>{model.model}</strong></td>
                    <td>
                      <Badge bg={getVerdictColor(model.prediction)}>
                        {model.prediction}
                      </Badge>
                    </td>
                    <td>{model.confidence}%</td>
                    <td>{model.fake_frame_count}</td>
                    <td>{model.real_frame_count}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card.Body>
        </Card>
      )}

      {/* Suspicious Frames Card */}
      {result.suspicious_frames && result.suspicious_frames.length > 0 && (
        <Card className="mb-3">
          <Card.Header>
            <h5 className="mb-0">⚠️ Suspicious Frames Detected</h5>
          </Card.Header>
          <Card.Body>
            <p className="mb-2">
              <strong>{result.suspicious_frames.length}</strong> frames show high probability of manipulation:
            </p>
            <div>
              {result.suspicious_frames.map((frameIdx, idx) => (
                <Badge key={idx} bg="danger" className="me-2 mb-2">
                  Frame {frameIdx}
                </Badge>
              ))}
            </div>
            <small className="text-muted">
              Suspicious frames have &gt;70% fake probability
            </small>
          </Card.Body>
        </Card>
      )}

      {/* Confidence Timeline */}
      {result.confidence_timeline && result.confidence_timeline.length > 0 && (
        <Card>
          <Card.Header>
            <h5 className="mb-0">Confidence Timeline</h5>
          </Card.Header>
          <Card.Body>
            <div className="confidence-timeline" style={{ display: 'flex', gap: '2px', height: '80px', alignItems: 'flex-end' }}>
              {result.confidence_timeline.map((confidence, idx) => {
                const color = confidence > 70 ? '#dc3545' : confidence > 50 ? '#ffc107' : '#198754';
                return (
                  <div
                    key={idx}
                    style={{
                      flex: 1,
                      height: `${confidence}%`,
                      backgroundColor: color,
                      opacity: 0.8,
                      transition: 'opacity 0.2s',
                      cursor: 'pointer'
                    }}
                    title={`Frame ${idx}: ${confidence.toFixed(1)}%`}
                    onMouseEnter={(e) => e.target.style.opacity = 1}
                    onMouseLeave={(e) => e.target.style.opacity = 0.8}
                  />
                );
              })}
            </div>
            <div className="d-flex justify-content-between mt-2 text-muted small">
              <span>Frame 0</span>
              <span>Frame {result.confidence_timeline.length - 1}</span>
            </div>
            <small className="text-muted">
              Hover over bars to see individual frame confidence
            </small>
          </Card.Body>
        </Card>
      )}
    </div>
  );
};

export default VideoResults;
