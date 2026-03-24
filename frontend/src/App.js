import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import History from './pages/History';
import './App.css';


function App() {
  return (
    <Router>
      <div className="App">
        {/* Header */}
        <div className="header bg-primary text-white py-4 mb-4">
          <div className="container">
            <h1 className="text-center mb-2">
              AI Media Detector
            </h1>
            <p className="text-center mb-0">
              Upload an image or video to detect if it's AI-generated
            </p>
          </div>
        </div>

        {/* Navigation */}
        <Navbar />

        {/* Routes */}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/history" element={<History />} />
          <Route path="/statistics" element={
            <div className="container text-center py-5">
              <h2>Statistics</h2>
              <p className="text-muted">...</p>
            </div>
          } />
        </Routes>

        {/* Footer */}
        <div className="text-center mt-5 mb-4">
          <div className="mb-3">
            <h6 className="text-muted mb-2">About This Application</h6>
            <p className="text-muted mb-1" style={{ fontSize: '0.9rem' }}>
              This system detects AI-generated images, videos using advanced ensemble learning.
            </p>
            <p className="text-muted mb-1" style={{ fontSize: '0.9rem' }}>
              <strong>Detects:</strong> StyleGAN faces, face swaps, GAN-generated images, videos and photorealistic deepfakes
            </p>
          </div>
        </div>
      </div>
    </Router>
  );
}

export default App;
