import streamlit as st
from database.db_setup import initialize_database, create_database_connection
from utils.audio import AudioManager
from utils.weather import WeatherService
from groq import Groq
import os
from dotenv import load_dotenv
import json
import plotly.graph_objects as go
import logging
import base64
from PIL import Image
import io

# Load environment variables and setup logging
load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize services
audio_manager = AudioManager()
weather_service = WeatherService()
groq_client = Groq()

# System prompt
SYSTEM_PROMPT = """You are Veloce AI, Volkswagen's intelligent vehicle assistant. You help users with:
- Vehicle information and status
- Maintenance scheduling and alerts
- Weather updates and driving conditions
- Voice commands for vehicle controls
- Navigation assistance
- Battery management for electric vehicles

Always maintain a helpful, professional tone focusing on Volkswagen vehicles and their features. 
If asked about non-Volkswagen vehicles, politely redirect to VW equivalents."""

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    if 'current_image' not in st.session_state:
        st.session_state.current_image = None

def display_vehicle_status(vehicle_data):
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Battery Level", f"{vehicle_data['battery_level']}%")
        st.metric("Engine Oil Life", f"{vehicle_data['engine_oil_life']}%")
        
    with col2:
        tire_pressure = json.loads(vehicle_data['tire_pressure'])
        fig = go.Figure(data=[go.Scatter(
            x=['FL', 'FR', 'RL', 'RR'],
            y=[tire_pressure['FL'], tire_pressure['FR'], 
               tire_pressure['RL'], tire_pressure['RR']],
            mode='lines+markers'
        )])
        fig.update_layout(title="Tire Pressure (PSI)")
        st.plotly_chart(fig)

def process_ai_response(messages):
    if st.session_state.current_image:
        # Remove system message when using images
        messages_without_system = [msg for msg in messages if msg["role"] != "system"]
        # Filter out any old image messages
        clean_messages = []
        for msg in messages_without_system:
            if isinstance(msg["content"], list):
                # Keep only the most recent image
                filtered_content = [c for c in msg["content"] if c["type"] == "text" or 
                                  (c["type"] == "image_url" and 
                                   c["image_url"]["url"].endswith(st.session_state.current_image))]
                if filtered_content:
                    msg["content"] = filtered_content
                    clean_messages.append(msg)
            else:
                clean_messages.append(msg)
                
        model = "llama-3.2-11b-vision-preview"
        response = groq_client.chat.completions.create(
            model=model,
            messages=clean_messages,
            temperature=0.7,
            max_tokens=1024
        )
    else:
        # Reset to text-only mode
        text_only_messages = []
        for msg in messages:
            if isinstance(msg["content"], list):
                # Extract only text content
                text_content = " ".join([c["text"] for c in msg["content"] if c["type"] == "text"])
                if text_content:
                    text_only_messages.append({"role": msg["role"], "content": text_content})
            else:
                text_only_messages.append(msg)
                
        model = "llama3-70b-8192"
        response = groq_client.chat.completions.create(
            model=model,
            messages=text_only_messages,
            temperature=0.7,
            max_tokens=1024
        )
    return response.choices[0].message.content

def main():
    st.set_page_config(page_title="Veloce AI - Volkswagen Assistant",
                      page_icon="🚗",
                      layout="wide")
    
    initialize_session_state()
    
    st.title("Veloce AI - Your Volkswagen Assistant")
    
    # Sidebar
    st.sidebar.title("Vehicle Selection")
    conn = create_database_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, model, year FROM vehicles")
    vehicles = cursor.fetchall()
    
    selected_vehicle = st.sidebar.selectbox(
        "Select Your Vehicle",
        options=vehicles,
        format_func=lambda x: f"{x['year']} {x['model']}"
    )
    
    # Image upload section
    st.sidebar.markdown("### Image Upload")
    uploaded_file = st.sidebar.file_uploader("Upload an image to ask questions about", 
                                          type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.sidebar.image(image, caption="Uploaded Image", use_container_width=True)
        st.session_state.current_image = encode_image(uploaded_file.getvalue())
    if st.session_state.current_image and st.sidebar.button("Clear Image"):
        st.session_state.current_image = None
        # Clean up message history
        text_only_messages = []
        for msg in st.session_state.messages:
            if isinstance(msg["content"], list):
                text_content = " ".join([c["text"] for c in msg["content"] if c["type"] == "text"])
                if text_content:
                    text_only_messages.append({"role": msg["role"], "content": text_content})
            else:
                text_only_messages.append(msg)
        st.session_state.messages = text_only_messages
        st.rerun()
    if selected_vehicle:
        cursor.execute("SELECT * FROM vehicles WHERE id = %s", 
                      (selected_vehicle['id'],))
        vehicle_data = cursor.fetchone()
        display_vehicle_status(vehicle_data)
    
    # Chat interface
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                if isinstance(message["content"], list):
                    for content in message["content"]:
                        if content["type"] == "text":
                            st.write(content["text"])
                        elif content["type"] == "image_url":
                            st.image(content["image_url"]["url"])
                else:
                    st.write(message["content"])
    
    # Voice input button
    if st.button("🎤 Voice Input"):
        try:
            with st.spinner("Listening..."):
                logger.info("Starting voice recording process")
                recording, sample_rate = audio_manager.record_audio()
                logger.info(f"Recording completed, sample rate: {sample_rate}")
                
                audio_file = audio_manager.save_audio(recording, sample_rate)
                logger.info(f"Audio saved to file: {audio_file}")
                
                user_input = audio_manager.speech_to_text(audio_file)
                logger.info(f"Transcribed text: {user_input}")
                
                if user_input:
                    message_content = [{"type": "text", "text": user_input}]
                    if st.session_state.current_image:
                        message_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{st.session_state.current_image}"
                            }
                        })
                    
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": message_content
                    })
                    
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            assistant_response = process_ai_response(
                                st.session_state.messages
                            )
                            st.write(assistant_response)
                            audio_manager.text_to_speech(assistant_response)
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                else:
                    st.error("No speech detected. Please try again.")
                    logger.warning("No speech detected in recording")
                    
        except Exception as e:
            error_msg = f"Error processing voice input: {str(e)}"
            st.error(error_msg)
            logger.error(error_msg)
    
    # Text input
    if user_input := st.chat_input():
        message_content = [{"type": "text", "text": user_input}]
        if st.session_state.current_image:
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{st.session_state.current_image}"
                }
            })
        
        st.session_state.messages.append({
            "role": "user",
            "content": message_content
        })
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                assistant_response = process_ai_response(st.session_state.messages)
                st.write(assistant_response)
                audio_manager.text_to_speech(assistant_response)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_response
        })

if __name__ == "__main__":
    main()