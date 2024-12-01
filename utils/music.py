from ytmusicapi import YTMusic
from streamlit_player import st_player
import streamlit as st

class MusicManager:
    def __init__(self):
        self.ytmusic = YTMusic()
        
    def search_song(self, query):
        try:
            results = self.ytmusic.search(query, filter="songs")
            if results:
                video_id = results[0]['videoId']
                return f"https://www.youtube.com/watch?v={video_id}"
            return None
        except Exception as e:
            st.error(f"Error searching song: {str(e)}")
            return None

    def play_music(self, url):
        try:
            st.subheader("Now Playing")
            st_player(url)
            return True
        except Exception as e:
            st.error(f"Error playing music: {str(e)}")
            return False