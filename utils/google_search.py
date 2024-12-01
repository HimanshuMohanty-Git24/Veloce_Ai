# google_search.py
from googleapiclient.discovery import build
import os

class GoogleSearchClient:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.cse_id = os.getenv('GOOGLE_CSE_ID')
        self.service = build('customsearch', 'v1', developerKey=self.api_key)

    def search(self, query, num_results=3):
        try:
            result = self.service.cse().list(
                q=query,
                cx=self.cse_id,
                num=num_results
            ).execute()

            if 'items' in result:
                return [
                    {
                        'title': item['title'],
                        'snippet': item['snippet'],
                        'link': item['link']
                    }
                    for item in result['items']
                ]
            return []
        except Exception as e:
            print(f"Google Search error: {str(e)}")
            return []