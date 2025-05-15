import { getApiUrl } from './backendConfig';
import { getGoogleTTSAudio } from './speechService'; // Import actual TTS function

// Mock data for speech error analysis
interface SpeechError {
  word: string;
  correctPronunciation: string;
  userPronunciation: string;
  explanation: string;
}

interface SpeechErrorAnalysis {
  sentence: string;
  errorWords: string[];
  errors: Record<string, SpeechError>;
}

// Mock practice sentences
export const practiceSentences = [
  "She recognized the symptoms of the illness immediately.",
  "The necessary documents were signed and delivered yesterday.",
  "The temperature fluctuated throughout the week.",
  "The beautiful mountain range was visible from the kitchen window.",
  "I particularly enjoyed the exhibition at the museum."
];

// Simulate processing speech with errors
export const analyzeErrors = async (recordingBlob: Blob): Promise<SpeechErrorAnalysis> => {
  const formData = new FormData();
  formData.append('audio', recordingBlob);

  const response = await fetch(getApiUrl('/api/speech-error-analysis'), {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Speech error analysis API error: ${response.status}`);
  }

  return await response.json();
};

// Fetches text-to-speech audio for the correct pronunciation of a word
export const getCorrectPronunciationAudio = async (word: string): Promise<Blob | null> => {
  if (!word) return null;
  try {
    // Using a default voice and speed. These could be made configurable if needed.
    const audioBlob = await getGoogleTTSAudio(word, 'en-US-Wavenet-A', 1.0);
    return audioBlob;
  } catch (error) {
    console.error(`Error fetching TTS audio for "${word}":`, error);
    // Depending on desired error handling, you might want to throw the error
    // or return null to be handled by the caller.
    return null;
  }
};
