import openai
import os
from dotenv import load_dotenv
from gtts import gTTS
from io import BytesIO

load_dotenv()

# Load the OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_answer(messages, cv_text, company_info, role_description):
    system_message = [
        {
            "role": "system",
            "content": (
                f"Eres un entrevistador de recursos humanos para la siguiente empresa:\n{company_info}\n"
                f"Estás entrevistando para el siguiente puesto:\n{role_description}\n"
                "Utiliza el CV proporcionado por el candidato para hacer preguntas relevantes. "
                "Después de 5 minutos de entrevista, debes dar un veredicto sobre si el candidato pasa a la siguiente ronda o no, "
                "basándote en su idoneidad para el puesto y la cultura de la empresa."
            )
        },
        {
            "role": "user",
            "content": f"Este es mi CV:\n{cv_text}"
        }
    ]
    # Sanitizar las messages para incluir sólo 'role' y 'content'
    sanitized_messages = []
    for msg in messages:
        sanitized_messages.append({
            'role': msg['role'],
            'content': msg['content']
        })
    messages = system_message + sanitized_messages
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message.content

def speech_to_text(audio_data):
    import io
    audio_file = io.BytesIO(audio_data)
    audio_file.name = 'audio.mp3'  # Whisper necesita una extensión de archivo
    transcript = openai.Audio.transcribe(
        "whisper-1",
        audio_file
    )
    return transcript['text']

def text_to_speech(input_text):
    tts = gTTS(text=input_text, lang='es')
    audio_data = BytesIO()
    tts.write_to_fp(audio_data)
    audio_data.seek(0)
    return audio_data.read()
