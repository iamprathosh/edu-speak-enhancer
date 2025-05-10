#!/usr/bin/env python
"""
Test script for language detection and text-to-speech functionality.

This script tests the language detection function from the Flask app
and generates audio files for multi-language phrases.
"""

import sys
import os
import io
import base64
import json
import requests
import traceback
from gtts import gTTS

# Configuration
API_URL = "http://localhost:5000"

# Test phrases
TEST_PHRASES = [
    "Hello bonjour hola guten tag",
    "I speak English, je parle français, y hablo español",
    "The quick brown fox jumps over the lazy dog",
    "Bonjour mes amis, comment allez-vous aujourd'hui?",
    "Hola amigos, ¿cómo están todos hoy?",
    "Guten Morgen, wie geht es dir heute?",
]

# Test the custom text-to-speech API
def test_custom_tts_api():
    """Test the custom TTS API with multi-language phrases."""
    print("\n=== Testing Custom TTS API ===")
    
    for i, phrase in enumerate(TEST_PHRASES, 1):
        print(f"\nPhrase {i}: '{phrase}'")
        
        try:
            print(f"Making API request to {API_URL}/api/texttospeech...")
            response = requests.post(
                f"{API_URL}/api/texttospeech",
                json={"text": phrase},
                timeout=30
            )
            
            print(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✓ API call successful!")
                
                # Process the response
                try:
                    data = response.json()
                    print(f"Response has the following keys: {list(data.keys())}")
                    
                    if "audio_base64" in data:
                        audio_base64 = data["audio_base64"]
                        print(f"Received base64 audio data, length: {len(audio_base64)}")
                        
                        # Check if base64 data is valid
                        try:
                            audio_data = base64.b64decode(audio_base64)
                            output_file = f"test_output_{i}.mp3"
                            
                            with open(output_file, "wb") as f:
                                f.write(audio_data)
                            
                            print(f"✓ Saved audio to {output_file} ({len(audio_data)} bytes)")
                        except Exception as e:
                            print(f"✗ Error decoding base64 data: {e}")
                    else:
                        print(f"✗ No audio_base64 key in response data")
                        print(f"Response content: {data}")
                except Exception as e:
                    print(f"✗ Error processing response data: {e}")
                    print(f"Response content: {response.text[:200]}...")
            else:
                print(f"✗ API call failed: Status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error response: {response.text[:200]}...")
        
        except Exception as e:
            print(f"✗ Exception occurred during API call: {e}")
            traceback.print_exc()

# Generate test audio files directly with gTTS for comparison
def generate_comparison_audio():
    """Generate audio files directly with gTTS for comparison."""
    print("\n=== Generating Comparison Audio with gTTS ===")
    
    for i, phrase in enumerate(TEST_PHRASES, 1):
        print(f"\nPhrase {i}: '{phrase}'")
        
        try:
            # Without language detection (using 'en' for all)
            tts_en = gTTS(text=phrase, lang='en', slow=False)
            output_file_en = f"direct_en_{i}.mp3"
            tts_en.save(output_file_en)
            print(f"✓ Saved English-only audio to {output_file_en}")
            
        except Exception as e:
            print(f"✗ Exception occurred: {e}")
            traceback.print_exc()

# Check if the Flask server is running
def check_server():
    """Check if the Flask server is running."""
    print("Checking if Flask server is running...")
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Flask server is running. Health check response: {response.json()}")
            return True
        else:
            print(f"✗ Flask server returned unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Could not connect to Flask server: {e}")
        return False

if __name__ == "__main__":
    print("=== Language Detection & TTS Test Script ===")
    
    # Check if server is running
    if check_server():
        # Test custom TTS API
        test_custom_tts_api()
        
        # Optionally generate comparison audio
        generate_comparison_audio()
    else:
        print("\n⚠️ Cannot proceed with tests because the Flask server is not running")
        print("   Make sure the Flask app is running at", API_URL)
