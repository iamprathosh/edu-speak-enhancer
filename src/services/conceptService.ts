import { getApiUrl } from './backendConfig';

// Mock data for concept summarization
export interface SummarizedConcept {
  summary: string;
  keyConcepts: string[];
  learningEnhancement: {
    focusPoints: string[];
    suggestedRelatedTopics: string[];
  };
}

// Compression levels
export type CompressionLevel = 'high' | 'medium' | 'low';

// Sample text about photosynthesis
export const sampleText = `Photosynthesis is the process by which plants, algae, and certain bacteria convert light energy, usually from the sun, into chemical energy in the form of glucose or other sugars. This process occurs in the chloroplasts of plant cells, specifically within structures called thylakoids which contain the pigment chlorophyll. Chlorophyll absorbs light energy, primarily from the blue and red parts of the electromagnetic spectrum, initiating the photosynthetic process.

The overall reaction of photosynthesis can be summarized by the chemical equation: 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂. This indicates that carbon dioxide and water, in the presence of light energy, are converted into glucose and oxygen.

Photosynthesis occurs in two main stages: the light-dependent reactions and the Calvin cycle (or light-independent reactions). The light-dependent reactions take place in the thylakoid membranes of the chloroplasts, where water is split, releasing oxygen and producing ATP (adenosine triphosphate) and NADPH (nicotinamide adenine dinucleotide phosphate). The Calvin cycle takes place in the stroma of the chloroplast, where carbon dioxide is fixed and converted into glucose using the ATP and NADPH produced in the light-dependent reactions.

Photosynthesis is vital for life on Earth as it maintains atmospheric oxygen levels necessary for aerobic organisms, removes carbon dioxide from the atmosphere, and provides the energy stored in chemical bonds that fuels nearly all ecosystems as the foundation of food chains.

Factors affecting the rate of photosynthesis include light intensity, carbon dioxide concentration, temperature, and water availability. Understanding these factors is important in agriculture for optimizing crop yields and in ecology for predicting how changes in environmental conditions might impact ecosystem productivity.`;

// API-based concept summarization
export const summarizeConcept = async (text: string, level: CompressionLevel): Promise<SummarizedConcept> => {
  try {
    const response = await fetch(getApiUrl('/api/summarize_concept'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        level
      }),
      credentials: 'include'
    });

    if (!response.ok) {
      let errorMessage = `API request failed with status ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData && errorData.error) {
          errorMessage = errorData.error;
        }
      } catch (jsonError) {
        // Error response was not JSON or JSON parsing failed.
        // Use statusText if available.
        if (response.statusText) {
            errorMessage = `${errorMessage}: ${response.statusText}`;
        }
      }
      throw new Error(errorMessage);
    }

    const data: SummarizedConcept = await response.json();
    return data;

  } catch (error) {
    console.error('Error summarizing text:', error);
    // Fallback to mock data if API fails, maintaining the original delay behavior
    return new Promise((resolve) => {
      setTimeout(() => {
        let summary: string;
        if (level === 'high') {
          summary = "Photosynthesis converts light energy into chemical energy (glucose) in plants and some microorganisms. The process occurs in chloroplasts, following the equation 6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂. It involves light-dependent reactions (producing ATP, NADPH, and O₂) and the Calvin cycle (producing glucose). Photosynthesis is essential for atmospheric oxygen, the carbon cycle, and food chains.";
        } else if (level === 'medium') {
          summary = "Photosynthesis is the process where plants and certain microorganisms convert light energy into chemical energy as glucose. Occurring in chloroplasts containing chlorophyll, it follows the equation: 6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂. The process has two stages: light-dependent reactions (producing ATP, NADPH, and oxygen) and the Calvin cycle (using ATP and NADPH to convert CO₂ to glucose). Photosynthesis maintains atmospheric oxygen levels, removes CO₂, and forms the base of food chains. Factors affecting its rate include light intensity, CO₂ concentration, temperature, and water availability.";
        } else { // low
          summary = "Photosynthesis is the process by which plants, algae, and certain bacteria convert light energy into chemical energy in the form of glucose. This occurs in chloroplasts containing chlorophyll, which absorbs light energy primarily from blue and red spectrum parts. The chemical equation is 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂. The process has two stages: light-dependent reactions in thylakoid membranes (producing ATP, NADPH, and oxygen) and the Calvin cycle in the stroma (using ATP and NADPH to convert carbon dioxide to glucose). Photosynthesis is crucial for removing CO₂ from the atmosphere, maintaining oxygen levels for aerobic organisms, and providing energy to ecosystems as the base of food chains. Factors affecting photosynthesis rates include light intensity, carbon dioxide concentration, temperature, and water availability, which are important considerations in agriculture and ecology.";
        }
        
        resolve({
          summary,
          keyConcepts: [
            "Photosynthesis converts light energy to chemical energy",
            "Occurs in chloroplasts containing chlorophyll",
            "Equation: 6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂",
            "Two stages: light-dependent reactions and Calvin cycle",
            "Crucial for oxygen production and carbon fixation",
            "Forms the base of most food chains"
          ],
          learningEnhancement: {
            focusPoints: [
              "The core chemical reaction and components",
              "The two-stage process (light-dependent and Calvin cycle)",
              "Ecological importance in oxygen production and as an energy source"
            ],
            suggestedRelatedTopics: [
              "Cellular respiration",
              "Carbon cycle",
              "Plant anatomy",
              "Ecological energy transfer"
            ]
          }
        });
      }, 1500);
    });
  }
};
