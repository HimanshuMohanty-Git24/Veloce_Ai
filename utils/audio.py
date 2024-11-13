import sounddevice as sd
import soundfile as sf
import numpy as np
from groq import Groq
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import os
from dotenv import load_dotenv

load_dotenv()

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AudioManager:
    def __init__(self):
        try:
            self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
            self.eleven_client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
            logger.info("AudioManager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AudioManager: {str(e)}")
            raise

    def record_audio(self, duration=5, sample_rate=16000):
        """Record audio from microphone"""
        try:
            logger.info("Starting audio recording...")
            recording = sd.rec(int(duration * sample_rate),
                             samplerate=sample_rate,
                             channels=1)
            sd.wait()
            logger.info("Audio recording completed")
            return recording, sample_rate
        except Exception as e:
            logger.error(f"Error during audio recording: {str(e)}")
            raise

    def save_audio(self, recording, sample_rate, filename="temp.wav"):
        """Save recorded audio to file"""
        try:
            logger.info(f"Saving audio to {filename}")
            sf.write(filename, recording, sample_rate)
            logger.info("Audio saved successfully")
            return filename
        except Exception as e:
            logger.error(f"Error saving audio: {str(e)}")
            raise

    def speech_to_text(self, audio_file):
        """Convert speech to text using Groq Whisper"""
        try:
            logger.info("Starting speech to text conversion")
            with open(audio_file, "rb") as file:
                transcript = self.groq_client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=file
                )
            logger.info("Speech to text conversion completed")
            return transcript.text
        except Exception as e:
            logger.error(f"Error in speech to text conversion: {str(e)}")
            raise

    def text_to_speech(self, text):
        """Convert text to speech using ElevenLabs"""
        audio = self.eleven_client.generate(
            text=text,
            voice="Daniel",
            model="eleven_multilingual_v2"
        )
        play(audio)