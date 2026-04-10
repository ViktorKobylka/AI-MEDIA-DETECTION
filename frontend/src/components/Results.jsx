/**
 * Results Component
 * Вisplay for both fresh image detections and cached results
 */

import React from 'react';
import { Card, Badge, ProgressBar, Row, Col, Alert } from 'react-bootstrap';
import './Results.css';

const Results = ({ result }) => {
  console.log('Results received:', result); // Debug

  // Safety check
  if (!result) {
    return (
      <Alert variant="warning">
        No results to display
      </Alert>
    );
  }

  const isCached = result.cached || false;
  
  // Extract main verdict data
  // Try multiple sources for compatibility
  const verdict = result.verdict || result.final?.verdict || 'UNKNOWN';
  const confidence = result.confidence || result.final?.confidence || 0;
  const fakeProb = result.fake_probability !== undefined 
    ? result.fake_probability 
    : (result.final?.fake_probability || 0);
  const realProb = result.real_probability !== undefined
    ? result.real_probability
    : (result.final?.real_probability || 0);
  const agreement = result.agreement_level || result.final?.agreement || 'unknown';
  
  // Extract detector results
  const detectors = result.detectors || {};
  const sightengine = detectors.sightengine || { available: false };
  const mobilenet = detectors.mobilenet || { available: false };

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

  // Detector display component
  const DetectorCard = ({ name, icon, data, bgClass }) => {
    const isAvailable = data && data.available;
    
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
                  bg={getVerdictVariant(data.verdict)}
                  className="px-3 py-2"
                  style={{ fontSize: '1rem' }}
                >
                  {data.verdict || 'UNKNOWN'}
                </Badge>
              </div>

              <div className="mb-2">
                <small className="text-muted d-block">Confidence</small>
                <h5 className="mb-1">
                  {data.confidence ? data.confidence.toFixed(1) : '0.0'}%
                </h5>
              </div>

              <div className="d-flex justify-content-between small text-muted mb-2">
                <span>Fake: {data.fake_probability ? data.fake_probability.toFixed(1) : '0.0'}%</span>
                <span>Real: {data.real_probability ? data.real_probability.toFixed(1) : '0.0'}%</span>
              </div>

              <ProgressBar style={{ height: '8px' }}>
                <ProgressBar 
                  variant="danger" 
                  now={data.fake_probability || 0} 
                  key={1}
                />
                <ProgressBar 
                  variant="success" 
                  now={data.real_probability || 0} 
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
            <i className="bi bi-shield-check me-2"></i>
            Detection Result
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
              {confidence ? confidence.toFixed(1) : '0.0'}%
            </h1>
          </div>

          {/* Probability Bar */}
          <div className="mb-3">
            <div className="d-flex justify-content-between mb-2">
              <span className="text-danger fw-bold">
                <i className="bi bi-x-circle me-1"></i>
                Fake: {fakeProb ? fakeProb.toFixed(1) : '0.0'}%
              </span>
              <span className="text-success fw-bold">
                <i className="bi bi-check-circle me-1"></i>
                Real: {realProb ? realProb.toFixed(1) : '0.0'}%
              </span>
            </div>
            
            <ProgressBar style={{ height: '30px' }}>
              <ProgressBar 
                variant="danger" 
                now={fakeProb || 0} 
                label={fakeProb > 10 ? `${(fakeProb || 0).toFixed(1)}%` : ''}
                key={1}
                className="fw-bold"
              />
              <ProgressBar 
                variant="success" 
                now={realProb || 0} 
                label={realProb > 10 ? `${(realProb || 0).toFixed(1)}%` : ''}
                key={2}
                className="fw-bold"
              />
            </ProgressBar>
          </div>

          {/* Agreement Badge */}
          <div className="mt-3">
            <Badge bg={agreementBadge.variant} className="px-3 py-2">
              <i className="bi bi-diagram-3 me-2"></i>
              {agreementBadge.text}
            </Badge>
          </div>
        </Card.Body>
      </Card>

      {/* Individual Detector Results */}
      <Card className="shadow-sm">
        <Card.Header className="bg-light">
          <h5 className="mb-0">
            <i className="bi bi-cpu me-2"></i>
            Model Breakdown
          </h5>
        </Card.Header>
        <Card.Body>
          <Row>
            <Col md={6} className="mb-3 mb-md-0">
              <DetectorCard
                name="SightEngine API"
                icon="bi bi-cloud-check"
                data={sightengine}
                bgClass="sightengine-card"
              />
            </Col>
            <Col md={6}>
              <DetectorCard
                name="MobileNetV4"
                icon="bi bi-cpu"
                data={mobilenet}
                bgClass="mobilenet-card"
              />
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Processing Info */}
      {result.processing_time_seconds && (
        <div className="text-center mt-3">
          <small className="text-muted">
            <i className="bi bi-clock me-1"></i>
            Processed in {result.processing_time_seconds.toFixed(2)}s
            {isCached && ' (from cache)'}
          </small>
        </div>
      )}
    </div>
  );
};

export default Results;