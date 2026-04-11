/**
 * About Page
 * Educational content about AI-generated content dangers and how the system works
 */

import React from 'react';
import { Container, Row, Col, Card, Badge, Alert } from 'react-bootstrap';
import AIQuiz from '../components/AIQuiz';

const About = () => {
  return (
    <Container className="py-4">

      {/* How It Works */}
      <Row className="mb-5">
        <Col lg={12}>
          <h3 className="mb-4 text-center">
            <i className="bi bi-gear me-2"></i>
            How It Works
          </h3>
          <Row>
            <Col md={4} className="mb-3">
              <Card className="h-100 text-center shadow-sm">
                <Card.Body>
                  <div className="mb-3" style={{ fontSize: '3rem' }}>
                    📤
                  </div>
                  <h5>1. Upload Media</h5>
                  <p className="text-muted">
                    Upload an image or short video to analyze
                  </p>
                </Card.Body>
              </Card>
            </Col>
            <Col md={4} className="mb-3">
              <Card className="h-100 text-center shadow-sm">
                <Card.Body>
                  <div className="mb-3" style={{ fontSize: '3rem' }}>
                    🔍
                  </div>
                  <h5>2. Dual Analysis</h5>
                  <p className="text-muted">
                    Both SightEngine and MobileNetV4 analyze independently
                  </p>
                </Card.Body>
              </Card>
            </Col>
            <Col md={4} className="mb-3">
              <Card className="h-100 text-center shadow-sm">
                <Card.Body>
                  <div className="mb-3" style={{ fontSize: '3rem' }}>
                    ✅
                  </div>
                  <h5>3. Get Results</h5>
                  <p className="text-muted">
                    Instant verdict: FAKE or REAL with confidence score
                  </p>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Col>
      </Row>

      {/* The Danger of AI Content */}
      <Row className="mb-5">
        <Col lg={12}>
          <Card className="shadow-sm border-danger">
            <Card.Header className="bg-danger text-white">
              <h4 className="mb-0">
                <i className="bi bi-exclamation-triangle me-2"></i>
                The Danger of AI-Generated Content
              </h4>
            </Card.Header>
            <Card.Body>
              <p className="lead mb-4">
                Deepfakes and AI-generated content pose serious threats to society, 
                democracy, and individual safety. Here are real cases that happened:
              </p>

              <Row>
                {/* Case 1: Political Deepfakes */}
                <Col md={6} className="mb-4">
                  <Card className="h-100 border-warning">
                    <Card.Body>
                      <Badge bg="warning" text="dark" className="mb-3">Political</Badge>
                      <h5 className="mb-3">Election Interference (2024)</h5>
                      <p>
                        A deepfake robocall impersonating President Biden told voters to 
                        "save your vote for the November election" during New Hampshire primaries.
                      </p>
                      <ul className="mb-0">
                        <li>Targeted thousands of voters</li>
                        <li>Attempted election manipulation</li>
                        <li>FCC investigation launched</li>
                      </ul>
                    </Card.Body>
                  </Card>
                </Col>

                {/* Case 2: Corporate Fraud */}
                <Col md={6} className="mb-4">
                  <Card className="h-100 border-danger">
                    <Card.Body>
                      <Badge bg="danger" className="mb-3">Financial Fraud</Badge>
                      <h5 className="mb-3">$25M CEO Deepfake (Hong Kong, 2024)</h5>
                      <p>
                        Criminals used deepfake video of a company's CFO to trick an employee 
                        into transferring $25 million to fraudulent accounts.
                      </p>
                      <ul className="mb-0">
                        <li>Multi-person video conference faked</li>
                        <li>Realistic voice and video clone</li>
                        <li>Largest deepfake fraud to date</li>
                      </ul>
                    </Card.Body>
                  </Card>
                </Col>

                {/* Case 3: Celebrity Scams */}
                <Col md={6} className="mb-4">
                  <Card className="h-100 border-primary">
                    <Card.Body>
                      <Badge bg="primary" className="mb-3">Identity Theft</Badge>
                      <h5 className="mb-3">Celebrity Deepfake Scams</h5>
                      <p>
                        Tom Hanks, Taylor Swift, Elon Musk, and others had their likenesses 
                        used in fake endorsements for scams and inappropriate content.
                      </p>
                      <ul className="mb-0">
                        <li>Fake product endorsements</li>
                        <li>Crypto scams using celebrity faces</li>
                        <li>Non-consensual deepfake content</li>
                      </ul>
                    </Card.Body>
                  </Card>
                </Col>

                {/* Case 4: Misinformation */}
                <Col md={6} className="mb-4">
                  <Card className="h-100 border-info">
                    <Card.Body>
                      <Badge bg="info" className="mb-3">Misinformation</Badge>
                      <h5 className="mb-3">Fake News & Propaganda</h5>
                      <p>
                        AI-generated images and videos spread false information about wars, 
                        disasters, and public figures across social media.
                      </p>
                      <ul className="mb-0">
                        <li>Fake war footage from conflicts</li>
                        <li>Fabricated disaster videos</li>
                        <li>Erosion of public trust in media</li>
                      </ul>
                    </Card.Body>
                  </Card>
                </Col>
              </Row>

              <Alert variant="warning" className="mt-4 mb-0">
                <i className="bi bi-info-circle me-2"></i>
                <strong>Why This Matters:</strong> Without detection tools, these attacks 
                will become more frequent and sophisticated. Early detection is crucial 
                for protecting individuals, organizations, and democratic processes.
              </Alert>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Interactive Quiz */}
      <Row className="mb-5">
        <Col lg={12}>
          <AIQuiz />
        </Col>
      </Row>

      {/* Our Solution */}
      <Row className="mb-5">
        <Col lg={12}>
          <Card className="shadow-sm border-success">
            <Card.Header className="bg-success text-white">
              <h4 className="mb-0">
                <i className="bi bi-check-circle me-2"></i>
                My Solution
              </h4>
            </Card.Header>
            <Card.Body>
              <Row>
                <Col md={6} className="mb-4 mb-md-0">
                  <h5 className="mb-3">Dual-Detector Approach</h5>
                  <div className="mb-3">
                    <h6>
                      <i className="bi bi-cloud-check text-primary me-2"></i>
                      SightEngine API
                    </h6>
                    <p className="text-muted mb-3">
                      Cloud-based detection with access to latest AI-generated content patterns. Also serves as an automatic labeler: high-confidence SightEngine predictions 
                        are used to build the training dataset for continual learning of MobileNetV4
                    </p>
                  </div>

                  <div className="mb-3">
                    <h6>
                      <i className="bi bi-cpu text-success me-2"></i>
                      MobileNetV4
                    </h6>
                    <p className="text-muted mb-3">
                      Local deep learning model trained on 14,000+ real and fake images
                    </p>
                  </div>

                  <div>
                    <h6>
                      <i className="bi bi-arrow-repeat text-warning me-2"></i>
                      Continual Learning
                    </h6>
                    <p className="text-muted mb-0">
                      Automatically retrains on new detections to stay current with evolving deepfakes
                    </p>
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      
    </Container>
  );
};

export default About;