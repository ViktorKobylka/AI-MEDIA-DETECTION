/**
 * Navbar Component
 * 
 * Navigation bar with links to different pages
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Container, Nav, Navbar as BootstrapNavbar } from 'react-bootstrap';

const Navbar = () => {
  const location = useLocation();

  return (
    <BootstrapNavbar bg="primary" variant="dark" expand="lg" className="mb-4">
      <Container>
        <BootstrapNavbar.Brand as={Link} to="/">
          AI Media Detector
        </BootstrapNavbar.Brand>
        
        <BootstrapNavbar.Toggle aria-controls="navbar-nav" />
        
        <BootstrapNavbar.Collapse id="navbar-nav">
          <Nav className="ms-auto">
            <Nav.Link 
              as={Link} 
              to="/" 
              active={location.pathname === '/'}
            >
              Home
            </Nav.Link>
            
            <Nav.Link 
              as={Link} 
              to="/history" 
              active={location.pathname === '/history'}
            >
              History
            </Nav.Link>
            
            <Nav.Link 
              as={Link} 
              to="/statistics" 
              active={location.pathname === '/statistics'}
            >
              Statistics
            </Nav.Link>
          </Nav>
        </BootstrapNavbar.Collapse>
      </Container>
    </BootstrapNavbar>
  );
};

export default Navbar;
