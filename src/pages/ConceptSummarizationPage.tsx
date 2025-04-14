import { ArrowLeft, FileText, Download, Copy, ChevronsDown, ChevronsUp, BookOpen } from 'lucide-react';
import { Link } from 'react-router-dom';
import Header from '@/components/Header';
import { useConceptSummarization } from '@/hooks/useConceptSummarization';
import { CompressionLevel } from '@/services/conceptService';
import { useToast } from '@/hooks/use-toast';

const ConceptSummarizationPage = () => {
  const { 
    inputText, 
    setInputText,
    summary,
    keyConcepts,
    learningEnhancement,
    compressionLevel,
    isProcessing,
    isGenerated,
    generateSummary,
    changeCompressionLevel
  } = useConceptSummarization();
  
  const { toast } = useToast();
  
  const handleCopy = () => {
    if (summary) {
      navigator.clipboard.writeText(summary);
      toast({
        title: "Copied to Clipboard",
        description: "Summary has been copied to your clipboard."
      });
    }
  };
  
  const handleDownload = () => {
    if (summary) {
      const element = document.createElement("a");
      const file = new Blob([summary], {type: 'text/plain'});
      element.href = URL.createObjectURL(file);
      element.download = "summary.txt";
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      
      toast({
        title: "Download Started",
        description: "Your summary is being downloaded as a text file."
      });
    }
  };
  
  const handleFileUpload = () => {
    // Simulate file selection with a mock action
    toast({
      title: "File Upload",
      description: "Document upload would be processed here in a real implementation."
    });
  };
  
  const summarizeLevels = [
    { key: 'high' as CompressionLevel, label: 'High Compression', icon: <ChevronsUp className="w-4 h-4" /> },
    { key: 'medium' as CompressionLevel, label: 'Medium Compression', icon: null },
    { key: 'low' as CompressionLevel, label: 'Low Compression', icon: <ChevronsDown className="w-4 h-4" /> }
  ];

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
            <h1 className="text-3xl md:text-4xl font-medium text-edumate-900 mb-4">Concept Summarization</h1>
            <p className="text-xl text-slate-600 max-w-3xl">
              Distill lengthy texts into concise, customizable summaries for efficient learning.
            </p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
            <div className="lg:col-span-3 space-y-6">
              <div className="glass-panel p-8">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-medium text-edumate-900">Input Text</h3>
                  <div className="flex space-x-2">
                    <button 
                      onClick={handleFileUpload}
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
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  disabled={isProcessing}
                  className={`w-full p-4 min-h-[300px] rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-edumate-500 text-slate-800 ${
                    isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                  placeholder="Paste your text here for summarization..."
                ></textarea>
                
                <div className="mt-4 flex justify-between items-center">
                  <div className="text-sm text-slate-500">
                    {inputText.length} characters
                  </div>
                  <button
                    onClick={generateSummary}
                    disabled={isProcessing || inputText.trim() === ''}
                    className={`px-4 py-2 rounded-lg font-medium ${
                      isProcessing || inputText.trim() === ''
                        ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                        : 'bg-edumate-500 text-white hover:bg-edumate-600'
                    } transition-colors`}
                  >
                    {isProcessing ? 'Processing...' : 'Summarize'}
                  </button>
                </div>
              </div>
              
              <div className="glass-panel p-8">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-medium text-edumate-900">Summary</h3>
                  <div className="flex space-x-2">
                    <button 
                      onClick={handleCopy}
                      disabled={!isGenerated || isProcessing}
                      className={`p-2 text-slate-600 hover:text-edumate-600 hover:bg-edumate-50 rounded-lg transition-colors ${
                        !isGenerated || isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                      title="Copy summary"
                    >
                      <Copy className="w-5 h-5" />
                    </button>
                    <button 
                      onClick={handleDownload}
                      disabled={!isGenerated || isProcessing}
                      className={`p-2 text-slate-600 hover:text-edumate-600 hover:bg-edumate-50 rounded-lg transition-colors ${
                        !isGenerated || isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                      title="Download summary"
                    >
                      <Download className="w-5 h-5" />
                    </button>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg border border-slate-100 min-h-[200px]">
                  {isProcessing ? (
                    <div className="flex items-center justify-center h-[188px]">
                      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-edumate-500"></div>
                    </div>
                  ) : isGenerated ? (
                    <p className="text-slate-800 leading-relaxed">
                      {summary}
                    </p>
                  ) : (
                    <div className="text-slate-400 flex flex-col items-center justify-center h-[188px] text-center">
                      <FileText className="w-8 h-8 mb-3 text-slate-300" />
                      <p>Click "Summarize" to generate a summary</p>
                    </div>
                  )}
                </div>
                
                <div className="mt-6">
                  <h4 className="text-lg font-medium text-edumate-900 mb-3">Summarization Level</h4>
                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
                    {summarizeLevels.map(level => (
                      <button
                        key={level.key}
                        onClick={() => changeCompressionLevel(level.key)}
                        disabled={isProcessing}
                        className={`px-4 py-2 rounded-lg flex items-center justify-center transition-colors ${
                          isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                        } ${
                          compressionLevel === level.key
                            ? 'bg-edumate-100 text-edumate-700 border border-edumate-200'
                            : 'bg-white text-slate-600 border border-slate-200 hover:border-edumate-200'
                        }`}
                      >
                        {level.icon && <span className="mr-1">{level.icon}</span>}
                        {level.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="lg:col-span-2">
              <div className="sticky top-24 space-y-6">
                <div className="glass-panel p-8">
                  <h3 className="text-xl font-medium text-edumate-900 mb-6">Key Concepts</h3>
                  
                  {isProcessing ? (
                    <div className="py-8 flex justify-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-edumate-500"></div>
                    </div>
                  ) : isGenerated ? (
                    <div className="space-y-3">
                      {keyConcepts.map((concept, index) => (
                        <div key={index} className="flex items-start">
                          <div className="flex-shrink-0 h-6 w-6 rounded-full bg-edumate-100 flex items-center justify-center mr-3 mt-0.5">
                            <span className="text-edumate-600 text-xs font-medium">{index + 1}</span>
                          </div>
                          <p className="text-slate-700">{concept}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-400">
                      <p>Generate a summary to see key concepts</p>
                    </div>
                  )}
                </div>
                
                {isGenerated && (
                  <div className="bg-edumate-50 rounded-lg p-6 border border-edumate-100">
                    <div className="flex items-center text-edumate-800 mb-4">
                      <BookOpen className="w-5 h-5 mr-2" />
                      <h3 className="text-lg font-medium">Learning Enhancement</h3>
                    </div>
                    
                    <div className="space-y-4">
                      <p className="text-slate-700 text-sm">
                        Your summary focuses on the fundamental aspects, highlighting:
                      </p>
                      <ul className="space-y-2 text-sm">
                        {learningEnhancement.focusPoints.map((point, index) => (
                          <li key={index} className="flex items-start">
                            <span className="flex-shrink-0 h-5 w-5 text-edumate-600 mr-2">•</span>
                            <span className="text-slate-700">{point}</span>
                          </li>
                        ))}
                      </ul>
                      
                      {learningEnhancement.suggestedRelatedTopics.length > 0 && (
                        <>
                          <p className="text-slate-700 text-sm font-medium mt-2">
                            Suggested related topics:
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {learningEnhancement.suggestedRelatedTopics.map((topic, index) => (
                              <span 
                                key={index}
                                className="bg-white px-3 py-1 rounded-full text-xs text-edumate-700 border border-edumate-200"
                              >
                                {topic}
                              </span>
                            ))}
                          </div>
                        </>
                      )}
                      
                      <p className="text-slate-700 text-sm">
                        Try adjusting the summarization level to focus on different aspects based on your learning needs.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ConceptSummarizationPage;
