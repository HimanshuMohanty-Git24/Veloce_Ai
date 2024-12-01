import requests
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        if not self.api_key:
            raise ValueError("OPENWEATHERMAP_API_KEY not found in environment variables")
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

    def get_weather(self, city: str) -> Optional[Dict[str, Union[float, str]]]:
        """
        Get weather information for a city
        
        Args:
            city (str): Name of the city
            
        Returns:
            Optional[Dict[str, Union[float, str]]]: Weather data or None if request fails
        """
        if not city or not isinstance(city, str):
            logger.error("Invalid city parameter")
            return None

        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'wind_speed': data['wind']['speed']
            }
        except requests.RequestException as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing weather data: {str(e)}")
            return None