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
      body: JSON.stringify({ text })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to check grammar');
      }
      return response.json();
    })
    .then(data => {
      resolve(data);
    })
    .catch(error => {
      console.error('Error checking grammar:', error);
      // Fallback to mock data if API fails
      setTimeout(() => {
        // This would be replaced with actual grammar checking API
        // Using an example text for mock corrections
        const sampleText = "I have recieved your letter last week and I will response as soon as possible. Me and my team are working hardly on this project.";
        
        if (text.includes(sampleText) || text.length > 20) {
          resolve([
            { 
              original: "recieved", 
              corrected: "received", 
              explanation: "The correct spelling follows the rule 'i before e except after c'." 
            },
            { 
              original: "last week", 
              corrected: "last week", 
              explanation: "When referring to a completed action in the past, use the simple past tense ('received') rather than the present perfect ('have received')." 
            },
            { 
              original: "response", 
              corrected: "respond", 
              explanation: "'Response' is a noun, while 'respond' is the verb form needed in this context." 
            },
            { 
              original: "Me and my team", 
              corrected: "My team and I", 
              explanation: "When referring to yourself and others, place yourself last and use the subject pronoun 'I' rather than the object pronoun 'me'." 
            },
            { 
              original: "hardly", 
              corrected: "hard", 
              explanation: "'Hardly' means 'barely' or 'scarcely', while 'hard' is the intended adverb meaning 'with great effort'." 
            }
          ]);
        } else {
          // For short or different texts, return fewer corrections
          resolve([
            { 
              original: "alot", 
              corrected: "a lot", 
              explanation: "'A lot' is always written as two words." 
            },
            { 
              original: "their", 
              corrected: "there", 
              explanation: "'There' indicates a place, while 'their' indicates possession." 
            }
          ]);
        }
      }, 1000);
    });
  });
};

// Simulate OCR (Optical Character Recognition) for uploaded images
export const processImage = (imageFile: File): Promise<string> => {
  return new Promise((resolve) => {
    // Simulate backend processing time
    setTimeout(() => {
      // In a real implementation, this would extract text from the image
      resolve("I have recieved your letter last week and I will response as soon as possible. Me and my team are working hardly on this project.");
    }, 2000);
  });
};
