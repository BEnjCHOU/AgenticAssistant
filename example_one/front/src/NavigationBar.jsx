import React from 'react';
import Container from 'react-bootstrap/Container';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import 'bootstrap/dist/css/bootstrap.min.css';



function NavigationBar() {
    return (
    <Navbar fixed="top" expand="lg" className="bg-body-tertiary">
      <Container>
        <Navbar.Brand href="#">AgenticAssistant</Navbar.Brand>
        <NavDropdown className="fw-bold" title="Dropdown" id="basic-nav-dropdown">
            <NavDropdown.Item href="#action/3.1">GPT</NavDropdown.Item>
            <NavDropdown.Item href="#action/3.2">XAI</NavDropdown.Item>
            <NavDropdown.Item href="#action/3.3">Gemini</NavDropdown.Item>
        </NavDropdown>
      </Container>
    </Navbar>
  );
}
export default NavigationBar;