/**
 * Statistics Page
 * Main analytics page with detection statistics and retraining status
 */

import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Badge, ProgressBar, Spinner, Alert } from 'react-bootstrap';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../services/api';

const Statistics = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      
      const response = await api.get('/statistics');
      
      if (response.success) {
        setStats(response.statistics);
      } else {
        setError('Failed to load statistics');
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Statistics error:', err);
      setError(err.message || 'Failed to load statistics');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Container className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3 text-muted">Loading statistics...</p>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="py-5">
        <Alert variant="danger">
          <Alert.Heading>Error Loading Statistics</Alert.Heading>
          <p>{error}</p>
        </Alert>
      </Container>
    );
  }

  // Extract data
  const detections = stats?.detections || {};
  const collection = stats?.collection || {};
  
  const totalDetections = detections.total_detections || 0;
  const fakeCount = detections.fake_count || 0;
  const realCount = detections.real_count || 0;
  const fakePercent = totalDetections > 0 ? ((fakeCount / totalDetections) * 100).toFixed(1) : 0;
  const realPercent = totalDetections > 0 ? ((realCount / totalDetections) * 100).toFixed(1) : 0;

  // Collection data
  const currentRound = collection?.current_round || 1;
  const totalCollected = collection?.total_collected || 0;
  const realCollected = collection?.real_collected || 0;
  const fakeCollected = collection?.fake_collected || 0;
  const targetFiles = 400;
  const collectionProgress = (totalCollected / targetFiles * 100).toFixed(1);

  // Pie chart data
  const pieData = [
    { name: 'FAKE', value: fakeCount, color: '#dc3545' },
    { name: 'REAL', value: realCount, color: '#198754' }
  ];

  return (
    <Container className="py-4">
      {/* Page Header */}
      <h2 className="mb-4">
        <i className="bi bi-bar-chart me-2"></i>
        Statistics & Analytics
      </h2>

      {/* Statistics Cards */}
      <Row className="mb-4">
        {/* Total Detections */}
        <Col md={4} className="mb-3">
          <Card className="h-100 shadow-sm border-0" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
            <Card.Body className="text-white">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-white-50 mb-2 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Total Detections
                  </h6>
                  <h2 className="mb-0 fw-bold" style={{ fontSize: '2.5rem' }}>
                    {totalDetections.toLocaleString()}
                  </h2>
                </div>
                <div>
                  <i className="bi bi-file-earmark-check" style={{ fontSize: '3.5rem', opacity: 0.2 }}></i>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        {/* Fake Detected */}
        <Col md={4} className="mb-3">
          <Card className="h-100 shadow-sm border-0" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
            <Card.Body className="text-white">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-white-50 mb-2 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Fake Detected
                  </h6>
                  <h2 className="mb-0 fw-bold" style={{ fontSize: '2.5rem' }}>
                    {fakeCount.toLocaleString()}
                  </h2>
                  <small className="text-white-50">{fakePercent}% of total</small>
                </div>
                <div>
                  <i className="bi bi-x-circle" style={{ fontSize: '3.5rem', opacity: 0.2 }}></i>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        {/* Real Detected */}
        <Col md={4} className="mb-3">
          <Card className="h-100 shadow-sm border-0" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
            <Card.Body className="text-white">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-white-50 mb-2 text-uppercase" style={{ fontSize: '0.75rem' }}>
                    Real Detected
                  </h6>
                  <h2 className="mb-0 fw-bold" style={{ fontSize: '2.5rem' }}>
                    {realCount.toLocaleString()}
                  </h2>
                  <small className="text-white-50">{realPercent}% of total</small>
                </div>
                <div>
                  <i className="bi bi-check-circle" style={{ fontSize: '3.5rem', opacity: 0.2 }}></i>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Verdict Distribution Chart */}
      <Row className="mb-4">
        <Col lg={12} className="mb-3">
          <Card className="h-100 shadow-sm">
            <Card.Header className="bg-light">
              <h5 className="mb-0">
                <i className="bi bi-pie-chart me-2"></i>
                Verdict Distribution
              </h5>
            </Card.Header>
            <Card.Body className="d-flex align-items-center justify-content-center">
              {totalDetections > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={true}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={120}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-center text-muted py-5">
                  <i className="bi bi-pie-chart" style={{ fontSize: '3rem', opacity: 0.3 }}></i>
                  <p className="mt-3 mb-0">No data available</p>
                  <small>Upload images to see distribution</small>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Retraining Status Section */}
      <Row>
        <Col lg={12}>
          <Card className="shadow-sm" style={{ borderTop: '3px solid #0d6efd' }}>
            <Card.Header className="bg-primary text-white">
              <h5 className="mb-0">
                <i className="bi bi-arrow-repeat me-2"></i>
                Continual Learning & Retraining Status
              </h5>
            </Card.Header>
            <Card.Body>
              <Row>
                {/* Collection Progress */}
                <Col md={6} className="mb-4 mb-md-0">
                  <h6 className="text-muted mb-3">
                    <i className="bi bi-collection me-2"></i>
                    Data Collection Progress
                  </h6>
                  
                  <div className="mb-4">
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <span className="fw-bold">Current Round:</span>
                      <Badge bg="primary" className="px-3 py-2">
                        Round {currentRound}
                      </Badge>
                    </div>
                    
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <span className="fw-bold">Total Files:</span>
                      <span className="text-muted">{totalCollected} / {targetFiles}</span>
                    </div>

                    <ProgressBar 
                      now={collectionProgress} 
                      label={`${collectionProgress}%`}
                      className="mb-3"
                      style={{ height: '30px' }}
                      variant={totalCollected >= targetFiles ? 'success' : 'primary'}
                    />
                  </div>

                  <div className="mb-3">
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <span className="text-success">
                        <i className="bi bi-check-circle-fill me-1"></i>
                        Real Files
                      </span>
                      <strong>{realCollected} / 200</strong>
                    </div>
                    <ProgressBar 
                      variant="success" 
                      now={(realCollected / 200) * 100} 
                      style={{ height: '15px' }}
                      label={realCollected > 10 ? `${realCollected}` : ''}
                    />
                  </div>

                  <div>
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <span className="text-danger">
                        <i className="bi bi-x-circle-fill me-1"></i>
                        Fake Files
                      </span>
                      <strong>{fakeCollected} / 200</strong>
                    </div>
                    <ProgressBar 
                      variant="danger" 
                      now={(fakeCollected / 200) * 100} 
                      style={{ height: '15px' }}
                      label={fakeCollected > 10 ? `${fakeCollected}` : ''}
                    />
                  </div>
                </Col>

                {/* Retraining Information */}
                <Col md={6}>
                  <h6 className="text-muted mb-3">
                    <i className="bi bi-calendar-check me-2"></i>
                    Retraining Information
                  </h6>
                  
                  <div className="mb-3">
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <span className="fw-bold">Next Retraining:</span>
                      <Badge bg={totalCollected >= targetFiles ? 'success' : 'secondary'} className="px-3 py-2">
                        {totalCollected >= targetFiles 
                          ? 'Ready!' 
                          : `${targetFiles - totalCollected} files needed`}
                      </Badge>
                    </div>
                  </div>

                  <div className="mb-4">
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <span className="fw-bold">Completed Rounds:</span>
                      <Badge bg="info" className="px-3 py-2">
                        {currentRound - 1} rounds
                      </Badge>
                    </div>
                  </div>

                  <Alert variant="info" className="mb-0">
                    <i className="bi bi-info-circle me-2"></i>
                    <small>
                      <strong>How it works:</strong> When 400 files are collected (200 real + 200 fake), 
                      the system automatically triggers retraining using experience replay 
                      to prevent catastrophic forgetting. Check runs at 3:00 AM daily.
                    </small>
                  </Alert>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Statistics;