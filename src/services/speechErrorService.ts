import { getApiUrl } from './backendConfig';

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

// Simulate text-to-speech functionality for correct pronunciation
export const getErrorAudio = (word: string, isCorrect: boolean): string => {
  // In a real implementation, this would generate or fetch audio files
  // For now, we'll just return a mock URL
  return `https://api.example.com/tts?text=${encodeURIComponent(word)}&isCorrect=${isCorrect}`;
};
