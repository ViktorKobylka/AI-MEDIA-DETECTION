/**
 * HistoryCard Component
 * 
 * Displays a single detection result in the history
 */

import React from 'react';
import { Card, Badge, Row, Col } from 'react-bootstrap';

const HistoryCard = ({ result }) => {
  // Format timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Get verdict color
  const getVerdictVariant = (verdict) => {
    switch (verdict) {
      case 'FAKE': return 'danger';
      case 'REAL': return 'success';
      case 'UNCERTAIN': return 'warning';
      default: return 'secondary';
    }
  };

  // Get content type icon
  const getContentIcon = (type) => {
    return type === 'video' ? '🎬' : '📷';
  };

  return (
    <Card className="mb-3 history-card" style={{ cursor: 'pointer' }}>
      <Card.Body>
        <Row className="align-items-center">
          {/* Icon and Filename */}
          <Col md={5}>
            <div className="d-flex align-items-center">
              <span style={{ fontSize: '1.5rem', marginRight: '10px' }}>
                {getContentIcon(result.content_type)}
              </span>
              <div>
                <strong>{result.filename}</strong>
                <br />
                <small className="text-muted">
                  {result.content_type === 'video' && result.video_info ? (
                    `${result.video_info.duration}s, ${result.video_info.resolution}`
                  ) : (
                    result.content_type
                  )}
                </small>
              </div>
            </div>
          </Col>

          {/* Verdict */}
          <Col md={2}>
            <Badge bg={getVerdictVariant(result.verdict)} className="w-100">
              {result.verdict}
            </Badge>
          </Col>

          {/* Confidence */}
          <Col md={2}>
            <div className="text-center">
              <strong style={{ fontSize: '1.2rem' }}>{result.confidence}%</strong>
              <br />
              <small className="text-muted">Confidence</small>
            </div>
          </Col>

          {/* Cached Status */}
          <Col md={1}>
            {result.cached && (
              <Badge bg="info" title="Cached result">
                ⚡
              </Badge>
            )}
          </Col>

          {/* Time */}
          <Col md={2} className="text-end">
            <small className="text-muted">
              {formatTime(result.timestamp)}
            </small>
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );
};

export default HistoryCard;
