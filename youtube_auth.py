import os
import pickle
from typing import Tuple, Optional
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]

class YouTubeAuthHandler:
    """
    Handles Google OAuth flow for YouTube Analytics and Data API v3.
    Supports both Streamlit Cloud (Web OAuth Flow) and Local Environment.
    """

    CLIENT_SECRETS_FILE = "client_secrets.json"
    TOKEN_FILE = "token.pickle"

    @classmethod
    def is_client_secrets_present(cls) -> bool:
        try:
            import streamlit as st
            if "client_secrets" in st.secrets:
                return True
        except Exception:
            pass
        return os.path.exists(cls.CLIENT_SECRETS_FILE)

    @classmethod
    def get_credentials(cls):
        creds = None
        
        # Check Streamlit session_state first
        try:
            import streamlit as st
            if "creds" in st.session_state and st.session_state.creds:
                creds = st.session_state.creds
        except Exception:
            pass

        # Fallback to local token pickle file
        if not creds and os.path.exists(cls.TOKEN_FILE):
            try:
                with open(cls.TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
            except Exception:
                creds = None

        if creds and creds.valid:
            return creds

        # Refresh token if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                cls.save_credentials(creds)
                return creds
            except Exception as e:
                print(f"Error refreshing credentials: {e}")

        return None

    @classmethod
    def save_credentials(cls, creds):
        try:
            import streamlit as st
            st.session_state.creds = creds
        except Exception:
            pass

        try:
            with open(cls.TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            print(f"Could not save token file: {e}")

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
    def get_client_config(cls) -> Optional[dict]:
        raw_config = None
        try:
            import streamlit as st
            if "client_secrets" in st.secrets:
                raw_config = dict(st.secrets["client_secrets"])
        except Exception as e:
            print(f"Error loading client config from st.secrets: {e}")

        if not raw_config and os.path.exists(cls.CLIENT_SECRETS_FILE):
            import json
            with open(cls.CLIENT_SECRETS_FILE, "r") as f:
                raw_config = json.load(f)

        if not raw_config:
            return None

        # Format normalization for google_auth_oauthlib
        if "web" in raw_config or "installed" in raw_config:
            return raw_config
        else:
            return {"web": raw_config}

    @classmethod
    def get_redirect_uri(cls) -> str:
        """
        Determines the redirect URI for OAuth.
        """
        import streamlit as st

        # 1. Secret override if provided in st.secrets
        try:
            if "app_url" in st.secrets:
                url = st.secrets["app_url"]
                return url if url.endswith("/") else f"{url}/"
        except Exception:
            pass

        # 2. Modern Streamlit header detection
        try:
            if hasattr(st, "context") and hasattr(st.context, "headers"):
                host = st.context.headers.get("Host") or st.context.headers.get("host")
                if host:
                    proto = "https" if ("streamlit.app" in host or not host.startswith("localhost")) else "http"
                    return f"{proto}://{host}/"
        except Exception:
            pass

        # 3. Default fallback to deployed Streamlit Cloud URL
        return "https://youtube-analytics-exporter-heq3jymvqjomfxeycxwrsf.streamlit.app/"

    @classmethod
    def create_oauth_flow(cls, redirect_uri: Optional[str] = None):
        client_config = cls.get_client_config()
        if not client_config:
            raise ValueError("No client secrets configuration found.")

        if not redirect_uri:
            redirect_uri = cls.get_redirect_uri()

        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        return flow
