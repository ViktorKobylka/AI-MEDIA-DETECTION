/**
 * AIQuiz Component
 * Interactive challenge to spot ai
 */

import React, { useState } from 'react';
import { Card, Button, Row, Col, Alert } from 'react-bootstrap';

const AIQuiz = () => {
  const [selectedA, setSelectedA] = useState(null);
  const [selectedB, setSelectedB] = useState(null);
  const [revealed, setRevealed] = useState(false);

  
  const imageA = {
    path: '/quiz-images/image1.jpg',  
    answer: 'REAL',  
    description: 'Original image'  
  };

  const imageB = {
    path: '/quiz-images/image2.jpg',  
    answer: 'FAKE',  
    description: 'AI-generated image'  
  };

  const handleReveal = () => {
    setRevealed(true);
  };

  const handleReset = () => {
    setSelectedA(null);
    setSelectedB(null);
    setRevealed(false);
  };

  const getResultVariant = (selected, correct) => {
    if (!revealed) return 'secondary';
    return selected === correct ? 'success' : 'danger';
  };

  const getScore = () => {
    let correct = 0;
    if (selectedA === imageA.answer) correct++;
    if (selectedB === imageB.answer) correct++;
    return correct;
  };

  return (
    <Card className="shadow-sm">
      <Card.Header className="bg-warning text-dark">
        <h5 className="mb-0">
          <i className="bi bi-puzzle me-2"></i>
           Spot the AI-Generated Image Challenge
        </h5>
      </Card.Header>
      <Card.Body>
        <p className="text-muted mb-4">
          Can you tell which image is a real image and which was created by AI? 
        </p>

        <Row>
          {/* Image A */}
          <Col md={6} className="mb-4">
            <Card className="h-100">
              <Card.Img 
                variant="top" 
                src={imageA.path} 
                alt="Image A"
                style={{ height: '300px', objectFit: 'cover' }}
              />
              <Card.Body>
                <h6 className="mb-3">Image A</h6>
                
                <div className="d-grid gap-2">
                  <Button
                    variant={selectedA === 'REAL' ? 'success' : 'outline-success'}
                    onClick={() => !revealed && setSelectedA('REAL')}
                    disabled={revealed}
                  >
                    <i className="bi bi-check-circle me-2"></i>
                    Real
                  </Button>
                  <Button
                    variant={selectedA === 'FAKE' ? 'danger' : 'outline-danger'}
                    onClick={() => !revealed && setSelectedA('FAKE')}
                    disabled={revealed}
                  >
                    <i className="bi bi-x-circle me-2"></i>
                    Fake (AI-generated)
                  </Button>
                </div>

                {revealed && (
                  <Alert variant={getResultVariant(selectedA, imageA.answer)} className="mt-3 mb-0">
                    <strong>Answer: {imageA.answer}</strong>
                    <br />
                    <small>{imageA.description}</small>
                    {selectedA === imageA.answer && (
                      <div className="mt-2">
                        <i className="bi bi-check-circle-fill me-1"></i>
                        Correct!
                      </div>
                    )}
                    {selectedA !== imageA.answer && selectedA && (
                      <div className="mt-2">
                        <i className="bi bi-x-circle-fill me-1"></i>
                        Incorrect
                      </div>
                    )}
                  </Alert>
                )}
              </Card.Body>
            </Card>
          </Col>

          {/* Image B */}
          <Col md={6} className="mb-4">
            <Card className="h-100">
              <Card.Img 
                variant="top" 
                src={imageB.path} 
                alt="Image B"
                style={{ height: '300px', objectFit: 'cover' }}
              />
              <Card.Body>
                <h6 className="mb-3">Image B</h6>
                
                <div className="d-grid gap-2">
                  <Button
                    variant={selectedB === 'REAL' ? 'success' : 'outline-success'}
                    onClick={() => !revealed && setSelectedB('REAL')}
                    disabled={revealed}
                  >
                    <i className="bi bi-check-circle me-2"></i>
                    Real
                  </Button>
                  <Button
                    variant={selectedB === 'FAKE' ? 'danger' : 'outline-danger'}
                    onClick={() => !revealed && setSelectedB('FAKE')}
                    disabled={revealed}
                  >
                    <i className="bi bi-x-circle me-2"></i>
                    Fake (AI-generated)
                  </Button>
                </div>

                {revealed && (
                  <Alert variant={getResultVariant(selectedB, imageB.answer)} className="mt-3 mb-0">
                    <strong>Answer: {imageB.answer}</strong>
                    <br />
                    <small>{imageB.description}</small>
                    {selectedB === imageB.answer && (
                      <div className="mt-2">
                        <i className="bi bi-check-circle-fill me-1"></i>
                        Correct!
                      </div>
                    )}
                    {selectedB !== imageB.answer && selectedB && (
                      <div className="mt-2">
                        <i className="bi bi-x-circle-fill me-1"></i>
                        Incorrect
                      </div>
                    )}
                  </Alert>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Action Buttons */}
        <div className="text-center mt-3">
          {!revealed ? (
            <Button
              variant="primary"
              size="lg"
              onClick={handleReveal}
              disabled={!selectedA || !selectedB}
            >
              <i className="bi bi-eye me-2"></i>
              Reveal Answers
            </Button>
          ) : (
            <>
              <Alert variant="info" className="mb-3">
                <strong>Your Score: {getScore()} / 2</strong>
                {getScore() === 2 && ' Perfect!'}
                {getScore() === 1 && ' Not bad!'}
                {getScore() === 0 && ' AI-generated images can fool anyone!'}
              </Alert>
              <Button
                variant="outline-primary"
                onClick={handleReset}
              >
                <i className="bi bi-arrow-clockwise me-2"></i>
                Try Again
              </Button>
            </>
          )}
        </div>
      </Card.Body>
    </Card>
  );
};

export default AIQuiz;