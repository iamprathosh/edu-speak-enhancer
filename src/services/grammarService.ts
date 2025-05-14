import { getApiUrl } from './backendConfig';

// Mock data for grammar checking
export interface GrammarCorrection {
  original: string;
  corrected: string;
  explanation: string;
}

// Simulate grammar checking with mock data
export const checkGrammar = (text: string): Promise<GrammarCorrection[]> => {
  return new Promise((resolve, reject) => {
    // Call the backend API
    fetch(getApiUrl('/api/grammar-check'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text })
    })
    .then(response => {
      if (!response.ok) {
        // If the response is not OK, try to parse the error message from the backend
        return response.json().then(err => {
          // Prefer backend error message if available
          throw new Error(err.error || `Failed to check grammar. Status: ${response.status}`);
        }).catch(() => {
          // Fallback if error response is not JSON or other parsing issue
          throw new Error(`Failed to check grammar. Status: ${response.status}`);
        });
      }
      return response.json();
    })
    .then(data => {
      // Assuming the backend returns data in the GrammarCorrection[] format
      // or an empty array if no corrections are needed / text is perfect.
      resolve(data as GrammarCorrection[]);
    })
    .catch(error => {
      console.error('Error checking grammar:', error);
      // Reject the promise with the error so the calling code can handle it
      reject(error); 
    });
  });
};

// Simulate OCR (Optical Character Recognition) for uploaded images
export const processImage = (imageFile: File): Promise<string> => {
  return new Promise((resolve) => {
    // Simulate backend processing time
    setTimeout(() => {
      // In a real implementation, this would extract text from the image
      resolve("I have recieved your letter last week and I will response as soon as possible. Me and my team are working hardly on this project.");
    }, 2000);
  });
};
