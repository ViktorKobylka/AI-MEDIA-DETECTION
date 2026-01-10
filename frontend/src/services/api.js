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
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${API_BASE_URL}/detect`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Detection failed:', error);
    
    if (error.response) {
      throw new Error(error.response.data.error || 'Detection failed');
    } else if (error.request) {
      throw new Error('Cannot connect to server');
    } else {
      throw new Error('An error occurred while processing the request');
    }
  }
};
