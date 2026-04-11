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
    <BootstrapNavbar variant="dark" expand="lg">
      <Container>
        <BootstrapNavbar.Toggle aria-controls="navbar-nav" />
        
        <BootstrapNavbar.Collapse id="navbar-nav">
          <Nav className="mx-auto">
            <Nav.Link 
              as={Link} 
              to="/" 
              active={location.pathname === '/'}
              className="px-4"
            >
              Home
            </Nav.Link>
            
            
            <Nav.Link 
              as={Link} 
              to="/statistics" 
              active={location.pathname === '/statistics'}
              className="px-4"
            >
              Statistics
            </Nav.Link>


            <Nav.Link 
              as={Link} 
              to="/about" 
              active={location.pathname === '/about'}
              className="px-4"
            >
              About
            </Nav.Link>
            
          </Nav>
        </BootstrapNavbar.Collapse>
      </Container>
    </BootstrapNavbar>
       
  );
};

export default Navbar;
