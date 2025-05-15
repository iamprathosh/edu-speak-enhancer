import { ArrowLeft, FileText, Camera, CheckCircle, XCircle, Copy } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Header } from '@/components/Header.tsx';
import { useGrammarCheck } from '@/hooks/useGrammarCheck';
import { useToast } from '@/hooks/use-toast';
import { LoadingIndicator } from '@/components/ui/loading-indicator';

const GrammarCheckPage = () => {
  const { 
    textInput, 
    setTextInput, 
    corrections, 
    isAnalyzed, 
    isProcessing,
    analyzeText,
    uploadImage,
    correctedText
  } = useGrammarCheck();
  
  const { toast } = useToast();
  
  const handleImageUpload = () => {
    // Simulate file selection with a mock file
    const mockFile = new File([""], "sample-image.jpg", { type: "image/jpeg" });
    uploadImage(mockFile);
  };
  
  const handleCopyText = () => {
    if (isAnalyzed) {
      navigator.clipboard.writeText(correctedText());
      toast({
        title: "Copied to Clipboard",
        description: "Corrected text has been copied to your clipboard."
      });
    }
  };
  
  const renderCorrectedText = () => {
    if (!isAnalyzed) return null;
    
    let text = textInput;
    
    // Apply corrections in reverse order to avoid messing up indices
    [...corrections].reverse().forEach(correction => {
      const index = text.toLowerCase().indexOf(correction.original.toLowerCase());
      if (index !== -1) {
        const beforeText = text.substring(0, index);
        const afterText = text.substring(index + correction.original.length);
        
        // Only highlight if it's actually corrected (original and corrected are different)
        if (correction.original.toLowerCase() !== correction.corrected.toLowerCase()) {
          text = beforeText + `<span class="text-green-600 font-medium">${correction.corrected}</span>` + afterText;
        }
      }
    });
    
    return (
      <div 
        className="text-slate-800"
        dangerouslySetInnerHTML={{ __html: text }}
      />
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-slate-50">
      <Header />
      <main className="pt-24 px-6 pb-16">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <Link to="/" className="inline-flex items-center text-edumate-600 hover:text-edumate-700 transition-colors">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Link>
          </div>
          
          <div className="mb-12">
            <h1 className="text-3xl md:text-4xl font-medium text-edumate-900 mb-4">Grammar Check</h1>
            <p className="text-xl text-slate-600 max-w-3xl">
              Convert handwritten notes to text and receive detailed grammatical corrections and improvements.
            </p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
            <div className="lg:col-span-3 space-y-6">
              <div className="glass-panel p-8">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-medium text-edumate-900">Input Text</h3>
                  <div className="flex space-x-2">
                    <button 
                      onClick={handleImageUpload}
                      disabled={isProcessing}
                      className={`p-2 text-slate-600 hover:text-edumate-600 hover:bg-edumate-50 rounded-lg transition-colors ${
                        isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                      title="Upload image with text"
                    >
                      <Camera className="w-5 h-5" />
                    </button>
                    <button 
                      disabled={isProcessing}
                      className={`p-2 text-slate-600 hover:text-edumate-600 hover:bg-edumate-50 rounded-lg transition-colors ${
                        isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                      title="Upload document"
                    >
                      <FileText className="w-5 h-5" />
                    </button>
                  </div>
                </div>
                
                <textarea
                  value={textInput}
                  onChange={(e) => {
                    setTextInput(e.target.value);
                  }}
                  disabled={isProcessing}
                  className={`w-full p-4 min-h-[200px] rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-edumate-500 text-slate-800 ${
                    isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                  placeholder="Type or paste your text here for grammar analysis..."
                ></textarea>
                
                <div className="mt-4 flex justify-between items-center">
                  <div className="text-sm text-slate-500">
                    {textInput.length} characters
                  </div>
                  <button
                    onClick={analyzeText}
                    disabled={isProcessing || textInput.trim() === ''}
                    className={`px-4 py-2 rounded-lg font-medium ${
                      isProcessing || textInput.trim() === ''
                        ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                        : 'bg-edumate-500 text-white hover:bg-edumate-600'
                    } transition-colors`}
                  >
                    {isProcessing ? 'Processing...' : 'Analyze Text'}
                  </button>
                </div>
              </div>
              
              <div className="glass-panel p-8">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-medium text-edumate-900">Corrected Text</h3>
                  <button 
                    onClick={handleCopyText}
                    disabled={!isAnalyzed || isProcessing}
                    className={`p-2 text-slate-600 hover:text-edumate-600 hover:bg-edumate-50 rounded-lg transition-colors ${
                      !isAnalyzed || isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                    }`} 
                    title="Copy corrected text"
                  >
                    <Copy className="w-5 h-5" />
                  </button>
                </div>
                
                <div className="bg-white p-6 rounded-lg border border-slate-100 min-h-[200px]">
                  {isProcessing ? (
                    <div className="flex items-center justify-center h-[168px]">
                      <LoadingIndicator size="lg" text="Analyzing your text..." />
                    </div>
                  ) : isAnalyzed ? (
                    renderCorrectedText()
                  ) : (
                    <div className="text-slate-400 flex flex-col items-center justify-center h-[168px] text-center">
                      <FileText className="w-8 h-8 mb-3 text-slate-300" />
                      <p>Click "Analyze Text" to see grammar corrections</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            <div className="lg:col-span-2">
              <div className="sticky top-24 space-y-6">
                <div className="glass-panel p-8">
                  <h3 className="text-xl font-medium text-edumate-900 mb-6">Grammar Issues</h3>
                  
                  {isProcessing ? (
                    <div className="flex items-center justify-center py-12">
                      <LoadingIndicator size="md" />
                    </div>
                  ) : isAnalyzed ? (
                    <div className="space-y-4">
                      {corrections.map((correction, index) => (
                        <div key={index} className="bg-white p-4 rounded-lg border border-slate-100">
                          <div className="flex items-start space-x-2 mb-2">
                            <div className="flex-shrink-0 mt-0.5">
                              {correction.original.toLowerCase() !== correction.corrected.toLowerCase() ? (
                                <XCircle className="w-5 h-5 text-red-500" />
                              ) : (
                                <CheckCircle className="w-5 h-5 text-yellow-500" />
                              )}
                            </div>
                            <div>
                              <p className={`font-medium ${
                                correction.original.toLowerCase() !== correction.corrected.toLowerCase()
                                  ? 'text-red-700'
                                  : 'text-yellow-700'
                              }`}>
                                {correction.original.toLowerCase() !== correction.corrected.toLowerCase()
                                  ? 'Error'
                                  : 'Suggestion'}
                              </p>
                              <p className="text-slate-700">
                                {correction.original.toLowerCase() !== correction.corrected.toLowerCase() 
                                  ? <><span className="line-through">{correction.original}</span> → <span className="text-green-600 font-medium">{correction.corrected}</span></>
                                  : <>{correction.original}</>
                                }
                              </p>
                            </div>
                          </div>
                          <p className="text-sm text-slate-600 pl-7">
                            {correction.explanation}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-400">
                      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
                        <FileText className="w-6 h-6" />
                      </div>
                      <p>Analyze your text to see grammar issues</p>
                    </div>
                  )}
                </div>
                
                <div className="bg-edumate-50 rounded-lg p-6 border border-edumate-100">
                  <h3 className="text-lg font-medium text-edumate-800 mb-3">Tips for Better Writing</h3>
                  <ul className="space-y-2">
                    <li className="flex items-start">
                      <span className="flex-shrink-0 h-5 w-5 rounded-full bg-edumate-200 flex items-center justify-center mr-2 mt-0.5">
                        <span className="text-edumate-600 text-xs">1</span>
                      </span>
                      <span className="text-slate-700 text-sm">Be consistent with tense throughout your writing</span>
                    </li>
                    <li className="flex items-start">
                      <span className="flex-shrink-0 h-5 w-5 rounded-full bg-edumate-200 flex items-center justify-center mr-2 mt-0.5">
                        <span className="text-edumate-600 text-xs">2</span>
                      </span>
                      <span className="text-slate-700 text-sm">Use active voice for clearer, more direct communication</span>
                    </li>
                    <li className="flex items-start">
                      <span className="flex-shrink-0 h-5 w-5 rounded-full bg-edumate-200 flex items-center justify-center mr-2 mt-0.5">
                        <span className="text-edumate-600 text-xs">3</span>
                      </span>
                      <span className="text-slate-700 text-sm">Avoid unnecessary jargon and complex vocabulary</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default GrammarCheckPage;
