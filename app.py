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
import requests
from datetime import datetime
from streamlit_javascript import st_javascript
import geocoder
from utils.music import MusicManager

# Load environment variables and setup logging
load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize services
audio_manager = AudioManager()
weather_service = WeatherService()
groq_client = Groq()
music_manager = MusicManager()

def get_current_location():
    """Get the user's current location based on IP address."""
    g = geocoder.ip('me')
    if g.ok:
        return {
            'latitude': g.latlng[0],
            'longitude': g.latlng[1]
        }
    else:
        return None

def reverse_geocode(latitude, longitude):
    """Get the city name from latitude and longitude using reverse geocoding."""
    url = 'https://nominatim.openstreetmap.org/reverse'
    params = {
        'format': 'json',
        'lat': latitude,
        'lon': longitude,
        'zoom': 10,
        'addressdetails': 1
    }
    headers = {
        'User-Agent': 'VeloceAI/1.0'
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        address = data.get('address', {})
        
        # Get city name and clean it
        city = address.get('city', '')
        if city:
            # Extract just the first part before any special characters
            city = city.split()[0].split(',')[0].strip()
        
        if not city:
            # Try other fields if city is not found
            for key in ['town', 'village', 'suburb', 'state']:
                value = address.get(key, '')
                if value:
                    # Take just the first word
                    city = value.split()[0]
                    break
        
        return city if city else None
    except Exception as e:
        logger.error(f"Error in reverse geocoding: {str(e)}")
        return None

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
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
    # Extract the last user message more reliably
    last_message = messages[-1]["content"]
    last_text = ""
    
    # Add debug logging
    logger.debug(f"Processing message: {last_message}")
    
    # Handle different message formats
    if isinstance(last_message, list):
        last_text = " ".join([c["text"] for c in last_message if c["type"] == "text"])
    else:
        last_text = str(last_message)
    
    logger.debug(f"Extracted text: {last_text}")
    
    # Check for music commands with more flexible matching
    if any(word in last_text.lower() for word in ["play", "music", "song"]):
        logger.info("Music command detected")
        
        # Extract song name more robustly
        query = last_text.lower()
        if "play" in query:
            query = query.split("play", 1)[1].strip()
        
        logger.info(f"Searching for song: {query}")
        
        # Try to play the song
        song_url = music_manager.search_song(query)
        if song_url:
            logger.info(f"Found song URL: {song_url}")
            if music_manager.play_music(song_url):
                return f"🎵 Now playing: {query}"
            return f"Found the song but couldn't play {query}"
        return f"Sorry, I couldn't find '{query}' on YouTube Music"

    # Continue with existing image processing
    if st.session_state.current_image:
        messages_without_system = [msg for msg in messages if msg["role"] != "system"]
        clean_messages = []
        for msg in messages_without_system:
            if isinstance(msg["content"], list):
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
        # Text-only mode (existing code)
        text_only_messages = []
        for msg in messages:
            if isinstance(msg["content"], list):
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
    # Option 1: Include 'vin' in the selection query
    # cursor.execute("SELECT id, model, year, vin FROM vehicles")
    # Option 2: Keep the original query
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
        st.sidebar.image(image, caption="Uploaded Image", use_column_width=True)
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
        st.experimental_rerun()
    
    if selected_vehicle:
        cursor.execute("SELECT * FROM vehicles WHERE id = %s", 
                      (selected_vehicle['id'],))
        vehicle_data = cursor.fetchone()
        display_vehicle_status(vehicle_data)
        
        # Fetch necessary variables for system prompt
        current_vehicle_id = vehicle_data['id']
        vehicle_model = vehicle_data['model']
        vehicle_year = vehicle_data['year']
        vehicle_vin = vehicle_data['vin']  # Get 'vin' from 'vehicle_data'
        mileage = vehicle_data['current_mileage']
        battery_percentage = vehicle_data['battery_level']
        tire_pressure = json.loads(vehicle_data['tire_pressure'])
        front_left_psi = tire_pressure['FL']
        front_right_psi = tire_pressure['FR']
        rear_left_psi = tire_pressure['RL']
        rear_right_psi = tire_pressure['RR']
        oil_life_percentage = vehicle_data['engine_oil_life']
        service_date = vehicle_data['last_service_date']

        # Get user's current location
        user_location = get_current_location()
        if user_location:
            latitude = user_location['latitude']
            longitude = user_location['longitude'] 
            current_location = f"{latitude}, {longitude}"
            current_city = reverse_geocode(latitude, longitude)
            if current_city:
                current_city = current_city.split()[0]  # Take only first word
        else:
            current_location = "Unknown"
            current_city = "Unknown"
        
        # Get weather data
        weather_data = weather_service.get_weather(current_city)
        if weather_data:
            current_temp = weather_data['temperature']
            humidity_percentage = weather_data['humidity']
            weather_description = weather_data['description']
            wind_speed = weather_data['wind_speed']
        else:
            current_temp = 0
            humidity_percentage = 0
            weather_description = "Unknown"
            wind_speed = 0
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # System prompt with actual variables
        SYSTEM_PROMPT = f"""You are Veloce AI, Volkswagen's intelligent vehicle assistant. You have access to the following real-time data and context:

CONTEXT_VARIABLES = {{
    "selected_vehicle": {{
        "id": {current_vehicle_id},
        "model": "{vehicle_model}",
        "year": {vehicle_year},
        "vin": "{vehicle_vin}",
        "current_mileage": {mileage},
        "battery_level": {battery_percentage},
        "tire_pressure": {{
            "FL": {front_left_psi},
            "FR": {front_right_psi},
            "RL": {rear_left_psi},
            "RR": {rear_right_psi}
        }},
        "engine_oil_life": {oil_life_percentage},
        "last_service_date": "{service_date}"
    }},
    "weather_data": {{
        "city": "{current_city}",
        "temperature": {current_temp},
        "humidity": {humidity_percentage},
        "description": "{weather_description}",
        "wind_speed": {wind_speed}
    }},
    "time": "{current_time}",
    "location": "{current_location}"
}}

DATABASE_ACCESS = {{
    "vehicles": ["id", "model", "year", "vin", "current_mileage", "battery_level", "tire_pressure", "engine_oil_life", "last_service_date"],
    "maintenance_records": ["id", "vehicle_id", "service_date", "service_type", "mileage", "description"]
}}

API_SERVICES = {{
    "weather": "OpenWeatherMap for real-time weather data",
    "voice": "ElevenLabs for text-to-speech",
    "llm": "Groq for natural language processing",
    "music": "YTMusic API for music playback and search"
}}

CAPABILITIES:
1. Vehicle Status:
   - Access real-time vehicle metrics from DATABASE_ACCESS
   - Monitor battery levels for EVs (ID.4 series)
   - Track tire pressure across all wheels
   - Check engine oil life and maintenance status

2. Weather & Navigation:
   - Pull current weather from CONTEXT_VARIABLES['weather_data']
   - Provide weather-based driving recommendations(also say the city name like "today the weather in <City-Name> is...")
   - Access location data for navigation assistance(Just say the city name not the coordinates)

3. Maintenance:
   - Query maintenance_records table for service history
   - Schedule and recommend maintenance based on vehicle data
   - Alert on critical maintenance needs

4. Voice Commands:
   - Process natural language commands for vehicle control
   - Convert responses to speech using ElevenLabs API

5. Music Playback:
   - Search and play music from YouTube Music
   - Handle voice/text commands for music control
   - Support song requests by name/artist
   - Play music through Streamlit's audio player

RESPONSE GUIDELINES:
- Only use data available in CONTEXT_VARIABLES or DATABASE_ACCESS
- Indicate when data is not available or needs refresh
- Format numbers with appropriate units (%, PSI, miles, °C)
- Prioritize safety-critical information
- Maintain professional Volkswagen brand voice

If asked about non-VW vehicles, politely redirect to VW equivalents."""

        # Update the system prompt in the message history
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ] + [msg for msg in st.session_state.messages if msg["role"] != "system"]
    
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