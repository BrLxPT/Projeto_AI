from core import TaskEngine
import speech_recognition as sr
from ollama_helper import OllamaAPI
from flask import Flask, request, jsonify
import re
import json
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
engine = TaskEngine()
ollama = OllamaAPI(timeout=120)  # Increased timeout to 120 seconds

def check_ollama_connection():
    """Check if Ollama server is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Ollama connection check failed: {str(e)}")
        return False

def extract_email(text):
    """Extract first email found in text"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def process_user_input(user_input):
    """Process user input for email commands"""
    try:
        recipient = extract_email(user_input)
        if not recipient:
            return {"status": "error", "message": "No valid email found in command"}
        
        prompt = f"""
        Extract email subject and body from the following text to send to {recipient}.
        Return ONLY valid JSON in this format:
        {{
            "action": "send_email",
            "parameters": {{
                "to": "{recipient}",
                "subject": "extracted subject here",
                "body": "extracted message body here"
            }}
        }}
        
        Text: {user_input}
        """
        
        logger.info(f"Sending prompt to Ollama: {prompt[:200]}...")
        ollama_response = ollama.generate(
            model="llama3",
            prompt=prompt,
            temperature=0.7,
            format="json",
            max_retries=3
        )
        
        if isinstance(ollama_response, dict) and ollama_response.get("status") == "error":
            return ollama_response
            
        response_text = ollama_response.get("response", str(ollama_response))
        
        # Try to extract JSON from response
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return {"status": "error", "message": "No valid JSON found in response"}
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"JSON decode error: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Error processing user input: {str(e)}")
        return {"status": "error", "message": f"Processing error: {str(e)}"}

def voice_input():
    """Capture voice input using microphone"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = r.listen(source, timeout=5)
            return r.recognize_google(audio, language="pt-BR")
        except sr.WaitTimeoutError:
            print("No speech detected")
            return ""
        except Exception as e:
            print(f"Voice recognition error: {str(e)}")
            return ""

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """API endpoint for chat interactions"""
    try:
        data = request.get_json()
        if not data or "mensagem" not in data:
            return jsonify({"error": "Invalid request format"}), 400
            
        response = ollama.generate(
            model="llama3",
            prompt=data["mensagem"],
            temperature=0.7
        )
        return jsonify({"response": response.get("response", response)})
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if not check_ollama_connection():
        print("Error: Ollama server not running. Please start with:")
        print("$ ollama serve")
        exit(1)

    while True:
        mode = input("Mode (voice/text/server): ").lower()
        
        if mode == "server":
            print("Starting Flask server...")
            app.run(host='0.0.0.0', port=5000, debug=False)
            break
            
        elif mode == "voice":
            user_input = voice_input()
            if not user_input:
                print("Could not understand voice command")
                continue
            print(f"Command: {user_input}")
        else:
            user_input = input("Command: ")
        
        if user_input.lower() in ["exit", "quit", "sair"]:
            break
            
        command = process_user_input(user_input)
        if command.get("status") == "error":
            print(f"Error: {command['message']}")
            continue
            
        result = engine.execute_task(command)  # Agora aceita tanto string quanto dict
        print("Result:", result)