import { getApiUrl, checkBackendConnectivity, handleApiError } from './backendConfig';

// Mock data for speech analysis
interface SpeechFeedback {
  pronunciation: number;
  fluency: number;
  rhythm: number;
  overall: number;
  suggestions: string[];
}

// Define voice interface for text-to-speech options
export interface Voice {
  id: string;
  name: string;
  gender: string;
  accent: string;
}

// Available voices for text-to-speech
// This 'availableVoices' mock is likely superseded by fetchAvailableVoices,
// but kept for reference or if used elsewhere directly.
export const googleVoices: Voice[] = [
  { id: 'en-US-Studio-M', name: 'Studio M (Male, US)', accent: 'American', gender: 'Male' },
  { id: 'en-US-Studio-O', name: 'Studio O (Female, US)', accent: 'American', gender: 'Female' },
];

// Mock phrases for practice
export const practiceExamples = [
  "The quick brown fox jumps over the lazy dog.",
  "She sells seashells by the seashore.",
  "How much wood would a woodchuck chuck if a woodchuck could chuck wood?"
];

// Simulate recording and processing speech with random delays
export const analyzeSpeech = (duration: number): Promise<SpeechFeedback> => {
  return new Promise((resolve) => {
    // Simulate backend processing time
    setTimeout(() => {
      // Generate simulated feedback with slight randomness
      resolve({
        pronunciation: 70 + Math.floor(Math.random() * 20),
        fluency: 65 + Math.floor(Math.random() * 25),
        rhythm: 75 + Math.floor(Math.random() * 20),
        overall: 70 + Math.floor(Math.random() * 20),
        suggestions: [
          "Try slowing down on complex words",
          "Pay attention to the 'th' sound",
          "Great job with intonation patterns",
          "Focus on syllable stress in longer words"
        ]
      });
    }, 1500);
  });
};


// Get audio from Google TTS API via our backend
export const getGoogleTTSAudio = async (text: string, voiceId: string, speed: number): Promise<Blob> => {
  try {
    // First check if backend is accessible
    const isConnected = await checkBackendConnectivity();
    if (!isConnected) {
      throw new Error(
        `Cannot connect to the speech server. Please make sure the Flask backend is running at ${getApiUrl('')}`
      );
    }
    
    const response = await fetch(getApiUrl('/api/tts_google'), { // Changed to /api/tts_google
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        voiceId: voiceId,
        speed
      }),
      credentials: 'include', // Add credentials include
    });
    
    if (!response.ok) {
      let errorMessage = `Failed with status: ${response.status}`;
      try {
        // Try to parse JSON error first
        const errorData = await response.json();
        errorMessage = errorData.error || JSON.stringify(errorData);
      } catch (jsonError) {
        // If JSON parsing fails, try to get text error
        try {
          const textError = await response.text();
          if (textError) {
            errorMessage = textError;
          }
        } catch (textErrorErr) {
          // Ignore if text parsing also fails
        }
      }
      // Limit the length of the error message shown to the user
      throw new Error(errorMessage.substring(0, 200)); 
    }
    
    // Check content type before assuming blob
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('audio/mpeg')) {
      console.warn(`Unexpected content type received: ${contentType}`);
      // Try to read as text to see if it's an error message
      const potentialErrorText = await response.text();
      throw new Error(`Received unexpected response format from server. ${potentialErrorText.substring(0,100)}`);
    }

    return await response.blob();
  } catch (error) {
    console.error('Error in text-to-speech API call:', error);
    throw handleApiError(error);
  }
};

// Get audio from custom Google Cloud TTS and googletrans backend
export const getCustomTTSAudio = async (text: string): Promise<string> => {
  try {
    console.log('getCustomTTSAudio called with text:', text);
    
    // First check if backend is accessible
    console.log('Checking backend connectivity...');
    const isConnected = await checkBackendConnectivity();
    console.log('Backend connectivity check result:', isConnected);
    
    if (!isConnected) {
      console.error('Backend not connected, cannot fetch custom TTS audio.');
      throw new Error('Backend not connected');
    }

    console.log('Making request to custom TTS API...');
    const apiUrl = getApiUrl('/api/texttospeech');
    console.log('API URL:', apiUrl);
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
      credentials: 'include', // Add credentials include
    });
    
    console.log('Response status:', response.status, response.statusText);

    if (!response.ok) {
      let errorMessage = `Failed with status: ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || JSON.stringify(errorData);
        console.error('Error data:', errorData);
      } catch (jsonError) {
        try {
          const textError = await response.text();
          if (textError) {
            errorMessage = textError;
            console.error('Error text:', textError);
          }
        } catch (textErrorErr) { /* ignore */ }
      }
      throw new Error(errorMessage.substring(0, 200));
    }

    const data = await response.json();
    if (!data.audio_base64) {
      throw new Error('No audio data received from custom TTS endpoint');
    }
    return data.audio_base64;

  } catch (error) {
    console.error('Error in custom text-to-speech API call:', error);
    throw handleApiError(error);
  }
};

// Fetch available voices from API
export const fetchAvailableVoices = async (): Promise<Voice[]> => {
  try {
    const response = await fetch(getApiUrl('/api/voices'), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    if (!response.ok) {
      console.error(`Error fetching voices, status: ${response.status} ${response.statusText}. Falling back to default voices.`);
      try {
        const errorBody = await response.json();
        console.error("Error body from /api/voices:", errorBody);
      } catch (e) {
        // Ignore if error body isn't json or doesn't exist
      }
      return googleVoices;
    }
    
    const data = await response.json();
    // Check if data has a 'voices' property and if it's an array
    if (data && Array.isArray(data.voices)) {
      return data.voices;
    } else if (Array.isArray(data)) { // Fallback for previous direct array response
      return data; // Assuming 'data' itself is the array of voices
    }
    // If data is not in the expected format, log a warning and fall back to default voices
    console.warn('Unexpected data format from /api/voices. Expected { voices: [] } or []. Falling back to default voices.', data);
    return googleVoices;

  } catch (error) {
    console.error('Failed to fetch available voices:', error);
    // Fallback to googleVoices in case of any error during fetch
    return googleVoices;
  }
};
