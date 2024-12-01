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
load_dotenv()


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Initialize services
audio_manager = AudioManager()
weather_service = WeatherService()
groq_client = Groq()

# System prompt for the AI assistant
SYSTEM_PROMPT = """You are Veloce AI, Volkswagen's intelligent vehicle assistant. You help users with:
- Vehicle information and status
- Maintenance scheduling and alerts
- Weather updates and driving conditions
- Voice commands for vehicle controls
- Navigation assistance
- Battery management for electric vehicles

Always maintain a helpful, professional tone focusing on Volkswagen vehicles and their features. 
If asked about non-Volkswagen vehicles, politely redirect to VW equivalents."""

def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

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

def main():
    st.set_page_config(page_title="Veloce AI - Volkswagen Assistant",
                      page_icon="🚗",
                      layout="wide")
    
    initialize_session_state()
    
    st.title("Veloce AI - Your Volkswagen Assistant")
    
    # Sidebar for vehicle selection
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
    
    if selected_vehicle:
        cursor.execute("""
            SELECT * FROM vehicles WHERE id = %s
        """, (selected_vehicle['id'],))
        vehicle_data = cursor.fetchone()
        display_vehicle_status(vehicle_data)
    
    # Main chat interface
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
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
                    # Add user message to chat
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    logger.info("Added user message to session state")
                    
                    # Get AI response
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            response = groq_client.chat.completions.create(
                                model="llama3-70b-8192",
                                messages=st.session_state.messages,
                                temperature=0.7,
                                max_tokens=1024
                            )
                            assistant_response = response.choices[0].message.content
                            st.write(assistant_response)
                            audio_manager.text_to_speech(assistant_response)
                            
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    logger.info("Added assistant response to session state")
                else:
                    st.error("No speech detected. Please try again.")
                    logger.warning("No speech detected in recording")
                    
        except Exception as e:
            error_msg = f"Error processing voice input: {str(e)}"
            st.error(error_msg)
            logger.error(error_msg)
    
    # Text input
    if user_input := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = groq_client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=st.session_state.messages,
                    temperature=0.7,
                    max_tokens=1024
                )
                assistant_response = response.choices[0].message.content
                st.write(assistant_response)
                audio_manager.text_to_speech(assistant_response)
                
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

if __name__ == "__main__":
    main()