/**
 * FilterBar Component
 * 
 * Filter controls for history page
 */

import React from 'react';
import { Form, Row, Col } from 'react-bootstrap';

const FilterBar = ({ filters, onFilterChange }) => {
  const handleChange = (field, value) => {
    onFilterChange({
      ...filters,
      [field]: value
    });
  };

  return (
    <div className="mb-4 p-3 bg-light rounded">
      <Row>
        {/* Content Type Filter */}
        <Col md={4}>
          <Form.Group>
            <Form.Label>Content Type</Form.Label>
            <Form.Select
              value={filters.content_type || ''}
              onChange={(e) => handleChange('content_type', e.target.value)}
            >
              <option value="">All Types</option>
              <option value="image">Images</option>
              <option value="video">Videos</option>
            </Form.Select>
          </Form.Group>
        </Col>

        {/* Verdict Filter */}
        <Col md={4}>
          <Form.Group>
            <Form.Label>Verdict</Form.Label>
            <Form.Select
              value={filters.verdict || ''}
              onChange={(e) => handleChange('verdict', e.target.value)}
            >
              <option value="">All Verdicts</option>
              <option value="FAKE">🔴 FAKE</option>
              <option value="REAL">🟢 REAL</option>
              <option value="UNCERTAIN">🟡 UNCERTAIN</option>
            </Form.Select>
          </Form.Group>
        </Col>

        {/* Limit Filter */}
        <Col md={4}>
          <Form.Group>
            <Form.Label>Results Limit</Form.Label>
            <Form.Select
              value={filters.limit || 50}
              onChange={(e) => handleChange('limit', parseInt(e.target.value))}
            >
              <option value="10">Last 10</option>
              <option value="25">Last 25</option>
              <option value="50">Last 50</option>
              <option value="100">Last 100</option>
            </Form.Select>
          </Form.Group>
        </Col>
      </Row>
    </div>
  );
};

export default FilterBar;
