/**
 * History Page
 * 
 * Displays detection history with search and filter functionality
 */

import React, { useState, useEffect } from 'react';
import { Container, Alert, Spinner, Button } from 'react-bootstrap';
import { getHistory, searchDetections } from '../services/api';
import SearchBar from '../components/SearchBar';
import FilterBar from '../components/FilterBar';
import HistoryCard from '../components/HistoryCard';

const History = () => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchMode, setSearchMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  const [filters, setFilters] = useState({
    limit: 50,
    content_type: '',
    verdict: ''
  });

  // Fetch history on mount and when filters change
  useEffect(() => {
    if (!searchMode) {
      fetchHistory();
    }
  }, [filters, searchMode]);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await getHistory(filters);
      
      if (response.success) {
        setResults(response.results);
      } else {
        setError('Failed to load history');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (query) => {
    if (!query) {
      // Clear search, go back to history
      setSearchMode(false);
      setSearchQuery('');
      return;
    }

    setSearchMode(true);
    setSearchQuery(query);
    setLoading(true);
    setError(null);

    try {
      const response = await searchDetections(query, filters.limit);
      
      if (response.success) {
        setResults(response.results);
      } else {
        setError('Search failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    
    // If in search mode, re-run search with new filters
    if (searchMode && searchQuery) {
      handleSearch(searchQuery);
    }
  };

  const handleRefresh = () => {
    setSearchMode(false);
    setSearchQuery('');
    fetchHistory();
  };

  return (
    <Container>
      {/* Page Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>📋 Detection History</h2>
        <Button variant="outline-primary" onClick={handleRefresh}>
          Refresh
        </Button>
      </div>

      {/* Search Bar */}
      <div className="mb-4">
        <SearchBar onSearch={handleSearch} loading={loading} />
      </div>

      {/* Filter Bar */}
      {!searchMode && (
        <FilterBar filters={filters} onFilterChange={handleFilterChange} />
      )}

      {/* Search Mode Indicator */}
      {searchMode && (
        <Alert variant="info" className="mb-4">
          <strong>Search Results</strong> for "{searchQuery}" - 
          <Button 
            variant="link" 
            size="sm" 
            onClick={() => setSearchMode(false)}
          >
            Clear search
          </Button>
        </Alert>
      )}

      {/* Error Alert */}
      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          <strong>Error:</strong> {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-5">
          <Spinner animation="border" variant="primary" />
          <p className="mt-3">Loading...</p>
        </div>
      )}

      {/* Results */}
      {!loading && results.length > 0 && (
        <>
          <div className="mb-3">
            <small className="text-muted">
              Showing {results.length} result{results.length !== 1 ? 's' : ''}
            </small>
          </div>

          {results.map((result, index) => (
            <HistoryCard key={result._id || index} result={result} />
          ))}
        </>
      )}

      {/* Empty State */}
      {!loading && results.length === 0 && (
        <div className="text-center py-5">
          <div style={{ fontSize: '3rem', marginBottom: '20px' }}>
            📭
          </div>
          <h4>No Results Found</h4>
          <p className="text-muted">
            {searchMode 
              ? `No detections found matching "${searchQuery}"`
              : 'No detection history yet. Upload an image or video to get started!'}
          </p>
          {searchMode && (
            <Button variant="primary" onClick={() => setSearchMode(false)}>
              View All History
            </Button>
          )}
        </div>
      )}
    </Container>
  );
};

export default History;
