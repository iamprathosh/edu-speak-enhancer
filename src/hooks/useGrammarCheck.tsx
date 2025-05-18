import { useState } from 'react';
import { checkGrammar, processImage, GrammarCorrection } from '@/services/grammarService';
import { useToast } from '@/hooks/use-toast';

export const useGrammarCheck = () => {
  const [textInput, setTextInput] = useState("I have recieved your letter last week and I will response as soon as possible. Me and my team are working hardly on this project.");
  const [corrections, setCorrections] = useState<GrammarCorrection[]>([]);
  const [isAnalyzed, setIsAnalyzed] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const { toast } = useToast();
  
  const analyzeText = async () => {
    if (textInput.trim() === '') {
      toast({
        title: "Empty Text",
        description: "Please enter some text to analyze.",
        variant: "destructive"
      });
      return;
    }
    
    setIsProcessing(true);
    
    try {
      const result = await checkGrammar(textInput);
      setCorrections(result);
      setIsAnalyzed(true);
      
      toast({
        title: "Analysis Complete",
        description: `Found ${result.length} grammar issue${result.length === 1 ? '' : 's'}.`,
      });
    } catch (error) {
      toast({
        title: "Analysis Failed",
        description: "Could not analyze your text. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsProcessing(false);
    }
  };
  
  const uploadImage = async (file: File) => {
    setIsProcessing(true);
    
    try {
      const extractedText = await processImage(file);
      setTextInput(extractedText);
      setIsAnalyzed(false);
      
      toast({
        title: "Image Processed",
        description: "Text has been extracted from your image.",
      });
      
      // Auto-analyze the extracted text
      const result = await checkGrammar(extractedText);
      setCorrections(result);
      setIsAnalyzed(true);
    } catch (error) {
      toast({
        title: "Processing Failed",
        description: "Could not extract text from your image. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsProcessing(false);
    }
  };
  
  const resetAnalysis = () => {
    setIsAnalyzed(false);
    setCorrections([]);
  };
  
  const correctedText = (): string => {
    let text = textInput;
    
    // Apply corrections
    corrections.forEach(correction => {
      if (correction.original.toLowerCase() !== correction.corrected.toLowerCase()) {
        text = text.replace(
          new RegExp(correction.original, 'gi'), 
          correction.corrected
        );
      }
    });
    
    return text;
  };
  
  return {
    textInput,
    setTextInput,
    corrections,
    isAnalyzed,
    isProcessing,
    analyzeText,
    uploadImage,
    resetAnalysis,
    correctedText
  };
};
