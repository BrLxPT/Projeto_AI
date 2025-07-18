from core import TaskEngine
import speech_recognition as sr
from ollama_helper import OllamaAPI
from flask import Flask, request, jsonify

app = Flask(__name__)
engine = TaskEngine()
ollama = OllamaAPI()

def voice_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Ouvindo...")
        audio = r.listen(source)
    try:
        return r.recognize_google(audio, language="pt-BR")
    except:
        return ""

while True:
    mode = input("Modo (voz/texto): ").lower()
    
    if mode == "voz":
        user_input = voice_input()
        print(f"Comando: {user_input}")
    else:
        user_input = input("Comando: ")
    
    if user_input.lower() in ["sair", "exit"]:
        break
        
    result = engine.execute_task(user_input)
    print("Resultado:", result)

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json()
    resposta = ollama.generate(
        model="llama3",
        prompt=data["mensagem"],
        temperature=0.7
    )
    return jsonify({"resposta": resposta["response"]})
