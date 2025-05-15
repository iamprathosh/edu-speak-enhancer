import { useState, useRef } from 'react';
import { analyzeErrors } from '@/services/speechErrorService';
import { useToast } from '@/hooks/use-toast';

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

export const useSpeechError = () => {
  const [analysis, setAnalysis] = useState<SpeechErrorAnalysis | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [currentStream, setCurrentStream] = useState<MediaStream | null>(null);
  const { toast } = useToast();
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setCurrentStream(stream);
      setIsRecording(true);
      audioChunksRef.current = []; // Clear previous chunks

      // Determine a supported MIME type
      const mimeTypes = [
        'audio/webm; codecs=opus',
        'audio/ogg; codecs=opus',
        'audio/wav',
        'audio/webm',
      ];
      const supportedMimeType = mimeTypes.find(type => MediaRecorder.isTypeSupported(type));

      if (!supportedMimeType) {
        toast({
          title: "Recording Error",
          description: "No supported audio format found for recording.",
          variant: "destructive"
        });
        setIsRecording(false);
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
          setCurrentStream(null);
        }
        return;
      }
      
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: supportedMimeType });
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        if (audioChunksRef.current.length > 0) {
          const audioBlob = new Blob(audioChunksRef.current, { type: supportedMimeType });
          processRecording(audioBlob);
          audioChunksRef.current = []; // Clear chunks after processing
        } else {
          toast({
            title: "Recording Error",
            description: "No audio data was recorded. Please try again.",
            variant: "destructive"
          });
          setIsProcessing(false); // Ensure processing is set to false
        }
        // Stop stream tracks after recording is fully processed
        if (currentStream) {
          currentStream.getTracks().forEach(track => track.stop());
          setCurrentStream(null);
        }
      };
      
      mediaRecorderRef.current.start();
      
      toast({
        title: "Recording Started",
        description: "Speak the sentence clearly into your microphone. Recording will stop automatically.",
      });
      
      // For demo purposes, automatically stop after 5 seconds
      // In a real app, you might have a manual stop button
      setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
          mediaRecorderRef.current.stop();
        }
      }, 5000); // Stop recording after 5 seconds
      
    } catch (error) {
      console.error("Error starting recording:", error);
      toast({
        title: "Microphone Access Denied",
        description: "Please allow microphone access to use this feature. If you've already allowed it, try checking your system's microphone settings.",
        variant: "destructive"
      });
      setIsRecording(false); // Ensure recording state is reset
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop(); // This will trigger 'onstop'
    }
    // Stream tracks are now stopped in mediaRecorder.onstop
    setIsRecording(false);
    setIsProcessing(true); // Set processing true, will be set to false in processRecording
  };

  const processRecording = async (audioBlob: Blob) => {
    try {
      const result = await analyzeErrors(audioBlob);
      setAnalysis(result);
      
      // Default select first error word
      if (result.errorWords.length > 0) {
        setSelectedWord(result.errorWords[0]);
      }
      
    } catch (error) {
      toast({
        title: "Analysis Failed",
        description: "Could not analyze your speech. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsProcessing(false);
    }
  };
  
  const selectWord = (word: string) => {
    setSelectedWord(word);
  };
  
  const resetAnalysis = () => {
    setAnalysis(null);
    setSelectedWord(null);
  };
  
  return {
    analysis,
    selectedWord,
    isRecording,
    isProcessing,
    startRecording,
    stopRecording: handleStopRecording,
    selectWord,
    resetAnalysis
  };
};
