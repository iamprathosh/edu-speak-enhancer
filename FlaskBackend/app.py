import nltk
import os
import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from google.cloud import texttospeech, speech, vision
from google.api_core import exceptions
import io
from dotenv import load_dotenv
from nltk.corpus import stopwords, wordnet
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.probability import FreqDist
from nltk.chunk import RegexpParser
from heapq import nlargest
import string
import re
from collections import Counter
import traceback
import google.generativeai as genai
import json
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
import language_tool_python  # Added for grammar check
import uuid  # Added for generating unique IDs
import base64
from googletrans import Translator

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
app = Flask(__name__, static_folder='static')
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],  # Example limits
    storage_uri="memory://",  # Use in-memory storage; consider Redis for production
)

# Add a test route that serves a static HTML page
@app.route('/test')
def test_page():
    logger.info("Test page requested")
    return app.send_static_file('test.html')

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
    tts_client = texttospeech.TextToSpeechClient()
    logger.info("Google Cloud TTS client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Google Cloud TTS client: {str(e)}")
    tts_client = None  # Ensure client is None if initialization fails

# Initialize Google Cloud Speech-to-Text
try:
    speech_client = speech.SpeechClient()
    logger.info("Google Cloud Speech client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Google Cloud Speech client: {str(e)}")
    speech_client = None

# Initialize Google Cloud Vision
try:
    vision_client = vision.ImageAnnotatorClient()
    logger.info("Google Cloud Vision client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Google Cloud Vision client: {str(e)}")
    vision_client = None

# Initialize LanguageTool
try:
    lang_tool = language_tool_python.LanguageTool('en-US')
    logger.info("LanguageTool initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize LanguageTool: {str(e)}")
    lang_tool = None


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
    try:  # Download WordNet
        nltk.data.find('corpora/wordnet')
        logger.info("NLTK wordnet already downloaded")
    except LookupError:
        logger.info("Downloading NLTK wordnet")
        nltk.download('wordnet', quiet=True)
    # Googletrans resource check if necessary, though they usually don't require explicit download like nltk
    logger.info("Googletrans is assumed to be installed via pip.")


download_nltk_resources()

# Function to detect the language of the given text
def detect_language_for_word(text):
    # Using a simpler approach with the new version of googletrans
    # googletrans 4.0.0+ is async, but we're running in a sync environment
    # Let's use a simpler language detection method
    
    # Map of common words to their languages
    french_words = {'bonjour', 'merci', 'oui', 'non', 'le', 'la', 'les', 'et', 'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'un', 'une', 'des', 'du', 'de', 'à', 'au', 'aux', 'avec', 'pour', 'dans', 'sur', 'sous', 'sans', 'qui', 'que', 'quoi', 'comment', 'pourquoi', 'où'}
    spanish_words = {'hola', 'gracias', 'sí', 'no', 'el', 'la', 'los', 'las', 'y', 'yo', 'tú', 'él', 'ella', 'nosotros', 'vosotros', 'ellos', 'ellas', 'un', 'una', 'unos', 'unas', 'del', 'al', 'a', 'con', 'para', 'en', 'sobre', 'bajo', 'sin', 'quien', 'que', 'como', 'porque', 'donde'}
    german_words = {'hallo', 'danke', 'ja', 'nein', 'der', 'die', 'das', 'und', 'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr', 'sie', 'ein', 'eine', 'einen', 'einem', 'einer', 'eines', 'mit', 'für', 'in', 'auf', 'unter', 'ohne', 'wer', 'was', 'wie', 'warum', 'wo'}
    
    try:
        # Clean the text
        cleaned_text = text.lower().strip().rstrip('.,:;!?')
        
        # Check if the word is in any of our language sets
        if cleaned_text in french_words:
            logger.info(f"Detected '{text}' as French")
            return 'fr'
        elif cleaned_text in spanish_words:
            logger.info(f"Detected '{text}' as Spanish")
            return 'es'
        elif cleaned_text in german_words:
            logger.info(f"Detected '{text}' as German")
            return 'de'
        
        # Check for language-specific patterns - this is a simple approximation
        if any(char in 'éèêëàâäæçîïôœùûüÿ' for char in cleaned_text):
            logger.info(f"Detected '{text}' as likely French (character patterns)")
            return 'fr'
        elif any(char in 'áéíóúüñ¿¡' for char in cleaned_text):
            logger.info(f"Detected '{text}' as likely Spanish (character patterns)")
            return 'es'
        elif any(char in 'äöüß' for char in cleaned_text):
            logger.info(f"Detected '{text}' as likely German (character patterns)")
            return 'de'
        
        # Default to English for unknown words
        logger.info(f"Defaulting '{text}' to English")
        return 'en'
    except Exception as e:
        logger.error(f"Error detecting language for '{text}': {e}")
        # Fallback to English to be safe
        return 'en'


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

@app.route('/api/tts_google', methods=['POST'])
@limiter.limit("10 per minute")  # Apply rate limiting
def text_to_speech_google(): # Renamed to avoid conflict
    logger.info("Received request for /api/tts (Google TTS)")
    if tts_client is None:
        logger.error("Google Cloud TTS client not initialized")
        return jsonify({'error': 'Text-to-speech service unavailable'}), 503

    try:
        data = request.get_json()
        # Log the raw received data
        logger.info(f"Received TTS request data: {data}")

        if not data:
            logger.warning("No JSON data received in request")
            return jsonify({'error': 'Invalid request: No JSON data'}), 400

        text = data.get('text', '').strip()
        if not text:
            logger.warning("Missing or empty 'text' field in request")
            return jsonify({'error': 'Text is required'}), 400

        voice_id = data.get('voiceId', 'en-US-Standard-D')  # Default
        # Log parsed parameters
        logger.info(f"TTS parameters - Text length: {len(text)}, Voice ID: {voice_id}")

        try:
            speed = float(data.get('speed', 2.0))
            if speed < 0.25 or speed > 4.0:
                logger.warning(f"Speed value out of range: {speed}. Received: {data.get('speed')}")
                return jsonify({'error': 'Speed must be between 0.25 and 4.0'}), 400
        except (TypeError, ValueError) as e:
            logger.warning(f"Invalid speed value: {data.get('speed')}. Error: {e}")
            return jsonify({'error': 'Speed must be a valid number'}), 400

        try:
            language_code = '-'.join(voice_id.split('-')[:2])
            if not language_code or len(language_code.split('-')) != 2:
                raise ValueError("Invalid voice ID format for language code extraction")
        except Exception as e:
            logger.warning(f"Invalid voice ID format: {voice_id}. Error extracting language code: {e}")
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
            logger.info(f"Calling Google TTS API with: Input='{text[:50]}...', Voice={voice}, Config={audio_config}") # Log API call details
            response = tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            logger.info("Successfully received TTS response from Google API")

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
            # Log the specific Google API error
            logger.error(f"Google API call error during synthesize_speech: {str(e)}", exc_info=True)
            return jsonify({'error': f'Text-to-speech API error: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Error processing TTS response or sending file: {str(e)}", exc_info=True)
            return jsonify({'error': f'Server error after TTS generation: {str(e)}'}), 500

    except Exception as e:
        # Log any other unexpected errors in the main try block
        logger.error(f"Unhandled error in text_to_speech_google function: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/texttospeech', methods=['POST'])
@limiter.limit("10 per minute")
def text_to_speech_custom():
    logger.info("Received request for /api/texttospeech (Multi-language TTS)")
    # Log the request headers for debugging
    logger.info(f"Request headers: {dict(request.headers)}")
    
    try:
        if tts_client is None:
            logger.error("Google Cloud TTS client not initialized")
            return jsonify({'error': 'Text-to-speech service unavailable'}), 503
            
        data = request.get_json()
        logger.info(f"Received custom TTS request data: {data}")

        if not data:
            logger.warning("No JSON data received in request for custom TTS")
            return jsonify({'error': 'Invalid request: No JSON data'}), 400

        text = data.get('text', '').strip()
        if not text:
            logger.warning("Missing or empty 'text' field in custom TTS request")
            return jsonify({'error': 'Text is required'}), 400

        logger.info(f"Processing text for TTS: '{text}'")
        words = text.split(' ')
        logger.info(f"Split into {len(words)} words")
        
        # Create an in-memory bytes buffer for the MP3 data
        mp3_fp = io.BytesIO()
        
        # Group words by language for better performance
        current_lang = None
        current_group = []
        lang_groups = []
        
        for word in words:
            if not word.strip():  # Skip empty strings
                continue
                
            detected_lang = detect_language_for_word(word)
            
            # If language changes or this is the first word, start a new group
            if detected_lang != current_lang:
                if current_group:
                    lang_groups.append((current_lang, ' '.join(current_group)))
                current_lang = detected_lang
                current_group = [word]
            else:
                current_group.append(word)
        
        # Add the last group if it exists
        if current_group:
            lang_groups.append((current_lang, ' '.join(current_group)))
        
        logger.info(f"Grouped text into {len(lang_groups)} language segments")
        groups_processed = 0
        
        # Map language codes to ones supported by Google Cloud TTS
        lang_code_map = {
            'en': 'en-US',
            'fr': 'fr-FR',
            'es': 'es-ES',
            'de': 'de-DE'
        }
        
        for lang, text_segment in lang_groups:
            try:
                google_lang_code = lang_code_map.get(lang, 'en-US')
                
                # Use Google Cloud TTS to synthesize speech for the entire segment
                synthesis_input = texttospeech.SynthesisInput(text=text_segment)
                
                # Select a voice appropriate for the language
                voice = texttospeech.VoiceSelectionParams(
                    language_code=google_lang_code,
                    ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
                )
                
                # Configure audio settings
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                
                # Make the API call for the whole segment
                logger.info(f"Calling Google TTS API for segment in language {google_lang_code}: '{text_segment[:50]}...'")
                response = tts_client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
                
                # Write the audio content to our buffer
                mp3_fp.write(response.audio_content)
                groups_processed += 1
                
            except exceptions.GoogleAPICallError as e:
                logger.error(f"Google API call error for segment '{text_segment[:50]}...': {str(e)}")
                if groups_processed == 0:
                    return jsonify({'error': f'Text-to-speech API error: {str(e)}'}), 500
                continue
            except Exception as e:
                logger.error(f"Error generating TTS for segment in lang '{lang}': {e}")
                logger.error(traceback.format_exc())
                
                if groups_processed == 0:
                    return jsonify({'error': f'Failed to generate speech. Error: {str(e)}'}), 500
                logger.warning(f"Skipping segment and continuing with the rest of the text")
                continue
        
        # If we haven't processed any groups successfully, return an error
        if groups_processed == 0:
            logger.error("No language segments were successfully processed")
            return jsonify({'error': 'Failed to generate speech for any parts of the text'}), 500
        
        # Rewind the buffer to the beginning to read the data
        mp3_fp.seek(0)
        audio_bytes = mp3_fp.read()
        
        # Encode the audio data to base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        logger.info(f"Successfully generated and encoded multi-language TTS audio, size: {len(audio_base64)} bytes")
        response = jsonify({'audio_base64': audio_base64})
        
        # Log the response headers for debugging
        logger.info(f"Response headers: {dict(response.headers)}")
        return response

    except Exception as e:
        logger.error(f"Unhandled error in custom text_to_speech_custom function: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/voices', methods=['GET'])
def get_voices():
    if tts_client is None:
        logger.error("Google Cloud TTS client not initialized")
        return jsonify({'error': 'Voice service unavailable'}), 503

    try:
        logger.info("Retrieving available voices from Google TTS API")
        try:
            response = tts_client.list_voices()
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


@app.route('/api/grammar-check', methods=['POST'])
@limiter.limit("20 per minute")  # Higher limit for potentially faster checks
def grammar_check():
    """Checks grammar for the provided text, prioritizing Gemini."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request: No JSON data'}), 400
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'error': 'Text is required'}), 400

        logger.info(f"Received grammar check request for text length: {len(text)}")

        corrections = []
        use_fallback = True

        if gemini_available and gemini_model:
            try:
                logger.info("Attempting grammar check with Gemini.")
                prompt = f"""
                Analyze the following text for grammatical errors, spelling mistakes, and awkward phrasing.
                Provide corrections and brief explanations.
                Format your response as a JSON list, where each item is an object with these exact keys:
                "id" (generate a unique UUID string),
                "error" (the incorrect word or phrase),
                "correction" (the suggested correction),
                "explanation" (a brief explanation of the error),
                "startIndex" (estimated 0-based start index of the error in the original text),
                "endIndex" (estimated 0-based end index of the error in the original text).

                If there are no errors, return an empty JSON list: [].

                Text to analyze:
                "{text}"
                """
                response = gemini_model.generate_content(prompt)
                result_text = response.text

                # Attempt to parse the JSON response
                if '[' in result_text and ']' in result_text:
                    json_str = result_text[result_text.find('['):result_text.rfind(']') + 1]
                    parsed_corrections = json.loads(json_str)

                    # Basic validation of the parsed structure
                    if isinstance(parsed_corrections, list):
                        corrections = parsed_corrections
                        use_fallback = False
                        logger.info(f"Successfully received and parsed {len(corrections)} corrections from Gemini.")
                    else:
                        logger.warning("Gemini response was not a valid JSON list.")
                else:
                    logger.warning("Could not find JSON list in Gemini response.")

            except Exception as e:
                logger.error(f"Error during Gemini grammar check: {str(e)}")
                # Fallback will be used

        if use_fallback:
            if lang_tool:
                logger.info("Using LanguageTool for grammar check fallback.")
                try:
                    matches = lang_tool.check(text)
                    for match in matches:
                        # Ensure there's at least one replacement suggestion
                        correction = match.replacements[0] if match.replacements else text[match.offset:match.offset + match.errorLength]
                        corrections.append({
                            "id": f"gc_lt_{uuid.uuid4()}",
                            "error": text[match.offset:match.offset + match.errorLength],
                            "correction": correction,
                            "explanation": match.message,
                            "startIndex": match.offset,
                            "endIndex": match.offset + match.errorLength
                        })
                    logger.info(f"Found {len(corrections)} potential issues using LanguageTool.")
                except Exception as lt_error:
                    logger.error(f"Error during LanguageTool check: {str(lt_error)}")
            else:
                logger.error("LanguageTool not available for fallback grammar check.")
 
        return jsonify(corrections)

    except Exception as e:
        logger.error(f"Error in grammar_check: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/speech-error-analysis', methods=['POST'])
@limiter.limit("5 per minute")  # Lower limit due to potential processing intensity
def speech_error_analysis():
    """Analyzes uploaded speech audio, using Gemini to enhance transcript analysis."""
    try:
        if speech_client is None:
            logger.error("Google Cloud Speech client not initialized")
            return jsonify({'error': 'Speech analysis service unavailable'}), 503

        if 'audio' not in request.files:
            logger.warning("No audio file found in request")
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            logger.warning("No selected audio file")
            return jsonify({'error': 'No selected audio file'}), 400

        filename = secure_filename(audio_file.filename)
        logger.info(f"Received audio file for analysis: {filename}")

        transcript = None
        errors = []  # Real error detection is complex, start with empty
        fluency = {  # Placeholder fluency data
            "score": 75,
            "pace": "slightly fast",
            "fillerWords": ["um", "uh"]
        }

        # --- Actual Speech-to-Text ---
        try:
            audio_content = audio_file.read()
            audio = speech.RecognitionAudio(content=audio_content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                language_code="en-US",
            )

            logger.info("Calling Google Cloud Speech-to-Text API")
            response = speech_client.recognize(config=config, audio=audio)

            if response.results:
                transcript = response.results[0].alternatives[0].transcript
                logger.info(f"Successfully transcribed audio. Transcript length: {len(transcript)}")
            else:
                logger.warning("Google Cloud Speech-to-Text returned no results.")
                transcript = ""

        except exceptions.GoogleAPICallError as e:
            logger.error(f"Google Cloud Speech API call error: {str(e)}")
            return jsonify({'error': f'Speech transcription failed: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Error during speech transcription: {str(e)}")
            return jsonify({'error': 'Failed to process audio file'}), 500

        analysis_result = {
            "transcript": transcript,
            "errors": errors,  # Currently empty
            "fluency": fluency  # Placeholder
        }

        # --- Enhance with Gemini if available ---
        if gemini_available and gemini_model and transcript:  # Check if transcript exists
            try:
                logger.info("Attempting to enhance speech analysis with Gemini.")
                fluency_details = json.dumps(analysis_result["fluency"])  # Send placeholder fluency

                prompt = f"""
                Review the following speech transcript.
                Identify potential pronunciation errors, grammatical mistakes, or awkward phrasing within the transcript.
                Also, provide general feedback on fluency based on the provided (placeholder) metrics.

                Transcript: "{analysis_result['transcript']}"

                Placeholder Fluency Metrics: {fluency_details}

                Format your response as a JSON object with optional keys:
                "identified_issues": A list of objects, each containing "id" (generate a unique UUID string), "issue" (the identified problematic word/phrase), "suggestion" (correction or improvement idea), and "explanation".
                "fluency_feedback": A string containing overall fluency advice based on the transcript and metrics.

                Example Response:
                {{
                  "identified_issues": [
                    {{ "id": "{uuid.uuid4()}", "issue": "wreckonized", "suggestion": "recognized", "explanation": "Potential mispronunciation. Focus on the 'rec' sound." }}
                  ],
                  "fluency_feedback": "Your pace is slightly fast, which can sometimes impact clarity. Try taking brief pauses. Reducing filler words like 'um' will also help."
                }}
                """
                response = gemini_model.generate_content(prompt)
                result_text = response.text

                # Attempt to parse JSON
                if '{' in result_text and '}' in result_text:
                    json_str = result_text[result_text.find('{'):result_text.rfind('}') + 1]
                    gemini_feedback = json.loads(json_str)

                    # Replace placeholder errors with Gemini's identified issues
                    if "identified_issues" in gemini_feedback and isinstance(gemini_feedback["identified_issues"], list):
                        analysis_result["errors"] = gemini_feedback["identified_issues"]  # Overwrite empty errors
                        logger.info(f"Added {len(analysis_result['errors'])} issues identified by Gemini.")

                    if "fluency_feedback" in gemini_feedback and isinstance(gemini_feedback["fluency_feedback"], str):
                        analysis_result["fluency"]["feedback"] = gemini_feedback["fluency_feedback"]
                        logger.info("Added fluency feedback from Gemini.")

                else:
                    logger.warning("Could not parse JSON feedback from Gemini for speech analysis.")

            except Exception as e:
                logger.error(f"Error during Gemini speech analysis enhancement: {str(e)}")

        return jsonify(analysis_result)

    except Exception as e:
        logger.error(f"Error in speech_error_analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/image-to-text', methods=['POST'])
@limiter.limit("10 per minute")  # Moderate limit for OCR
def image_to_text():
    """Extracts text from an uploaded image, prioritizing Gemini Vision (if available)."""
    if vision_client is None:
        logger.error("Google Cloud Vision client not initialized")
        return jsonify({'error': 'Image analysis service unavailable'}), 503
    try:
        if 'image' not in request.files:
            logger.warning("No image file found in request")
            return jsonify({'error': 'No image file provided'}), 400

        image_file = request.files['image']
        if image_file.filename == '':
            logger.warning("No selected image file")
            return jsonify({'error': 'No selected image file'}), 400

        filename = secure_filename(image_file.filename)
        logger.info(f"Received image file for OCR: {filename}")

        extracted_text = None

        # --- Google Cloud Vision OCR ---
        try:
            image_content = image_file.read()
            image = vision.Image(content=image_content)

            logger.info("Calling Google Cloud Vision API for text detection")
            response = vision_client.text_detection(image=image)

            if response.error.message:
                logger.error(f"Google Cloud Vision API error: {response.error.message}")
                return jsonify({'error': f'Image analysis failed: {response.error.message}'}), 500

            if response.text_annotations:
                extracted_text = response.text_annotations[0].description
                logger.info(f"Successfully extracted text from image. Length: {len(extracted_text)}")
            else:
                logger.warning("Google Cloud Vision found no text in the image.")
                extracted_text = ""

        except Exception as e:
            logger.error(f"Error during Google Cloud Vision OCR: {str(e)}")
            return jsonify({'error': 'Failed to process image file'}), 500

        if extracted_text is None:
            logger.error("Text extraction resulted in None.")  # Should ideally be caught above
            return jsonify({"error": "Could not extract text from image"}), 500

        return jsonify({"extractedText": extracted_text})

    except Exception as e:
        logger.error(f"Error in image_to_text: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500


# --- Health Check Endpoint ---
@app.route('/api/health', methods=['GET'])
def health_check():
    logger.info("Health check endpoint called")
    status = "ok"  # Assume ok unless specific services fail
    version = "1.0.0"

    try:
        nltk_status = "ok"
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('taggers/averaged_perceptron_tagger')  # Check tagger
            nltk.data.find('corpora/wordnet')  # Check wordnet
        except LookupError:
            nltk_status = "missing_resources"

        tts_status = 'available' if tts_client is not None else 'unavailable'
        stt_status = 'available' if speech_client is not None else 'unavailable'
        ocr_status = 'available' if vision_client is not None else 'unavailable'
        grammar_status = 'available' if lang_tool is not None else 'unavailable'
        gemini_status = 'available' if gemini_available else 'unavailable'

        if any(s == 'unavailable' for s in [tts_status, stt_status, ocr_status, grammar_status, gemini_status]):
            status = "limited"
            
        # Add CORS headers explicitly for debugging
        response = jsonify({
            'status': status,
            'version': version,
            'services': {
                'tts': tts_status,
                'nltk': nltk_status,
                'gemini': gemini_status,
                'speech_to_text': stt_status,
                'ocr': ocr_status,
                'grammar_check': grammar_status,
            },
            'timestamp': os.path.getmtime(__file__) if os.path.exists(__file__) else None
        })
        
        logger.info(f"Health check response: {status}")
        return response
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() in ('true', '1', 't')

    logger.info(f"Starting Flask app on port {port} with debug={debug_mode}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
