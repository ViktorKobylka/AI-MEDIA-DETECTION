/**
 * SearchBar Component
 * 
 * Search component with live filtering
 */

import React, { useState } from 'react';
import { Form, InputGroup, Button, Spinner } from 'react-bootstrap';

const SearchBar = ({ onSearch, loading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleClear = () => {
    setQuery('');
    onSearch(''); // Clear search results
  };

  return (
    <Form onSubmit={handleSubmit}>
      <InputGroup>
        <Form.Control
          type="text"
          placeholder="Search by filename..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
        />
        
        {query && (
          <Button 
            variant="outline-secondary" 
            onClick={handleClear}
            disabled={loading}
          >
            ✕
          </Button>
        )}
        
        <Button 
          variant="primary" 
          type="submit"
          disabled={loading || !query.trim()}
        >
          {loading ? (
            <>
              <Spinner
                as="span"
                animation="border"
                size="sm"
                role="status"
                aria-hidden="true"
                className="me-2"
              />
              Searching...
            </>
          ) : (
            'Search'
          )}
        </Button>
      </InputGroup>
      
      {query && (
        <Form.Text className="text-muted mt-2 d-block">
          Searching for: "{query}"
        </Form.Text>
      )}
    </Form>
  );
};

export default SearchBar;
