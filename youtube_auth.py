import os
import pickle
from typing import Tuple, Optional

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]

class YouTubeAuthHandler:
    """
    Handles Google OAuth flow for YouTube Analytics and Data API v3.
    Stores session tokens in `token.pickle`.
    """

    CLIENT_SECRETS_FILE = "client_secrets.json"
    TOKEN_FILE = "token.pickle"

    @classmethod
    def is_client_secrets_present(cls) -> bool:
        import streamlit as st
        try:
            if "client_secrets" in st.secrets:
                return True
        except Exception:
            pass
        return os.path.exists(cls.CLIENT_SECRETS_FILE)

    @classmethod
    def get_credentials(cls):
        creds = None
        if os.path.exists(cls.TOKEN_FILE):
            try:
                with open(cls.TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
            except Exception:
                creds = None

        if creds and creds.valid:
            return creds

        return None

    @classmethod
    def get_services(cls) -> Tuple[Optional[object], Optional[object], bool]:
        """
        Returns (analytics_service, data_service, is_authenticated)
        """
        creds = cls.get_credentials()
        if not creds:
            return None, None, False

        try:
            from googleapiclient.discovery import build
            analytics = build('youtubeAnalytics', 'v2', credentials=creds)
            data = build('youtube', 'v3', credentials=creds)
            return analytics, data, True
        except Exception as e:
            print(f"Error building Google API services: {e}")
            return None, None, False

    @classmethod
    def save_credentials(cls, creds):
        with open(cls.TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    @classmethod
    def get_channel_info(cls, data_service) -> Optional[dict]:
        """
        Retrieves snippet and statistics for the authenticated channel.
        """
        if not data_service:
            return None
        try:
            response = data_service.channels().list(
                mine=True,
                part="snippet,statistics"
            ).execute()
            items = response.get("items", [])
            if items:
                snippet = items[0].get("snippet", {})
                stats = items[0].get("statistics", {})
                return {
                    "title": snippet.get("title", "Unknown Channel"),
                    "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                    "subscribers": stats.get("subscriberCount", "0"),
                    "customUrl": snippet.get("customUrl", "")
                }
        except Exception as e:
            print(f"Error fetching channel info: {e}")
        return None

    @classmethod
    def create_oauth_flow(cls):
        from google_auth_oauthlib.flow import InstalledAppFlow
        import streamlit as st
        
        # Try loading from Streamlit secrets (production cloud config)
        try:
            if "client_secrets" in st.secrets:
                # Convert the Streamlit secrets object to a dict
                client_config = dict(st.secrets["client_secrets"])
                return InstalledAppFlow.from_client_config(client_config, SCOPES)
        except Exception as e:
            print(f"Error loading client config from st.secrets: {e}")

        # Fallback to local file
        flow = InstalledAppFlow.from_client_secrets_file(
            cls.CLIENT_SECRETS_FILE, SCOPES
        )
        return flow

