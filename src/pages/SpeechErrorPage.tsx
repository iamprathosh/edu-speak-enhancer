import { ArrowLeft, Mic, Play, SkipForward } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Header } from '@/components/Header.tsx';
import { useSpeechError } from '@/hooks/useSpeechError';
import { practiceSentences } from '@/services/speechErrorService';
import { useToast } from '@/hooks/use-toast';
import { LoadingIndicator } from '@/components/ui/loading-indicator';

const SpeechErrorPage = () => {
  const { 
    analysis, 
    selectedWord, 
    isRecording, 
    isProcessing,
    startRecording,
    stopRecording,
    selectWord,
    resetAnalysis
  } = useSpeechError();
  
  const { toast } = useToast();
  
  const playAudio = (word: string, isCorrect: boolean = true) => {
    // In a real implementation, this would play the audio
    // For now, we'll just show a toast
    toast({
      title: isCorrect ? "Correct Pronunciation" : "Your Pronunciation",
      description: `Playing audio for "${word}"`,
    });
  };
  
  const renderSentenceWithHighlights = () => {
    if (!analysis) return "Record your speech to see analysis";
    
    return analysis.sentence.split(' ').map((word, index) => {
      const cleanWord = word.replace(/[.,!?]/g, '');
      const hasError = analysis.errorWords.includes(cleanWord);
      const isSelected = cleanWord === selectedWord;
      
      return (
        <span 
          key={index}
          className={`cursor-pointer ${
            hasError 
              ? 'underline decoration-wavy decoration-red-500 underline-offset-4' 
              : ''
          } ${
            isSelected 
              ? 'bg-edumate-100 text-edumate-700' 
              : ''
          }`}
          onClick={() => hasError ? selectWord(cleanWord) : null}
        >
          {word}{' '}
        </span>
      );
    });
  };
  
  const handlePracticeSentence = (sentence: string) => {
    toast({
      title: "Practice Mode",
      description: "Recording will start in 3 seconds. Read the sentence aloud.",
    });
    
    // In a real implementation, this would start recording after a countdown
    setTimeout(() => {
      startRecording();
    }, 3000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-slate-50">
      <Header />
      <main className="pt-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <Link to="/" className="inline-flex items-center text-edumate-600 hover:text-edumate-700 transition-colors">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Link>
          </div>
          
          <div className="mb-12">
            <h1 className="text-3xl md:text-4xl font-medium text-edumate-900 mb-4">Speech Error Analysis</h1>
            <p className="text-xl text-slate-600 max-w-3xl">
              Detect subtle mispronunciations and receive context-specific corrective suggestions.
            </p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <div className="space-y-8">
              <div className="glass-panel p-8">
                <h3 className="text-xl font-medium text-edumate-900 mb-6">Current Analysis</h3>
                
                <div className="bg-white p-6 rounded-lg border border-slate-100 mb-6">
                  {isRecording ? (
                    <div className="flex flex-col items-center justify-center py-6">
                      <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center mb-3 animate-pulse">
                        <Mic className="w-6 h-6 text-red-500" />
                      </div>
                      <p className="text-edumate-500">Recording your speech...</p>
                    </div>
                  ) : isProcessing ? (
                    <div className="flex flex-col items-center justify-center py-6">
                      <LoadingIndicator size="md" text="Processing your speech..." />
                    </div>
                  ) : (
                    <p className="text-lg text-slate-800 leading-relaxed">
                      {renderSentenceWithHighlights()}
                    </p>
                  )}
                  {analysis && !isProcessing && !isRecording && (
                    <div className="mt-4 text-sm text-slate-500 flex items-center">
                      <Mic className="w-4 h-4 mr-1" /> 
                      Speech sample recorded
                    </div>
                  )}
                </div>
                
                <div className="flex space-x-4">
                  <button 
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={isProcessing}
                    className={`px-4 py-2 ${
                      isRecording 
                        ? 'bg-red-500 hover:bg-red-600' 
                        : 'bg-edumate-500 hover:bg-edumate-600'
                    } text-white rounded-lg transition-colors flex items-center ${
                      isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    <Mic className="w-4 h-4 mr-2" />
                    {isRecording ? 'Stop Recording' : 'Record New'}
                  </button>
                  <button 
                    onClick={resetAnalysis}
                    disabled={!analysis || isRecording || isProcessing}
                    className={`px-4 py-2 border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors flex items-center ${
                      !analysis || isRecording || isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    <SkipForward className="w-4 h-4 mr-2" />
                    Skip to Next
                  </button>
                </div>
              </div>
              
              <div className="glass-panel p-8">
                <h3 className="text-xl font-medium text-edumate-900 mb-4">Practice Sentences</h3>
                <div className="space-y-3">
                  {practiceSentences.slice(0, 3).map((sentence, index) => (
                    <div key={index} className="bg-white p-4 rounded-lg border border-slate-100 hover:border-edumate-200 transition-colors">
                      <p className="text-slate-700">{sentence}</p>
                      <div className="flex items-center justify-between mt-2">
                        <button 
                          onClick={() => playAudio(sentence)}
                          className="flex items-center text-sm text-edumate-500 hover:text-edumate-600 transition-colors"
                        >
                          <Play className="w-4 h-4 mr-1" />
                          Listen
                        </button>
                        <button 
                          onClick={() => handlePracticeSentence(sentence)}
                          className="flex items-center text-sm text-edumate-500 hover:text-edumate-600 transition-colors"
                        >
                          <Mic className="w-4 h-4 mr-1" />
                          Practice
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="glass-panel p-8">
              <h3 className="text-xl font-medium text-edumate-900 mb-6">
                {selectedWord && analysis ? `Correction for "${selectedWord}"` : 'Select a highlighted word for correction'}
              </h3>
              
              {isProcessing ? (
                <div className="flex justify-center py-12">
                  <LoadingIndicator size="lg" text="Analyzing pronunciation..." />
                </div>
              ) : selectedWord && analysis?.errors[selectedWord] ? (
                <div className="space-y-6">
                  <div className="bg-edumate-50 p-6 rounded-lg">
                    <h4 className="text-lg font-medium text-edumate-800 mb-3">Pronunciation Guide</h4>
                    <p className="text-slate-700 mb-4">
                      <span className="font-medium">Correct pronunciation:</span> {analysis.errors[selectedWord].correctPronunciation}
                    </p>
                    <p className="text-slate-700 mb-4">
                      <span className="font-medium">Your pronunciation:</span> {analysis.errors[selectedWord].userPronunciation}
                    </p>
                    <p className="text-slate-700">
                      {analysis.errors[selectedWord].explanation}
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="text-lg font-medium text-edumate-800 mb-3">Listen & Compare</h4>
                    <div className="space-y-3">
                      <div className="bg-white p-4 rounded-lg border border-slate-100">
                        <div className="flex justify-between items-center">
                          <span className="text-slate-700">Correct pronunciation</span>
                          <button 
                            onClick={() => playAudio(selectedWord, true)}
                            className="flex items-center text-edumate-500 hover:text-edumate-600 transition-colors"
                          >
                            <Play className="w-4 h-4 mr-1" />
                            Play
                          </button>
                        </div>
                      </div>
                      <div className="bg-white p-4 rounded-lg border border-slate-100">
                        <div className="flex justify-between items-center">
                          <span className="text-slate-700">Your pronunciation</span>
                          <button 
                            onClick={() => playAudio(selectedWord, false)}
                            className="flex items-center text-edumate-500 hover:text-edumate-600 transition-colors"
                          >
                            <Play className="w-4 h-4 mr-1" />
                            Play
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="text-lg font-medium text-edumate-800 mb-3">Practice</h4>
                    <button 
                      onClick={() => {
                        toast({
                          title: "Practice Word",
                          description: `Say "${selectedWord}" clearly into your microphone.`,
                        });
                        setTimeout(() => startRecording(), 2000);
                      }}
                      disabled={isRecording || isProcessing}
                      className={`w-full py-3 bg-edumate-500 text-white rounded-lg hover:bg-edumate-600 transition-colors flex items-center justify-center ${
                        isRecording || isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                    >
                      <Mic className="w-4 h-4 mr-2" />
                      Practice this word
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="w-16 h-16 rounded-full bg-edumate-100 flex items-center justify-center mb-4">
                    <svg 
                      xmlns="http://www.w3.org/2000/svg" 
                      width="24" 
                      height="24" 
                      viewBox="0 0 24 24" 
                      fill="none" 
                      stroke="currentColor" 
                      strokeWidth="2" 
                      strokeLinecap="round" 
                      strokeLinejoin="round"
                      className="text-edumate-500"
                    >
                      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  </div>
                  <p className="text-slate-600 max-w-xs">
                    {analysis ? 'Click on a highlighted word in the sentence to see detailed pronunciation guidance' : 'Record your speech to start analysis'}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default SpeechErrorPage;
