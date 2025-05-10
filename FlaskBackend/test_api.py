import requests
import json
import base64
import os
import sys

def test_texttospeech_api():
    print("Starting text-to-speech API test...")
    url = "http://localhost:5000/api/texttospeech"
    print(f"Using API endpoint: {url}")
    
    test_texts = [
        "Hello world",
        "Bonjour le monde",
        "Hola mundo",
        "Hello world. Bonjour le monde. Hola mundo."
    ]
    print(f"Will test {len(test_texts)} phrases")
    
    for idx, text in enumerate(test_texts):
        print(f"\nTest {idx+1}: Converting '{text}'")
        
        try:
            # Call the API
            response = requests.post(
                url,
                json={"text": text},
                headers={"Content-Type": "application/json"}
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                
                if "audio_base64" in data:
                    audio_base64 = data["audio_base64"]
                    
                    # Decode the base64 audio data
                    audio_data = base64.b64decode(audio_base64)
                    
                    # Save the audio to a file
                    output_file = f"test_output_{idx+1}.mp3"
                    with open(output_file, "wb") as f:
                        f.write(audio_data)
                    
                    print(f"✅ Success! Audio saved to {output_file}")
                    print(f"   Audio size: {len(audio_data) / 1024:.2f} KB")
                else:
                    print(f"❌ Error: Response does not contain audio_base64 field")
                    print(f"   Response: {data}")
            else:
                print(f"❌ Error: Status code {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error message: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   Response: {response.text}")
                    
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_texttospeech_api()
