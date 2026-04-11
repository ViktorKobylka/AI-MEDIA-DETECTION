import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Statistics from './pages/Statistics';
import About from './pages/About';
import './App.css';


function App() {
  return (
    <Router>
      <div className="App">
        {/* Header */}
        <div className="header-navbar-wrapper">
          <div className="header text-white py-4">
            <div className="container">
              <h1 className="text-center mb-2">
                AI Media Detector
              </h1>
              <p className="text-center mb-0">
                Upload an image or video to detect if it's AI-generated
              </p>
            </div>
          </div>
          { /* Navigation */}
          <Navbar />
        </div>

        {/* Routes */}
        <div>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/statistics" element={<Statistics />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </div>

        {/* Footer */}
        <div className="text-center mt-5 mb-4">
          <div className="mb-3">
            <h6 className="text-muted mb-2">About This Application</h6>
            <p className="text-muted mb-1" style={{ fontSize: '0.9rem' }}>
              AI-powered deepfake detection system with dual-detector architecture and continual learning.
            </p>
            <p className="text-muted mb-1" style={{ fontSize: '0.9rem' }}>
              <strong>Detects:</strong> AI-generated faces, deepfakes and synthetic media
            </p>
          </div>
        </div>
      </div>
    </Router>
  );
}

export default App;
