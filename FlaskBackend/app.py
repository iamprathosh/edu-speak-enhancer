import nltk
import os
import logging
from flask import Flask, request, jsonify, send_file, session # Added session
from flask_cors import CORS
from google.cloud import texttospeech, speech, vision
from google.api_core import exceptions
from dotenv import load_dotenv
from nltk.corpus import stopwords, wordnet
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.probability import FreqDist
from nltk.chunk import RegexpParser
from heapq import nlargest
from collections import Counter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
# language_tool_python # Original comment
# uuid # Original comment
from googletrans import Translator
from werkzeug.security import generate_password_hash, check_password_hash # Added for password hashing
# datetime # Original comment
from functools import wraps # Added for decorators

import logging
import os
import json
import io
import datetime
import traceback
import base64
import google.generativeai as genai
import language_tool_python # Ensure this is actively imported if lang_tool is used
import nltk # Ensure nltk is imported if its submodules are used directly after download

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
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your_very_secret_key_here_change_me') # Added SECRET_KEY for sessions
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Explicitly set for development
app.config['SESSION_COOKIE_SECURE'] = False # Explicitly set for HTTP development
# Get allowed origins from environment variable or use defaults
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:8080,http://127.0.0.1:8080')
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS.split(',')}}, supports_credentials=True) # Ensure frontend origin is allowed and credentials supported

# User data store
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
        return {}
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            # Ensure history is a list for each user
            for username, data in users.items():
                if 'history' not in data or not isinstance(data['history'], list):
                    data['history'] = []
            return users
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading users file: {e}")
        # If file is corrupted or unreadable, start with an empty user set for this session
        # and try to create/overwrite with an empty JSON object to fix it for next time.
        try:
            with open(USERS_FILE, 'w') as f:
                json.dump({}, f)
        except IOError as save_e:
            logger.error(f"Could not even create/overwrite users.json: {save_e}")
        return {}

def save_users(users_data):
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=4)
    except IOError as e:
        logger.error(f"Error saving users file: {e}")

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

# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"login_required: Auth check TEMPORARILY BYPASSED. Current session: {dict(session)}")
        logger.info(f"login_required: Request cookies: {request.cookies}")
        # if 'user_id' not in session: # <--- Temporarily commented out
        #     logger.warning(f"login_required: 'user_id' not in session. Access denied.")
        #     return jsonify({'error': 'Authentication required'}), 401
        # logger.info(f"login_required: 'user_id' found: {session.get('user_id', 'N/A')}. Access granted (bypass active).")
        return f(*args, **kwargs)
    return decorated_function

# --- User Authentication Endpoints ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    users = load_users()
    if username in users:
        return jsonify({'error': 'Username already exists'}), 409 # 409 Conflict

    users[username] = {
        'password_hash': generate_password_hash(password),
        'history': []
    }
    save_users(users)
    session['user_id'] = username  # Log in the user upon registration
    logger.info(f"User {username} registered successfully and logged in.")
    # Return user object for consistency and immediate use by frontend
    return jsonify({'message': 'User registered successfully', 'user': {'username': username}}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    users = load_users()
    user = users.get(username)

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid username or password'}), 401

    session['user_id'] = username
    logger.info(f"User {username} logged in successfully.")
    return jsonify({'message': 'Login successful', 'user': {'username': username}}), 200

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    user_id = session.pop('user_id', None)
    if user_id:
        logger.info(f"User {user_id} logged out.")
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/me', methods=['GET'])
@login_required
def me():
    user_id = session.get('user_id')
    
    if not user_id:
        logger.info("/api/me: No user_id in session (auth bypass active). Returning mock user.")
        return jsonify({'username': 'mockuser', 'history_count': 0, 'isMock': True}), 200

    users = load_users()
    user_data = users.get(user_id)
    if not user_data: # Should not happen if @login_required works and user exists in users.json
        logger.error(f"/api/me: User {user_id} found in session but not in users.json. This is a data consistency issue.")
        return jsonify({'error': 'User data not found after authentication'}), 404
    return jsonify({'username': user_id, 'history_count': len(user_data.get('history', []))}), 200

# --- History Management ---
def add_user_history(username, feature, details):
    users = load_users()
    if username in users:
        # Ensure history list exists
        if 'history' not in users[username] or not isinstance(users[username]['history'], list):
            users[username]['history'] = []
        
        history_entry = {
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z', # ISO 8601 format
            'feature': feature,
            'details': details
        }
        users[username]['history'].append(history_entry)
        # Optional: Limit history size
        # max_history = 50 
        # users[username]['history'] = users[username]['history'][-max_history:]
        save_users(users)
        logger.info(f"History added for user {username}, feature {feature}.")
    else:
        logger.warning(f"Attempted to add history for non-existent user {username}.")

@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    user_id = session.get('user_id')
    users = load_users()
    user_data = users.get(user_id)
    if not user_data:
        return jsonify({'error': 'User not found'}), 404 # Should be caught by @login_required
    
    # Sort history by timestamp descending (newest first)
    user_history = sorted(user_data.get('history', []), key=lambda x: x['timestamp'], reverse=True)
    return jsonify({'history': user_history}), 200

# Initialize Gemini API (Prioritize)
gemini_available = False
gemini_model = None
if "GEMINI_API_KEY" in os.environ:
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])  # Configure once
        gemini_model = genai.GenerativeModel('gemini-2.0-flash')  # Updated model initialization
        gemini_available = True
        logger.info("Gemini API initialized successfully with gemini-2.0-flash model.")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API: {str(e)}")
else:
    logger.warning("GEMINI_API_KEY environment variable not set!")

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


# --- API Health Check ---
@app.route('/api/health', methods=['GET'])
def health_check():
    logger.info("Health check endpoint hit")
    # Check status of critical services (TTS, Speech-to-Text, Gemini, etc.)
    services_status = {
        "tts_google": "available" if tts_client else "unavailable",
        "speech_to_text_google": "available" if speech_client else "unavailable",
        "vision_google": "available" if vision_client else "unavailable",
        "gemini_ai": "available" if gemini_available and gemini_model else "unavailable",
        "language_tool": "available" if lang_tool else "unavailable"
    }
    # Overall status can be 'ok' if core services are up, or 'degraded'/'error'
    # For simplicity, let's say 'ok' if at least Gemini and TTS are up.
    # You can define more complex logic here.
    if gemini_available and tts_client:
        overall_status = "ok"
    elif gemini_available or tts_client:
        overall_status = "degraded"
    else:
        overall_status = "error"
        
    return jsonify({
        "status": overall_status,
        "timestamp": datetime.datetime.utcnow().isoformat() + 'Z',
        "services": services_status
    }), 200

# --- API Endpoints ---

@app.route('/api/tts_google', methods=['POST'])
@limiter.limit("10 per minute")  # Apply rate limiting
@login_required # Protect this endpoint
def text_to_speech_google(): # Renamed to avoid conflict
    user_id = session.get('user_id') # Get current user
    logger.info(f"User {user_id} requesting /api/tts (Google TTS)")
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

        # Add to history
        add_user_history(user_id, 'tts_google', {'text_length': len(text), 'voice_id': data.get('voiceId')})

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


@app.route('/api/speech-error-analysis', methods=['POST'])
@limiter.limit("5 per minute")  # Lower limit due to potential processing intensity
@login_required # Protect this endpoint
def speech_error_analysis():
    user_id = session.get('user_id') # Get current user
    logger.info(f"User {user_id} requesting /api/speech-error-analysis")
    if not gemini_available or gemini_model is None:
        logger.error("Gemini API not available for speech error analysis")
        return jsonify({'error': 'Advanced speech analysis service is currently unavailable due to Gemini API issues.'}), 503

    if 'audio' not in request.files:
        logger.warning("No audio file provided in request")
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    filename = secure_filename(audio_file.filename if audio_file.filename else "audio_data.webm")

    try:
        audio_bytes = audio_file.read()
        logger.info(f"Audio file received: {filename}, size: {len(audio_bytes)} bytes for user {user_id}")

        # Add to history (early, before potentially failing API calls)
        add_user_history(user_id, 'speech_error_analysis', {'filename': filename, 'size': len(audio_bytes)})

        if not audio_bytes:
            logger.warning("Audio file is empty after reading from request.")
            return jsonify({'error': 'Audio file is empty or could not be read from the request.'}), 400

        transcript = None
        if speech_client:
            audio = speech.RecognitionAudio(content=audio_bytes)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS, # Ensure frontend sends compatible format
                sample_rate_hertz=48000, # Ensure frontend sends compatible sample rate or make this flexible
                language_code="en-US",
                enable_automatic_punctuation=True
            )
            logger.info("Sending audio to Google Speech-to-Text API for transcription")
            try:
                response = speech_client.recognize(config=config, audio=audio)
                if not response.results or not response.results[0].alternatives:
                    logger.warning("Speech-to-Text API returned no transcription.")
                    return jsonify({'error': 'Speech-to-Text API returned no transcription.'}), 500 # MODIFIED
                transcript = response.results[0].alternatives[0].transcript
                logger.info(f"Transcript: {transcript}")
            except exceptions.GoogleAPICallError as e:
                logger.error(f"Google Speech-to-Text API error: {str(e)}")
                return jsonify({'error': f'Google Speech-to-Text API error: {str(e)}'}), 500
        else:
            logger.error("Speech client not available for transcription.")
            return jsonify({'error': 'Speech transcription service not available.'}), 503

        if transcript is None: # Should not happen if previous checks are correct, but as a safeguard
            logger.error("Transcription resulted in None unexpectedly.")
            return jsonify({'error': 'Failed to obtain transcript.'}), 500

        prompt = f"""Analyze the following spoken sentence for pronunciation errors: "{transcript}".
Provide a detailed analysis of any mispronounced words.
For each mispronounced word, identify the word, suggest the correct pronunciation (phonetically if possible),
and explain the error.
The user was attempting to say the sentence. The audio quality might vary.
Focus on common pronunciation mistakes for an English language learner.

If no significant errors are found, state that the pronunciation is good.

Format the output as a JSON object with the following structure:
{{
  "sentence": "The original transcribed sentence.",
  "errorWords": ["word1", "word2", ...],
  "errors": {{
    "word1": {{
      "word": "word1",
      "correctPronunciation": "kəˈrɛkt prəˌnʌnsiˈeɪʃən",
      "userPronunciation": "how the user might have said it (descriptive)",
      "explanation": "Detailed explanation of the error and how to correct it."
    }}
  }}
}}

If no errors:
{{
  "sentence": "The original transcribed sentence.",
  "errorWords": [],
  "errors": {{}}
}}

Transcript:
{transcript}
"""
        logger.info("Sending transcript to Gemini for error analysis.")
        gemini_response = gemini_model.generate_content(prompt)

        logger.info(f"Raw Gemini response: {gemini_response.text}")

        try:
            response_text = gemini_response.text.strip()
            # Strip markdown code block if present
            if response_text.startswith("```json") and response_text.endswith("```"):
                response_text = response_text[len("```json"):-len("```")].strip()
            elif response_text.startswith("```") and response_text.endswith("```"): # Handle generic markdown code block
                response_text = response_text[len("```"):-len("```")].strip() # ADDED strip for generic block
            
            # Ensure the text is not empty after stripping
            if not response_text:
                logger.error("Gemini response text is empty after stripping markdown.") # ADDED log
                return jsonify({'error': 'Gemini response was empty after processing.'}), 500 # ADDED jsonify

            analysis_result = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Problematic Gemini response text (after attempting to strip markdown): {response_text[:500]}...") # Log the text that failed
            return jsonify({'error': 'Failed to parse Gemini response as JSON', 'details': str(e)}), 500 # MODIFIED

        if not isinstance(analysis_result, dict) or \
           'sentence' not in analysis_result or \
           'errorWords' not in analysis_result or \
           'errors' not in analysis_result:
            logger.error(f"Gemini response is not in the expected format: {analysis_result}")
            return jsonify({'error': 'Gemini response is not in the expected format.'}), 500 # MODIFIED
            
        logger.info(f"Speech error analysis successful: {analysis_result}")
        return jsonify(analysis_result)

    except exceptions.GoogleAPICallError as e:
        logger.error(f"A Google API call error occurred during speech error analysis: {str(e)}", exc_info=True)
        return jsonify({'error': f'A Google API call error occurred: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error during speech error analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Unexpected error during speech error analysis: {str(e)}'}), 500 # MODIFIED


@app.route('/api/texttospeech', methods=['POST'])
@limiter.limit("10 per minute")
@login_required # Protect this endpoint
def text_to_speech_custom():
    user_id = session.get('user_id') # Get current user
    logger.info(f"User {user_id} requesting /api/texttospeech (Multi-language TTS)")
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

        # Add to history
        add_user_history(user_id, 'texttospeech_custom', {'text_length': len(text)})

        logger.info(f"Processing text for TTS: '{text}' for user {user_id}")
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
@login_required # Protect this endpoint
def get_voices():
    user_id = session.get('user_id') # Get current user
    logger.info(f"User {user_id} requesting /api/voices") # Log access
    if tts_client is None:
        logger.error("Google Cloud TTS client not initialized")
        return jsonify({'error': 'Text-to-speech service (for voices) unavailable'}), 503 # Added jsonify return

    try:
        logger.info("Retrieving available voices from Google TTS API")
        try:
            google_voices_response = tts_client.list_voices() # Renamed to avoid conflict
        except exceptions.GoogleAPICallError as e:
            logger.error(f"Google API call error during list_voices: {str(e)}", exc_info=True)
            return jsonify({'error': f'TTS voices API error: {str(e)}'}), 500 # Added jsonify return

        voices = []
        for voice in google_voices_response.voices: # Use the renamed variable
            voices.append({
                'id': voice.name,
                'name': voice.name, # Or a more friendly display name if available
                'languageCode': voice.language_codes[0] if voice.language_codes else 'N/A',
                'gender': texttospeech.SsmlVoiceGender(voice.ssml_gender).name
            })
        
        logger.info(f"Successfully retrieved {len(voices)} voices.")
        return jsonify({'voices': voices})

    except Exception as e:
        logger.error(f"Unhandled error in get_voices function: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error retrieving voices: {str(e)}'}), 500 # Added jsonify return


@app.route('/api/grammar-check', methods=['POST'])
@limiter.limit("15 per minute") # Example: 15 requests per minute
@login_required # Protect this endpoint
def grammar_check():
    user_id = session.get('user_id') # Get current user
    logger.info(f"User {user_id} requesting /api/grammar_check")
    if lang_tool is None:
        logger.error("LanguageTool not initialized")
        return jsonify({'error': 'Grammar check service unavailable'}), 503

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    text_to_check = data.get('text')

    if not text_to_check:
        return jsonify({"error": "No text provided for grammar check"}), 400

    if not isinstance(text_to_check, str):
        return jsonify({"error": "Text must be a string"}), 400

    # Add to history
    add_user_history(user_id, 'grammar_check', {'text_length': len(text_to_check)})

    logger.info(f"Received grammar check request for text: '{text_to_check[:100]}...'")  # Log more text

    corrections = []
    # Prioritize Gemini if available
    if gemini_available and gemini_model:
        try:
            prompt = f"""Please correct the grammar of the following text and provide explanations for each correction.
            Respond ONLY with a valid JSON list of objects, where each object has 'original', 'corrected', and 'explanation' keys.
            If a phrase is correct and needs no changes, omit it.
            If the entire text is grammatically perfect, return an empty JSON list: [].
            Do not attempt to correct stylistic choices unless they are grammatically incorrect.
            Ensure the output is nothing but the JSON list, without any surrounding text, markdown, or explanations outside the JSON structure.

            For example, if the input is 'I has a apple.', the output should be:
            [
                {{
                    "original": "has",
                    "corrected": "have",
                    "explanation": "The subject 'I' requires the verb 'have'."
                }},
                {{
                    "original": "a apple",
                    "corrected": "an apple",
                    "explanation": "Use 'an' before a vowel sound."
                }}
            ]

            Text to correct:
            "{text_to_check}"
            """
            logger.info("Sending request to Gemini for grammar check.")
            # Using the new SDK structure
            response = gemini_model.generate_content(prompt)
            
            # Debug: Print raw Gemini response text
            logger.debug(f"Raw Gemini response text: {response.text}")

            # Attempt to parse the JSON response from Gemini
            try:
                # The response.text should directly be the JSON string based on the prompt.
                # Remove potential markdown backticks if Gemini still adds them despite instructions
                cleaned_response_text = response.text.strip()
                if cleaned_response_text.startswith("```json"):
                    cleaned_response_text = cleaned_response_text[7:]
                if cleaned_response_text.endswith("```"):
                    cleaned_response_text = cleaned_response_text[:-3]
                
                gemini_corrections = json.loads(cleaned_response_text.strip())
                
                if isinstance(gemini_corrections, list):
                    # Validate structure of corrections if needed here
                    corrections = gemini_corrections
                    logger.info(f"Successfully processed grammar check with Gemini. Found {len(corrections)} corrections.")
                else:
                    logger.warning(f"Gemini response was not a list as expected. Response: {gemini_corrections}")
                    # Fallback logic can be triggered here if needed
                    raise ValueError("Gemini response was not a list.")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response: {e}")
                logger.error(f"Problematic Gemini response text: {response.text}")
                # Fallback to LanguageTool if Gemini response is not valid JSON
                if lang_tool:
                    logger.info("Falling back to LanguageTool due to Gemini JSON parsing error.")
                    matches = lang_tool.check(text_to_check)
                    for match in matches:
                        if match.replacements:
                            corrections.append({
                                "original": text_to_check[match.offset:match.offset+match.errorLength],
                                "corrected": match.replacements[0],
                                "explanation": match.message,
                                "rule": match.ruleId
                            })
                    logger.info(f"Processed with LanguageTool fallback, found {len(corrections)} corrections.")
                else:
                    logger.warning("LanguageTool not available for fallback after JSON parsing error.")
            except Exception as e:  # Catch other potential errors from Gemini processing
                logger.error(f"An unexpected error occurred while processing Gemini response: {str(e)}")
                logger.error(traceback.format_exc())
                if lang_tool:  # Fallback for other errors
                    logger.info("Falling back to LanguageTool due to an unexpected error with Gemini.")
                    matches = lang_tool.check(text_to_check)
                    for match in matches:
                        if match.replacements:
                            corrections.append({
                                "original": text_to_check[match.offset:match.offset+match.errorLength],
                                "corrected": match.replacements[0],
                                "explanation": match.message,
                                "rule": match.ruleId
                            })
                    logger.info(f"Processed with LanguageTool fallback, found {len(corrections)} corrections.")
                else:
                    logger.warning("LanguageTool not available for fallback after unexpected Gemini error.")

        except exceptions.GoogleAPIError as e:  # This might need to be a more general google.api_core.exceptions.GoogleAPIError or specific genai exception
            logger.error(f"Gemini API Error: {str(e)}")
            logger.error(traceback.format_exc())
            # Fallback to LanguageTool if Gemini API fails
            if lang_tool:
                logger.info("Falling back to LanguageTool due to Gemini API error.")
                matches = lang_tool.check(text_to_check)
                for match in matches:
                    if match.replacements:
                        corrections.append({
                            "original": text_to_check[match.offset:match.offset+match.errorLength],
                            "corrected": match.replacements[0],
                            "explanation": match.message,
                            "rule": match.ruleId
                        })
                logger.info(f"Processed with LanguageTool fallback, found {len(corrections)} corrections.")
            else:
                logger.warning("LanguageTool not available for fallback after Gemini API error.")
        except Exception as e:
            logger.error(f"Unexpected error during Gemini grammar check: {str(e)}")
            logger.error(traceback.format_exc())
            # Fallback for other unexpected errors
            if lang_tool:
                logger.info("Falling back to LanguageTool due to an unexpected error during Gemini call.")
                matches = lang_tool.check(text_to_check)
                for match in matches:
                    if match.replacements:
                        corrections.append({
                            "original": text_to_check[match.offset:match.offset+match.errorLength],
                            "corrected": match.replacements[0],
                            "explanation": match.message,
                            "rule": match.ruleId
                        })
                logger.info(f"Processed with LanguageTool fallback, found {len(corrections)} corrections.")
            else:
                logger.warning("LanguageTool not available for fallback after unexpected error.")

    # If Gemini is not available or failed, and LanguageTool is available, use it
    elif lang_tool:
        logger.info("Using LanguageTool for grammar check (Gemini not available or failed).")
        try:
            matches = lang_tool.check(text_to_check)
            for match in matches:
                if match.replacements:  # Only add if there are suggestions
                    corrections.append({
                        "original": text_to_check[match.offset:match.offset+match.errorLength],
                        "corrected": match.replacements[0],
                        "explanation": match.message,
                        "rule": match.ruleId
                    })
            logger.info(f"Processed with LanguageTool, found {len(corrections)} corrections.")
        except Exception as e:
            logger.error(f"Error during LanguageTool grammar check: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": "Error processing with LanguageTool"}), 500
    else:
        logger.warning("No grammar check tool (Gemini or LanguageTool) is available.")
        return jsonify({"error": "Grammar check service not available"}), 503

    return jsonify(corrections)


@app.route('/api/summarize_concept', methods=['POST'])
@limiter.limit("5 per minute") # Example: 5 requests per minute
@login_required # Protect this endpoint
def summarize_concept_api():
    user_id = session.get('user_id') # Get current user
    logger.info(f"User {user_id} requesting /api/summarize_concept")
    if not gemini_available or gemini_model is None:
        logger.error("Gemini API not available for summarization.")
        return jsonify({'error': 'Summarization service unavailable due to Gemini API issue'}), 503

    try:
        data = request.get_json()
        concept_text = data.get('text') # Changed 'concept' to 'text'
        target_audience = data.get('audience', 'general') # Default to general audience
        compression_level = data.get('level', 'medium')  # Default to medium

        if not concept_text: # Changed 'concept' to 'concept_text'
            return jsonify({'error': 'No text provided for summarization'}), 400

        # Add to history
        add_user_history(user_id, 'summarize_concept', {'concept_length': len(concept_text), 'audience': target_audience, 'level': compression_level}) # Changed 'concept' to 'concept_text'

        # Tailor the prompt based on compression level
        if compression_level == 'high':
            prompt = f"""Summarize the following concept text concisely for a {target_audience} audience. Identify up to 5 key concepts. Suggest 3-4 focus points for learning and 3-4 related topics.
            Concept: "{concept_text}"
            Format your response as a JSON object with keys "summary", "keyConcepts" (list of strings), "learningEnhancement" (an object with "focusPoints" and "suggestedRelatedTopics" as lists of strings).
            Ensure the summary is very short and highly compressed.
            """
        elif compression_level == 'low':
            prompt = f"""Provide a detailed summary of the following concept text for a {target_audience} audience. Identify 7-10 key concepts. Suggest 5-6 focus points for learning and 5-6 related topics.
            Concept: "{concept_text}"
            Format your response as a JSON object with keys "summary", "keyConcepts" (list of strings), "learningEnhancement" (an object with "focusPoints" and "suggestedRelatedTopics" as lists of strings).
            Ensure the summary is comprehensive and less compressed.
            """
        else:  # Medium compression
            prompt = f"""Summarize the following concept text for a {target_audience} audience. Identify 5-7 key concepts. Suggest 4-5 focus points for learning and 4-5 related topics.
            Concept: "{concept_text}"
            Format your response as a JSON object with keys "summary", "keyConcepts" (list of strings), "learningEnhancement" (an object with "focusPoints" and "suggestedRelatedTopics" as lists of strings).
            The summary should be balanced in detail.
            """

        logger.info(f"Generating summary with Gemini. Compression: {compression_level}. Concept length: {len(concept_text)}")
        response = gemini_model.generate_content(prompt)

        # Attempt to parse the response as JSON
        try:
            # It's common for the API to return markdown with a JSON block.
            # We need to extract the JSON part.
            response_text = response.text
            # Find the start and end of the JSON block
            json_start_index = response_text.find('{')
            json_end_index = response_text.rfind('}') + 1

            if json_start_index != -1 and json_end_index != -1:
                json_string = response_text[json_start_index:json_end_index]
                summary_data = json.loads(json_string)
                logger.info("Successfully parsed Gemini response as JSON.")
            else:
                logger.error(f"Could not find JSON in Gemini response: {response_text}")
                # Fallback: try to create a basic summary if JSON parsing fails
                summary_data = {
                    "summary": response_text, # Use the whole text as summary
                    "keyConcepts": ["Could not extract key concepts"],
                    "learningEnhancement": {
                        "focusPoints": ["Unable to determine focus points"],
                        "suggestedRelatedTopics": ["Unable to determine related topics"]
                    }
                }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {str(e)}. Response text: {response.text}")
            # Fallback if JSON parsing fails
            summary_data = {
                "summary": response.text, # Use the whole text as summary
                "keyConcepts": ["Failed to parse key concepts from model output"],
                "learningEnhancement": {
                    "focusPoints": ["Failed to parse focus points"],
                    "suggestedRelatedTopics": ["Failed to parse related topics"]
                }
            }
        except Exception as e: # Catch other potential errors with the response object
            logger.error(f"Error processing Gemini response: {str(e)}. Response: {response}")
            return jsonify({'error': f'Error processing Gemini response: {str(e)}'}), 500


        return jsonify(summary_data)

    except Exception as e:
        logger.error(f"Error in summarize_concept_api: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500
