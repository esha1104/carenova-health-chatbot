/**
 * API Client for Carenova Health Chatbot
 * Wrapper functions to communicate with FastAPI backend
 */

const API_BASE_URL = window.location.origin || 'http://localhost:8000';
const API_TIMEOUT = 10000; // 10 seconds

/**
 * Make a fetch request with timeout and error handling
 */
async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('Request timeout - backend may be unavailable');
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Initialize API client (can add configuration logic here)
 */
function initAPI(baseURL = null) {
  if (baseURL) {
    window.API_BASE_URL = baseURL;
  }
  console.log('API Client initialized with base URL:', API_BASE_URL);
}

/**
 * Check backend health
 */
async function checkHealth() {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/health`);
    console.log('Backend health check:', response);
    return response;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
}

/**
 * Get follow-up questions based on initial symptoms
 * @param {string} symptoms - User's initial symptom description
 * @returns {Promise<{questions: string[]}>}
 */
async function getFollowupQuestions(symptoms) {
  if (!symptoms || symptoms.trim().length === 0) {
    throw new Error('Please describe your symptoms');
  }

  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/followup-questions`, {
      method: 'POST',
      body: JSON.stringify({ symptoms: symptoms.trim() }),
    });
    console.log('Follow-up questions received:', response);
    return response;
  } catch (error) {
    console.error('Error fetching follow-up questions:', error);
    throw error;
  }
}

/**
 * Analyze symptoms based on initial symptoms and follow-up answers
 * @param {string} initialSymptoms - Initial symptom description
 * @param {string[]} followupAnswers - Answers to follow-up questions
 * @returns {Promise<Object>} Analysis results
 */
async function analyzeSymptoms(initialSymptoms, followupAnswers) {
  if (!initialSymptoms || initialSymptoms.trim().length === 0) {
    throw new Error('Please describe your symptoms');
  }

  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      body: JSON.stringify({
        initial_symptoms: initialSymptoms.trim(),
        followup_answers: followupAnswers || [],
      }),
    });
    console.log('Analysis results received:', response);
    return response;
  } catch (error) {
    console.error('Error analyzing symptoms:', error);
    throw error;
  }
}

/**
 * Submit contact form
 * @param {string} name - User's name
 * @param {string} email - User's email
 * @param {string} message - Contact message
 * @returns {Promise<{status: string, message: string}>}
 */
async function submitContact(name, email, message) {
  if (!name || !email || !message) {
    throw new Error('All fields are required');
  }

  // Basic email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Please enter a valid email address');
  }

  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/contact`, {
      method: 'POST',
      body: JSON.stringify({ name, email, message }),
    });
    console.log('Contact form submitted successfully:', response);
    return response;
  } catch (error) {
    console.error('Error submitting contact form:', error);
    throw error;
  }
}

/**
 * Export all functions for use in HTML
 */
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initAPI,
    checkHealth,
    getFollowupQuestions,
    analyzeSymptoms,
    submitContact,
  };
}
