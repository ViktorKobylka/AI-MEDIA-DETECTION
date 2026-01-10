/**
 * Results Component
 * Displays detection results with individual model breakdown
 */

import React from 'react';
import { Card, Badge, ProgressBar, Alert } from 'react-bootstrap';

const Results = ({ result }) => {
  const getVerdictVariant = (verdict) => {
    switch (verdict) {
      case 'FAKE':
        return 'danger';
      case 'REAL':
        return 'success';
      case 'UNCERTAIN':
        return 'warning';
      default:
        return 'secondary';
    }
  };

  const getVerdictIcon = (verdict) => {
    switch (verdict) {
      case 'FAKE':
        return '🔴';
      case 'REAL':
        return '🟢';
      case 'UNCERTAIN':
        return '🟡';
      default:
        return '⚪';
    }
  };

  const getAgreementBadge = (level) => {
    switch (level) {
      case 'HIGH':
        return 'success';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
        return 'danger';
      default:
        return 'secondary';
    }
  };

  return (
    <Card className="mt-4 results-card">
      <Card.Body>
        <div className="text-center mb-4">
          <h2 className="mb-3">
            {getVerdictIcon(result.verdict)} {result.verdict}
          </h2>
          <h4 className="text-muted">
            Confidence: {result.confidence.toFixed(2)}%
          </h4>
          <Badge bg={getAgreementBadge(result.agreement_level)} className="mt-2">
            Agreement: {result.agreement_level}
          </Badge>
        </div>

        <ProgressBar className="mb-4" style={{ height: '30px' }}>
          <ProgressBar 
            variant="danger" 
            now={result.fake_probability * 100} 
            label={`${(result.fake_probability * 100).toFixed(1)}% Fake`}
            key={1}
          />
          <ProgressBar 
            variant="success" 
            now={result.real_probability * 100} 
            label={`${(result.real_probability * 100).toFixed(1)}% Real`}
            key={2}
          />
        </ProgressBar>

        <h6 className="mb-3">Individual Models:</h6>
        <div className="models-breakdown">
          {result.individual_results.map((model, index) => (
            <Card key={index} className="mb-2" bg="light">
              <Card.Body className="py-2">
                <div className="d-flex justify-content-between align-items-center">
                  <div>
                    <strong>{model.model}</strong>
                  </div>
                  <div className="text-end">
                    <Badge bg={getVerdictVariant(model.prediction)}>
                      {model.prediction}
                    </Badge>
                    {' '}
                    <span className="text-muted">
                      {model.confidence.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </Card.Body>
            </Card>
          ))}
        </div>

        <Alert variant="info" className="mt-3 mb-0">
          <div className="d-flex align-items-start">
            <i className="bi bi-lightbulb me-2"></i>
            <div>
              <strong>Recommendation:</strong> {result.recommendation}
            </div>
          </div>
        </Alert>
      </Card.Body>
    </Card>
  );
};

export default Results;
