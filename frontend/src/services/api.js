import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method.toUpperCase(), config.url, config.data);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.data);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    
    // Transform error for better user experience
    if (error.response) {
      const message = error.response.data?.detail || 
                     error.response.data?.message ||
                     'An error occurred while processing your request';
      throw new Error(message);
    } else if (error.request) {
      throw new Error('Unable to connect to the server. Please check if the backend is running.');
    } else {
      throw new Error('An unexpected error occurred');
    }
  }
);

/**
 * Calculate fares for a list of journeys
 * @param {Array} journeys - Array of journey objects with from_zone and to_zone
 * @returns {Promise} Response with calculated fares
 */
export const calculateFares = async (journeys) => {
  try {
    const response = await api.post('/api/calculate-fares', {
      journeys: journeys
    });
    return response.data;
  } catch (error) {
    console.error('Calculate fares error:', error);
    throw error;
  }
};

/**
 * Get fare rules from the backend
 * @returns {Promise} Response with fare rules
 */
export const getFareRules = async () => {
  try {
    const response = await api.get('/api/fare-rules');
    return response.data;
  } catch (error) {
    console.error('Get fare rules error:', error);
    throw error;
  }
};

/**
 * Health check for the API
 * @returns {Promise} Health status
 */
export const healthCheck = async () => {
  try {
    const response = await api.get('/api/health');
    return response.data;
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
};

export default api;
