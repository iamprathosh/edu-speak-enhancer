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
      body: JSON.stringify({ text }),
      credentials: 'include' // <<< Add this line
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
export const processImage = async (imageFile: File): Promise<string> => {
  const formData = new FormData();
  formData.append('file', imageFile);

  try {
    const response = await fetch(getApiUrl('/api/extract-text-from-image'), {
      method: 'POST',
      body: formData,
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to extract text from image. Invalid server response.' }));
      throw new Error(errorData.error || `Failed to extract text from image. Status: ${response.status}`);
    }

    const data = await response.json();
    if (typeof data.text === 'string') {
      return data.text;
    } else {
      throw new Error('Invalid text data received from image processing.');
    }
  } catch (error) {
    console.error('Error processing image:', error);
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('An unknown error occurred while processing the image.');
  }
};

// Function to process PDF files and extract text
export const processPdf = async (pdfFile: File): Promise<string> => {
  const formData = new FormData();
  formData.append('file', pdfFile);

  try {
    const response = await fetch(getApiUrl('/api/extract-text-from-pdf'), {
      method: 'POST',
      body: formData,
      credentials: 'include',
      // Note: Don't set 'Content-Type': 'multipart/form-data' manually for FormData.
      // The browser will set it correctly along with the boundary.
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to extract text from PDF. Invalid server response.' }));
      throw new Error(errorData.error || `Failed to extract text from PDF. Status: ${response.status}`);
    }

    const data = await response.json();
    if (typeof data.text === 'string') {
      return data.text;
    } else {
      throw new Error('Invalid text data received from PDF processing.');
    }
  } catch (error) {
    console.error('Error processing PDF:', error);
    if (error instanceof Error) {
      throw error; // Re-throw the original error if it's already an Error instance
    }
    throw new Error('An unknown error occurred while processing the PDF.');
  }
};
