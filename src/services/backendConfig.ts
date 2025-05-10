/**
 * Configuration file for backend API settings
 */

// Base URL for API requests - change this for different environments
export const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://api.edumate.app' // Production API URL
  : 'http://localhost:5000';   // Local development API URL

// Helper function to get full API URL
export const getApiUrl = (endpoint: string): string => {
  // Remove leading slash if it exists
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
  return `${API_BASE_URL}/${cleanEndpoint}`;
};

// Helper function to handle API errors consistently
export const handleApiError = (error: unknown): Error => {
  if (error instanceof Error) {
    // Check for network-related errors like CORS or server not running
    if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
      return new Error(
        `Cannot connect to the server at ${API_BASE_URL}. Make sure the Flask backend is running and accessible.`
      );
    }
    return error;
  }
  return new Error('An unknown error occurred while communicating with the server');
};

// Check if the backend is accessible
export const checkBackendConnectivity = async (): Promise<boolean> => {
  try {
    console.log('Checking backend connectivity to:', getApiUrl('/api/health'));
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.log('Connectivity check timed out');
      controller.abort();
    }, 8000); // Increase timeout to 8 seconds
    
    const response = await fetch(getApiUrl('/api/health'), {
      method: 'GET',
      signal: controller.signal,
      // Ensure we're not affected by browser caching
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
    
    clearTimeout(timeoutId);
    
    console.log('Backend connectivity check response:', response.status, response.statusText);
    
    // Try to get the response body for more information
    try {
      const responseBody = await response.json();
      console.log('Backend health check details:', responseBody);
      
      // If we get a valid health check response with services
      if (responseBody && responseBody.services) {
        // Check specifically if TTS service is available
        const ttsAvailable = responseBody.services.tts === 'available';
        console.log('TTS service available:', ttsAvailable);
        
        if (!ttsAvailable) {
          console.warn('TTS service is not available according to health check');
        }
        
        // Still return true if overall health is OK, even if some services are limited
        return response.ok;
      }
    } catch (e) {
      console.log('Could not parse health check response body', e);
    }
    
    return response.ok;
  } catch (error) {
    console.error('Backend connectivity check failed with error:', error);
    return false;
  }
};

// Timeout duration for API requests (in milliseconds)
export const API_TIMEOUT = 30000; // 30 seconds
