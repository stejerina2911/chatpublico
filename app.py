import streamlit as st
import os
from utils import get_answer, speech_to_text, text_to_speech
from audio_recorder_streamlit import audio_recorder
import time
import base64
from io import BytesIO

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "interview_started" not in st.session_state:
        st.session_state.interview_started = False
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "cv_text" not in st.session_state:
        st.session_state.cv_text = ""
    if "interview_finished" not in st.session_state:
        st.session_state.interview_finished = False
    if "company_info" not in st.session_state:
        st.session_state.company_info = ""
    if "role_description" not in st.session_state:
        st.session_state.role_description = ""

initialize_session_state()

st.title("Entrevistador Virtual 🤖")

def autoplay_audio_bytes(audio_bytes, autoplay=True):
    b64 = base64.b64encode(audio_bytes).decode()
    if autoplay:
        md = f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
    else:
        md = f"""
        <audio controls>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
    st.markdown(md, unsafe_allow_html=True)

if not st.session_state.company_info:
    st.write("Por favor, proporciona la siguiente información antes de comenzar la entrevista.")
    company_info_input = st.text_area("Información de la empresa", height=150)
    role_description_input = st.text_area("Descripción del puesto", height=150)
    if st.button("Enviar información de la empresa y del puesto"):
        if company_info_input.strip() and role_description_input.strip():
            st.session_state.company_info = company_info_input
            st.session_state.role_description = role_description_input
            st.success("Información de la empresa y del puesto recibida.")
            st.experimental_rerun()
        else:
            st.error("Por favor, proporciona la información de la empresa y la descripción del puesto.")
elif not st.session_state.cv_text:
    st.write("Por favor, copia y pega tu CV en el siguiente cuadro de texto:")
    cv_text_input = st.text_area("Ingresa tu CV aquí", height=300)
    if st.button("Enviar CV"):
        if cv_text_input.strip():
            st.session_state.cv_text = cv_text_input
            st.session_state.interview_started = True
            st.session_state.start_time = time.time()
            st.success("CV recibido. Comenzando la entrevista...")
            st.experimental_rerun()
        else:
            st.error("El CV no puede estar vacío.")
else:
    if not st.session_state.interview_finished:
        # Display previous messages
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if message["role"] == "assistant" and "audio_bytes" in message:
                    # Set autoplay to False for previous messages
                    autoplay_audio_bytes(message["audio_bytes"], autoplay=False)

        # If there are no messages yet, assistant starts the conversation
        if not st.session_state.messages:
            with st.chat_message("assistant"):
                with st.spinner("Pensando..."):
                    # Assistant initiates the conversation
                    initial_prompt = "¡Hola! Gracias por enviar tu CV. ¿Podrías contarme un poco más sobre tu experiencia más reciente?"
                    st.write(initial_prompt)
                    # Generate audio
                    audio_bytes = text_to_speech(initial_prompt)
                    autoplay_audio_bytes(audio_bytes, autoplay=True)
                    st.session_state.messages.append({"role": "assistant", "content": initial_prompt, "audio_bytes": audio_bytes})

        # Audio recorder in the main area
        audio_bytes_user = audio_recorder(pause_threshold=3.0)
        if audio_bytes_user:
            # Process the audio bytes
            with st.spinner("Transcribiendo..."):
                transcript = speech_to_text(audio_bytes_user)
                if transcript:
                    st.session_state.messages.append({"role": "user", "content": transcript})
                    with st.chat_message("user"):
                        st.write(transcript)

        # Check if 5 minutes have passed
        elapsed_time = time.time() - st.session_state.start_time
        if elapsed_time >= 300:
            st.session_state.interview_finished = True
            # Generate the verdict
            with st.chat_message("assistant"):
                with st.spinner("Analizando las respuestas..."):
                    final_response = get_answer(
                        st.session_state.messages + [{"role": "assistant", "content": "Por favor, proporciona un veredicto sobre si el candidato pasa a la siguiente ronda o no, basándote en la entrevista."}],
                        st.session_state.cv_text,
                        st.session_state.company_info,
                        st.session_state.role_description
                    )
                st.write(final_response)
                # Generate audio
                audio_bytes = text_to_speech(final_response)
                autoplay_audio_bytes(audio_bytes, autoplay=True)
                st.session_state.messages.append({"role": "assistant", "content": final_response, "audio_bytes": audio_bytes})
        else:
            if st.session_state.messages and st.session_state.messages[-1]["role"] != "assistant":
                with st.chat_message("assistant"):
                    with st.spinner("Pensando..."):
                        response = get_answer(
                            st.session_state.messages,
                            st.session_state.cv_text,
                            st.session_state.company_info,
                            st.session_state.role_description
                        )
                    st.write(response)
                    # Generate audio
                    audio_bytes = text_to_speech(response)
                    autoplay_audio_bytes(audio_bytes, autoplay=True)
                    st.session_state.messages.append({"role": "assistant", "content": response, "audio_bytes": audio_bytes})
    else:
        st.write("La entrevista ha finalizado. Gracias por tu tiempo.")
