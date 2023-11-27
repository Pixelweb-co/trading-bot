import speech_recognition as sr
import requests
import pyttsx3

# Configuración de la API de ChatGPT
GPT_API_URL = "https://api.openai.com/v1/engines/davinci-codex/completions"
GPT_API_KEY = "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"

# Configuración de la biblioteca de síntesis de voz
engine = pyttsx3.init()

# Función para convertir el texto en voz y reproducirlo
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Función para enviar una solicitud a la API de ChatGPT
def chat_gpt(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GPT_API_KEY}"
    }
    data = {
        "prompt": prompt,
        "max_tokens": 50
    }
    response = requests.post(GPT_API_URL, headers=headers, json=data)
    response_json = response.json()
    return response_json["choices"][0]["text"].strip()

# Función principal para el reconocimiento de voz y el chat con GPT
def voice_chat():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        print("Di algo...")
        audio = r.listen(source)

    try:
        print("Transcribiendo...")
        text = r.recognize_google(audio)
        print("Usuario:", text)

        response = chat_gpt(text)
        print("GPT:", response)

        print("Convirtiendo a voz...")
        speak(response)
    except sr.UnknownValueError:
        print("No se pudo entender el audio.")
    except sr.RequestError as e:
        print("Error al solicitar resultados desde el servicio de reconocimiento de voz; {0}".format(e))

# Ejecutar la función principal
voice_chat()
