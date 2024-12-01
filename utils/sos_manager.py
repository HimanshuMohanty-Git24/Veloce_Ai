import requests
from math import radians, sin, cos, sqrt, atan2
import logging
from twilio.rest import Client
import os

logger = logging.getLogger(__name__)

class SOSManager:
    def __init__(self, db_connection):
        self.conn = db_connection
        self.twilio_client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )

    def get_nearest_police_station(self, latitude, longitude):
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM police_stations")
        stations = cursor.fetchall()
        
        nearest = None
        min_distance = float('inf')
        
        for station in stations:
            distance = self._calculate_distance(
                latitude, longitude,
                float(station['latitude']), 
                float(station['longitude'])
            )
            if distance < min_distance:
                min_distance = distance
                nearest = station
        
        return nearest

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

    def send_sos_messages(self, location, situation="Emergency! Need immediate assistance!"):
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM emergency_contacts")
        contacts = cursor.fetchall()
        
        message_body = (
            f"EMERGENCY SOS ALERT!\n"
            f"Situation: {situation}\n"
            f"Location: {location}\n"
            f"Google Maps Link: https://www.google.com/maps?q={location}"
        )
        
        sent_count = 0
        for contact in contacts:
            try:
                message = self.twilio_client.messages.create(
                    body=message_body,
                    from_=os.getenv('TWILIO_PHONE_NUMBER'),
                    to=contact['phone_number']
                )
                sent_count += 1
                logger.info(f"SOS message sent to {contact['name']}")
            except Exception as e:
                logger.error(f"Failed to send SOS to {contact['name']}: {str(e)}")
        
        return sent_count

    def handle_sos_request(self, latitude, longitude, situation=None):
        location = f"{latitude},{longitude}"
        nearest_station = self.get_nearest_police_station(latitude, longitude)
        messages_sent = self.send_sos_messages(location, situation)
        
        return {
            "status": "success",
            "messages_sent": messages_sent,
            "nearest_police_station": nearest_station,
            "location": location
        }