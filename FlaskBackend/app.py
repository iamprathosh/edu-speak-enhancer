import nltk
import os
import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from google.cloud import texttospeech
from google.api_core import exceptions
import io
from dotenv import load_dotenv
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.probability import FreqDist
from nltk.chunk import RegexpParser  # For improved phrase extraction
from heapq import nlargest
import string
import re
from collections import Counter
import traceback
import google.generativeai as genai
import json
from flask_limiter import Limiter  # For rate limiting
from flask_limiter.util import get_remote_address

# --- Configuration and Initialization (Same as previous, with additions) ---

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],  # Example limits
    storage_uri="memory://",  # Use in-memory storage; consider Redis for production
)

# Initialize Gemini API (Prioritize)
gemini_available = False
gemini_model = None
if "GEMINI_API_KEY" in os.environ:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    try:
        gemini_model = genai.GenerativeModel('gemini-pro')
        gemini_available = True
        logger.info("Gemini API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API: {str(e)}")
        # Don't exit; allow fallback to NLTK
else:
    logger.warning("GEMINI_API_KEY environment variable not set!")
    logger.warning("Using NLTK fallback for summarization and concept extraction.")


# Initialize Google Cloud TTS
try:
    client = texttospeech.TextToSpeechClient()
    logger.info("Google Cloud TTS client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Google Cloud TTS client: {str(e)}")
    client = None  # Ensure client is None if initialization fails


def download_nltk_resources():
    try:
        nltk.data.find('tokenizers/punkt')
        logger.info("NLTK punkt tokenizer already downloaded")
    except LookupError:
        logger.info("Downloading NLTK punkt tokenizer")
        nltk.download('punkt', quiet=True)

    try:
        nltk.data.find('corpora/stopwords')
        logger.info("NLTK stopwords already downloaded")
    except LookupError:
        logger.info("Downloading NLTK stopwords")
        nltk.download('stopwords', quiet=True)
    try:  # Download POS tagger
        nltk.data.find('taggers/averaged_perceptron_tagger')
        logger.info("NLTK averaged_perceptron_tagger already downloaded")
    except LookupError:
        logger.info("Downloading NLTK averaged_perceptron_tagger")
        nltk.download('averaged_perceptron_tagger', quiet=True)


download_nltk_resources()

# --- Error Handling ---

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}")
    logger.error(traceback.format_exc())
    return jsonify({
        'error': 'An unexpected error occurred',
        'message': str(e)
    }), 500


# --- API Endpoints ---

@app.route('/api/tts', methods=['POST'])
@limiter.limit("10 per minute")  # Apply rate limiting
def text_to_speech():
     if client is None:
        logger.error("Google Cloud TTS client not initialized")
        return jsonify({'error': 'Text-to-speech service unavailable'}), 503

     try:
        data = request.get_json()

        if not data:
            logger.warning("No JSON data received in request")
            return jsonify({'error': 'Invalid request: No JSON data'}), 400

        if 'text' not in data or not data['text'].strip():
            logger.warning("Missing or empty 'text' field in request")
            return jsonify({'error': 'Text is required'}), 400

        text = data.get('text', '').strip()
        voice_id = data.get('voiceId', 'en-US-Standard-D')  # Default

        try:
            speed = float(data.get('speed', 1.0))
            if speed < 0.25 or speed > 4.0:
                logger.warning(f"Speed value out of range: {speed}")
                return jsonify({'error': 'Speed must be between 0.25 and 4.0'}), 400
        except (TypeError, ValueError) as e:
            logger.warning(f"Invalid speed value: {data.get('speed')}")
            return jsonify({'error': 'Speed must be a valid number'}), 400

        try:
            language_code = '-'.join(voice_id.split('-')[:2])
            if not language_code or len(language_code.split('-')) != 2:
                raise ValueError("Invalid voice ID format")
        except Exception:
            logger.warning(f"Invalid voice ID format: {voice_id}")
            return jsonify({'error': 'Invalid voice ID format'}), 400
        logger.info(f"Processing TTS request: language={language_code}, voice={voice_id}, speed={speed}")
        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_id
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speed
        )

        try:
            logger.info("Calling Google TTS API")
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            logger.info("Successfully received TTS response")

            if not response.audio_content:
                logger.error("No audio content in Google TTS response")
                return jsonify({'error': 'No audio generated'}), 500

            audio_buffer = io.BytesIO(response.audio_content)
            audio_buffer.seek(0)

            logger.info("Sending audio file response")
            return send_file(
                audio_buffer,
                mimetype="audio/mpeg",
                as_attachment=True,
                download_name="speech.mp3"
            )

        except exceptions.GoogleAPICallError as e:
            logger.error(f"Google API call error: {str(e)}")
            return jsonify({'error': f'Text-to-speech API error: {str(e)}'}), 500

     except Exception as e:
        logger.error(f"Error in text_to_speech: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/voices', methods=['GET'])
def get_voices():
    if client is None:
        logger.error("Google Cloud TTS client not initialized")
        return jsonify({'error': 'Voice service unavailable'}), 503
    
    try:
        logger.info("Retrieving available voices from Google TTS API")
        try:
            response = client.list_voices()
        except exceptions.GoogleAPICallError as e:
            logger.error(f"Google API call error: {str(e)}")
            return jsonify({'error': f'Failed to retrieve voices: {str(e)}'}), 500
        
        voices = []
        for voice in response.voices:
            if any(lang_code.startswith('en-') for lang_code in voice.language_codes):
                if voice.ssml_gender == texttospeech.SsmlVoiceGender.MALE:
                    gender = "Male"
                elif voice.ssml_gender == texttospeech.SsmlVoiceGender.FEMALE:
                    gender = "Female"
                else:
                    gender = "Neutral"
                
                language_code = voice.language_codes[0]
                if language_code == "en-US":
                    accent = "American"
                elif language_code == "en-GB":
                    accent = "British"
                elif language_code == "en-AU":
                    accent = "Australian"
                elif language_code == "en-IN":
                    accent = "Indian"
                else:
                    accent = language_code
                
                voices.append({
                    "id": voice.name,
                    "name": voice.name.split('-')[-1],
                    "accent": accent,
                    "gender": gender,
                    "language": language_code
                })
        
        if not voices:
            logger.warning("No English voices found in API response")
            return jsonify({'warning': 'No English voices available', 'voices': []}), 200
            
        logger.info(f"Successfully retrieved {len(voices)} voices")
        return jsonify(voices)
        
    except Exception as e:
        logger.error(f"Error in get_voices: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/summarize', methods=['POST'])
@limiter.limit("10 per minute")  # Apply rate limiting
def summarize_concept():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request: No JSON data'}), 400
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        level = data.get('level', 'medium')
        if level not in ['high', 'medium', 'low']:
            return jsonify({'error': 'Invalid compression level'}), 400
        if len(text) < 50:
             return jsonify({'error': 'Text too short. Minimum 50 characters required.'}), 400

        # --- Prioritize Gemini ---
        if gemini_available:
            try:
                summary, key_concepts, focus_points, related_topics = generate_concepts_with_gemini(text, level)  # Pass level
                logger.info("Successfully generated summary and concepts with Gemini")
                return jsonify({
                    "summary": summary,
                    "keyConcepts": key_concepts,
                    "learningEnhancement": {
                        "focusPoints": focus_points,
                        "suggestedRelatedTopics": related_topics
                    }
                })
            except Exception as e:
                logger.error(f"Error with Gemini API: {str(e)}. Falling back to NLTK.")
                # Fallback to NLTK is handled below

        # --- NLTK Fallback ---
        logger.info("Using NLTK for summarization and concept extraction")
        summary = generate_summary(text, level)
        key_concepts = extract_key_concepts(text)
        focus_points = generate_focus_points(text, key_concepts)
        related_topics = generate_related_topics(text, key_concepts)
        return jsonify({
            "summary": summary,
            "keyConcepts": key_concepts,
            "learningEnhancement": {
                "focusPoints": focus_points,
                "suggestedRelatedTopics": related_topics
            }
        })

    except Exception as e:
        logger.error(f"Error in summarize_concept: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500


# --- Helper Functions ---

def generate_concepts_with_gemini(text, level):
    """Use Gemini API for summarization, key concepts, and learning enhancement.
        Now includes summarization and handles level.
    """
    try:
        # --- Construct the prompt ---
        prompt = f"""
        Please analyze this text and provide:
        1. A summary of the text.  The summary should be concise but comprehensive.
           - If the 'level' is 'high', aim for a very short summary (1-2 sentences).
           - If the 'level' is 'medium', aim for a moderate-length summary (3-4 sentences).
           - If the 'level' is 'low', you can provide a more detailed summary (5-7 sentences).
        2. 6 key concepts as brief phrases (2-5 words each).
        3. 3 learning focus points (1 sentence each).
        4. 4 related topics that would complement this knowledge (short phrases).

        Format your response as JSON with these exact keys:
        "summary", "keyConcepts", "focusPoints", "relatedTopics"

        Compression Level: {level}

        Text to analyze:
        {text}
        """

        response = gemini_model.generate_content(prompt)

        # --- Parse the response (with robust error handling) ---
        try:
            result_text = response.text
            if '{' in result_text and '}' in result_text:
                json_str = result_text[result_text.find('{'):result_text.rfind('}') + 1]
                result = json.loads(json_str)

                summary = result.get("summary", "Could not generate summary.")  # Provide default
                key_concepts = result.get("keyConcepts", [])[:6]
                focus_points = result.get("focusPoints", [])[:3]
                related_topics = result.get("relatedTopics", [])[:4]

                return summary, key_concepts, focus_points, related_topics

        except Exception as json_error:
            logger.warning(f"Failed to parse JSON from Gemini: {str(json_error)}")
            # Attempt fallback extraction (as in previous version)
            #  ... (Code from previous version's fallback here) ...
            content = response.text
            sections = content.split('\n\n')
            key_concepts = []
            focus_points = []
            related_topics = []
            summary = None

            for section in sections:
                section_lower = section.lower()
                if "summary" in section_lower:
                    if summary is None:
                        summary = section.replace("Summary:", "").strip()
                if "key concept" in section_lower:
                    lines = section.split('\n')
                    key_concepts.extend([line.split(':', 1)[-1].split('-', 1)[-1].split('•', 1)[-1].strip() for line in lines if ':' in line or '-' in line or '•' in line])
                elif "focus point" in section_lower or "learning point" in section_lower:
                    lines = section.split('\n')
                    focus_points.extend([line.split(':', 1)[-1].split('-', 1)[-1].split('•', 1)[-1].strip() for line in lines if ':' in line or '-' in line or '•' in line])
                elif "related topic" in section_lower:
                    lines = section.split('\n')
                    related_topics.extend([line.split(':', 1)[-1].split('-', 1)[-1].split('•', 1)[-1].strip() for line in lines if ':' in line or '-' in line or '•' in line])

            key_concepts = key_concepts[:6]
            focus_points = focus_points[:3]
            related_topics = related_topics[:4]

            if summary is None:
                summary = "Could not generate summary."

            if not key_concepts:
                key_concepts = ["No key concepts identified."] * 6
            if not focus_points:
                focus_points = ["No focus points identified."] * 3
            if not related_topics:
                related_topics = ["No related topics identified"] * 4

            return summary, key_concepts, focus_points, related_topics


    except Exception as e:
        logger.error(f"Error in generate_concepts_with_gemini: {str(e)}")
        raise  # Re-raise to trigger NLTK fallback


def generate_summary(text, level):
    """NLTK-based text summarization (same as before, but used as fallback)."""
    try:
        sentences = sent_tokenize(text)
        if not sentences:
            logger.warning("No sentences found in text")
            return "No content to summarize."

        words = word_tokenize(text.lower())
        stop_words = set(stopwords.words('english'))
        words = [word for word in words if word is not None and word.isalnum() and word not in stop_words]
        if not words:
             logger.warning("No significant words found after filtering")
             return "Content lacks significant terms for summarization."

        word_freq = FreqDist(words)

        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            sentence_words = word_tokenize(sentence.lower())
            sentence_words = [word for word in sentence_words if word isalnum() and word not in stop_words]
            if len(sentence_words) == 0:
                continue

            score = sum(word_freq[word] for word in sentence_words) / len(sentence_words)
            sentence_scores[i] = score
        if not sentence_scores:
             logger.warning("No sentences could be scored")
             return "Unable to generate a meaningful summary."
        if level == 'high':
            num_sentences = max(1, int(len(sentences) * 0.2))
        elif level == 'medium':
            num_sentences = max(2, int(len(sentences) * 0.4))
        else:  # low
            num_sentences = max(3, int(len(sentences) * 0.6))

        summary_indices = nlargest(num_sentences, sentence_scores, key=sentence_scores.get)

        if not summary_indices:
            logger.warning("Failed to select top sentences")
            return "Summary generation failed."
        summary_indices.sort()
        summary = ' '.join([sentences[i] for i in summary_indices])
        return summary
    except Exception as e:
        logger.error(f"Error in generate_summary: {str(e)}")
        return "Error generating summary."


def extract_key_concepts(text, num_concepts=6):
    """NLTK-based key concept extraction (Improved with POS tagging)."""
    try:
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalnum() and word not in stop_words]

        if not words:
            logger.warning("No significant words found for concept extraction")
            return ["No key concepts identified"]

        # Use POS tagging to identify noun phrases
        tagged_words = nltk.pos_tag(words)
        # Define a grammar for noun phrases (NP)
        grammar = r"""
            NP: {<DT>?<JJ>*<NN.*>+}   # Chunk sequences of DT, JJ, NN
                {<NNP>+}            # Chunk sequences of proper nouns
        """
        cp = RegexpParser(grammar)
        tree = cp.parse(tagged_words)

        noun_phrases = []
        for subtree in tree.subtrees():
            if subtree.label() == 'NP':
                phrase = ' '.join(word for word, pos in subtree.leaves())
                if len(phrase.split()) >= 2:  # Consider only phrases with 2+ words
                    noun_phrases.append(phrase)

        # Remove duplicates and get top phrases
        unique_phrases = list(set(noun_phrases))

        if not unique_phrases:
            logger.warning("No phrases extracted")
            return ["No key concepts identified"]
        return unique_phrases[:num_concepts] if len(unique_phrases) >= num_concepts else unique_phrases

    except Exception as e:
        logger.error(f"Error in extract_key_concepts: {str(e)}")
        return ["Error extracting key concepts"]

def extract_phrase_around_word(sentence, word):
    """Extract a meaningful phrase around the target word"""
    try:
        words = sentence.split()
        word_pos = None

        # Find position of word (case-insensitive)
        for i, w in enumerate(words):
            if word in w.lower():
                word_pos = i
                break

        if word_pos is None:
            return None

        # Extract 3-5 words around the target word
        start = max(0, word_pos - 2)
        end = min(len(words), word_pos + 3)
        phrase = ' '.join(words[start:end])

        # Clean up phrase
        phrase = re.sub(r'[^\w\s]', '', phrase).strip()
        return phrase
    except Exception as e:
        logger.error(f"Error in extract_phrase_around_word: {str(e)}")
        return None

def generate_focus_points(text, key_concepts, num_points=3):
    """Generate learning focus points based on key concepts"""
    try:
        sentences = sent_tokenize(text)
        if not sentences:
             logger.warning("No sentences found for focus points")
             return ["Review the full text for key information"]

        focus_sentences = []
        for concept in key_concepts:
            if not concept:
                continue
            for sentence in sentences:
                if any(word in sentence.lower() for word in concept.lower().split()):
                    focus_sentences.append(sentence)
                    break
        if len(focus_sentences) < num_points:
            remaining = [s for s in sentences if s not in focus_sentences]
            focus_sentences += remaining[:num_points - len(focus_sentences)]

        if not focus_sentences:
            logger.warning("No focus sentences generated")
            return ["Focus on understanding the main concepts presented"]

        focus_points = []
        for sentence in focus_sentences[:num_points]:
            point = simplify_sentence(sentence)
            if point:
                focus_points.append(point)

        if not focus_points:
            logger.warning("No focus points generated after simplification")
            return ["Focus on understanding the main concepts presented"]

        return focus_points
    except Exception as e:
        logger.error(f"Error in generate_focus_points: {str(e)}")
        return ["Focus on understanding the core content"]

def simplify_sentence(sentence):
    """Create a simplified version of a sentence for a focus point"""
    try:
        parts = re.split(r'[,;:]', sentence)
        if parts:
            return parts[0].strip()
        return sentence
    except Exception as e:
        logger.error(f"Error in simplify_sentence: {str(e)}")
        return sentence

def generate_related_topics(text, key_concepts, num_topics=4):
    """Generate related topics based on text and key concepts"""
    try:
        topics = set()
        domains = [
            "biology", "chemistry", "physics", "mathematics", "history",
            "geology", "astronomy", "ecology", "evolution", "genetics",
            "cell biology", "anatomy", "physiology", "biochemistry",
            "organic chemistry", "inorganic chemistry", "quantum physics",
            "thermodynamics", "mechanics", "electromagnetism", "calculus",
            "statistics", "algebra", "geometry", "world history",
            "ancient history", "modern history", "geography", "economics",
            "psychology", "sociology", "anthropology", "literature",
            "linguistics", "computer science", "artificial intelligence",
            "machine learning", "data science", "engineering", "medicine"
        ]

        text_lower = text.lower()
        for domain in domains:
            if domain in text_lower:
                topics.add(domain.title())
        for concept in key_concepts:
            if not concept:
                continue

            words = concept.lower().split()
            for domain in domains:
                domain_words = domain.split()
                if any(word in domain_words for word in words):
                    topics.add(domain.title())

        if len(topics) < num_topics:
            default_topics = ["Theoretical Foundations", "Practical Applications",
                            "Historical Development", "Modern Advances",
                            "Research Methods", "Educational Approaches"]
            topics.update(default_topics[:num_topics - len(topics)])

        return list(topics)[:num_topics]
    except Exception as e:
        logger.error(f"Error in generate_related_topics: {str(e)}")
        return ["General Knowledge", "Academic Study", "Further Reading", "Related Research"]


# --- Health Check Endpoint ---
@app.route('/api/health', methods=['GET'])
def health_check():
    status = "ok" if client is not None else "limited"
    version = "1.0.0"

    try:
        nltk_status = "ok"
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk_status = "missing_resources"

        return jsonify({
            'status': status,
            'version': version,
            'services': {
                'tts': 'available' if client is not None else 'unavailable',
                'nltk': nltk_status,
                'gemini': 'available' if gemini_available else 'unavailable', # Add Gemini status
            },
            'timestamp': os.path.getmtime(__file__) if os.path.exists(__file__) else None
        })
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() in ('true', '1', 't')

    logger.info(f"Starting Flask app on port {port} with debug={debug_mode}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
