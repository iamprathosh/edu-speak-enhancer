import { getApiUrl } from './backendConfig';

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
  gender: 'male' | 'female';
  accent: string;
}

// Available voices for text-to-speech
export const availableVoices: Voice[] = [
  { id: 'en-US-1', name: 'Matthew', gender: 'male', accent: 'American' },
  { id: 'en-US-2', name: 'Olivia', gender: 'female', accent: 'American' },
  { id: 'en-GB-1', name: 'James', gender: 'male', accent: 'British' },
  { id: 'en-GB-2', name: 'Emma', gender: 'female', accent: 'British' },
  { id: 'en-AU-1', name: 'Jack', gender: 'male', accent: 'Australian' },
  { id: 'en-AU-2', name: 'Charlotte', gender: 'female', accent: 'Australian' }
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
        ].sort(() => 0.5 - Math.random()).slice(0, 3)
      });
    }, duration * 300); // Simulate longer processing for longer recordings
  });
};

// Simulate text-to-speech functionality
export const getAudioForPhrase = (
  phrase: string, 
  voiceId: string = 'en-US-1', 
  speed: number = 1.0
): string => {
  // In a real implementation, this would generate or fetch audio files
  // For now, we'll just return a mock URL
  return `https://api.example.com/tts?text=${encodeURIComponent(phrase)}&voice=${voiceId}&speed=${speed}`;
};

// Google TTS API options
export interface GoogleTTSOptions {
  text: string;
  voiceId: string; // The Google voice ID
  speed: number;   // Speech rate between 0.25 and 4.0
  pitch?: number;  // Optional pitch adjustment (-20.0 to 20.0)
  languageCode?: string; // Default to 'en-US' if not specified
}

// Function to call Google TTS API using our Flask backend
export const getGoogleTTSAudio = async (options: GoogleTTSOptions): Promise<ArrayBuffer> => {
  try {
    // Point to the Flask backend endpoint
    const endpoint = '/api/tts';
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: options.text,
        voiceId: options.voiceId,
        speed: options.speed,
      }),
    });

    if (!response.ok) {
      throw new Error(`TTS API error: ${response.status}`);
    }

    return await response.arrayBuffer();
  } catch (error) {
    console.error('Error calling TTS API:', error);
    throw error;
  }
};

// Function to fetch available voices from the backend
export const fetchAvailableVoices = async (): Promise<Voice[]> => {
  try {
    const response = await fetch('/api/voices');
    
    if (!response.ok) {
      throw new Error(`Failed to fetch voices: ${response.status}`);
    }
    
    const voices = await response.json();
    return voices;
  } catch (error) {
    console.error('Error fetching available voices:', error);
    // Return the mock voices as fallback
    return googleVoices.map(voice => ({
      id: voice.id,
      name: voice.name,
      gender: voice.gender.toLowerCase() as 'male' | 'female',
      accent: voice.accent
    }));
  }
};

// Map of Google TTS voices - these would come from the actual Google API
export const googleVoices = [
  { id: 'en-US-Wavenet-A', name: 'Wavenet A', accent: 'American', gender: 'Female' },
  { id: 'en-US-Wavenet-B', name: 'Wavenet B', accent: 'American', gender: 'Male' },
  { id: 'en-US-Wavenet-C', name: 'Wavenet C', accent: 'American', gender: 'Female' },
  { id: 'en-US-Wavenet-D', name: 'Wavenet D', accent: 'American', gender: 'Male' },
  { id: 'en-US-Wavenet-E', name: 'Wavenet E', accent: 'American', gender: 'Female' },
  { id: 'en-US-Wavenet-F', name: 'Wavenet F', accent: 'American', gender: 'Female' },
  { id: 'en-GB-Wavenet-A', name: 'Wavenet A', accent: 'British', gender: 'Female' },
  { id: 'en-GB-Wavenet-B', name: 'Wavenet B', accent: 'British', gender: 'Male' },
  { id: 'en-GB-Wavenet-C', name: 'Wavenet C', accent: 'British', gender: 'Female' },
  { id: 'en-AU-Wavenet-A', name: 'Wavenet A', accent: 'Australian', gender: 'Female' },
  { id: 'en-AU-Wavenet-B', name: 'Wavenet B', accent: 'Australian', gender: 'Male' },
  { id: 'en-IN-Wavenet-A', name: 'Wavenet A', accent: 'Indian', gender: 'Female' },
  { id: 'en-IN-Wavenet-B', name: 'Wavenet B', accent: 'Indian', gender: 'Male' },
];

/**
 * Function to call the backend API for text-to-speech
 * @param {string} text - The text to convert to speech
 * @param {string} voiceId - The voice ID to use for speech synthesis
 * @param {number} speed - The speed of the speech
 * @returns {Promise<ArrayBuffer>} - The audio content as an ArrayBuffer
 */
export const callTextToSpeechAPI = async (text: string, voiceId: string, speed: number): Promise<ArrayBuffer> => {
  try {
    const response = await fetch(getApiUrl('/api/tts'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, voiceId, speed }),
    });

    if (!response.ok) {
      throw new Error(`TTS API error: ${response.status}`);
    }

    return await response.arrayBuffer();
  } catch (error) {
    console.error('Error calling TTS API:', error);
    throw error;
  }
};
