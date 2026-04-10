/**
 * API Service for AI Detection Backend
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

/**
 * Check if API is healthy
 */
export const checkHealth = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/health`);
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};

/**
 * Detect if image is AI-generated
 */
export const detectImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post('/api/detect_dual', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};


/**
 * Detect if video is AI-generated 
 */
export const detectVideo = async (file) => {
  const formData = new FormData();
  formData.append('video', file);

  const response = await axios.post('/api/detect_video', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};


/**
 * Get detection history
 */
export const getHistory = async (params = {}) => {
  try {
    const queryParams = new URLSearchParams();
    
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.content_type) queryParams.append('content_type', params.content_type);
    if (params.verdict) queryParams.append('verdict', params.verdict);
    
    const response = await axios.get(`${API_BASE_URL}/history?${queryParams.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch history:', error);
    throw new Error(error.response?.data?.error || 'Failed to fetch history');
  }
};

/**
 * Search detection results by filename
 */
export const searchDetections = async (query, limit = 20) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/search`, {
      query,
      limit
    });
    return response.data;
  } catch (error) {
    console.error('Search failed:', error);
    throw new Error(error.response?.data?.error || 'Search failed');
  }
};

/**
 * Get overall detection statistics
 */
export const getStatistics = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/statistics`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch statistics:', error);
    throw new Error(error.response?.data?.error || 'Failed to fetch statistics');
  }
};
