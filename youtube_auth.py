import os
import pickle
import json
import base64
import urllib.parse
from typing import List, Optional, Tuple
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]

class YouTubeAuthHandler:
    """
    Handles Google OAuth flow for YouTube Analytics and Data API v3.

    Environment routing:
      - Local:           client_secrets.json + token.pickle + session_state
      - Streamlit Cloud: st.secrets[client_secrets] + session_state only

    Environment is detected by _is_cloud_environment() using:
      1. YOUTUBE_EXPORTER_ENV=cloud environment variable (explicit override)
      2. Presence of 'client_secrets' key in st.secrets (cloud deployment pattern)
    """

    CLIENT_SECRETS_FILE = "client_secrets.json"
    TOKEN_FILE = "token.pickle"
    VERIFIER_FILE = "verifier.txt"
    LAST_DATA_API_ERROR = None

    @classmethod
    def _is_cloud_environment(cls) -> bool:
        """
        Returns True when running on Streamlit Cloud.

        Detection order (no hostname or header inspection):
          1. YOUTUBE_EXPORTER_ENV env var set to 'cloud'
          2. st.secrets contains 'client_secrets' key (cloud deployment pattern)

        To force cloud mode locally for testing:
          set YOUTUBE_EXPORTER_ENV=cloud
        """
        if os.environ.get("YOUTUBE_EXPORTER_ENV", "").lower() == "cloud":
            return True
        try:
            import streamlit as st
            return "client_secrets" in st.secrets
        except Exception:
            return False

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
        """
        Load OAuth credentials.

        Local:  session_state (if present) → token.pickle → refresh → None
        Cloud:  session_state only (token.pickle is not used; filesystem is ephemeral)
        """
        creds = None
        is_cloud = cls._is_cloud_environment()

        # Always check session_state first (works on both local and cloud)
        try:
            import streamlit as st
            if "creds" in st.session_state and st.session_state.creds:
                creds = st.session_state.creds
        except Exception:
            pass

        # Local only: fall back to token.pickle for convenience across browser restarts
        if not creds and not is_cloud and os.path.exists(cls.TOKEN_FILE):
            try:
                with open(cls.TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
            except Exception:
                creds = None

        if creds and creds.valid:
            return creds

        # Refresh expired token
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
        """
        Persist OAuth credentials.

        Local:  session_state + token.pickle
        Cloud:  session_state only (no pickle writes — filesystem is ephemeral)
        """
        is_cloud = cls._is_cloud_environment()

        # Always save to session_state
        try:
            import streamlit as st
            st.session_state.creds = creds
        except Exception:
            pass

        # Local only: also persist to token.pickle for convenience
        if not is_cloud:
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
            analytics = build('youtubeAnalytics', 'v2', credentials=creds, static_discovery=False)
            data = build('youtube', 'v3', credentials=creds, static_discovery=True)
            return analytics, data, True
        except Exception as e:
            print(f"Error building Google API services: {e}")
            return None, None, False

    @classmethod
    def get_channels(cls, data_service) -> List[dict]:
        """Return normalized identity data for channels owned by the user."""
        cls.LAST_DATA_API_ERROR = None
        if not data_service:
            return []

        try:
            channels = []
            page_token = None

            while True:
                request_args = {
                    "mine": True,
                    "part": "snippet,statistics,contentDetails",
                    "maxResults": 50
                }
                if page_token:
                    request_args["pageToken"] = page_token

                response = data_service.channels().list(**request_args).execute()
                for item in response.get("items", []):
                    snippet = item.get("snippet", {})
                    stats = item.get("statistics", {})
                    thumbnails = snippet.get("thumbnails", {})
                    custom_url = snippet.get("customUrl", "")
                    handle = custom_url if custom_url.startswith("@") else ""
                    channels.append({
                        "id": item.get("id", ""),
                        "title": snippet.get("title", ""),
                        "handle": handle,
                        "thumbnail": cls._best_thumbnail(thumbnails),
                        "custom_url": custom_url,
                        "subscribers": stats.get("subscriberCount"),
                        "hidden_subscriber_count": stats.get("hiddenSubscriberCount", False),
                        "video_count": stats.get("videoCount"),
                        "created_at": snippet.get("publishedAt", ""),
                        # Retained for future use: playlist metadata, thumbnails, and URL resolution
                        "uploads_playlist_id": (
                            item.get("contentDetails", {})
                            .get("relatedPlaylists", {})
                            .get("uploads", "")
                        )
                    })

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            return channels
        except Exception as e:
            cls.LAST_DATA_API_ERROR = cls.summarize_api_error(e)
            print(f"Error fetching channel info: {cls.LAST_DATA_API_ERROR}")
        return []

    @classmethod
    def get_channel_info(cls, data_service, channel_id: Optional[str] = None) -> Optional[dict]:
        """Return one owned channel, optionally selected by its channel ID."""
        channels = cls.get_channels(data_service)
        if channel_id:
            return next((channel for channel in channels if channel["id"] == channel_id), None)
        if channels:
            return channels[0]
        return None

    @staticmethod
    def _best_thumbnail(thumbnails: dict) -> str:
        for size in ("high", "medium", "default"):
            url = thumbnails.get(size, {}).get("url")
            if url:
                return url
        return ""

    @classmethod
    def summarize_api_error(cls, error) -> str:
        """Return a human-readable error message for common YouTube API errors."""
        text = str(error)
        if "accessNotConfigured" in text or "YouTube Data API v3 has not been used" in text:
            return (
                "YouTube Data API v3 is not enabled for this Google Cloud project. "
                "Enable it at console.cloud.google.com under APIs & Services."
            )
        if "YouTube Analytics API has not been used" in text:
            return (
                "YouTube Analytics API is not enabled for this Google Cloud project. "
                "Enable it at console.cloud.google.com under APIs & Services."
            )
        if "quotaExceeded" in text:
            return (
                "YouTube API daily quota exceeded. "
                "Please wait until midnight Pacific Time and try again."
            )
        if "rateLimitExceeded" in text or "429" in text:
            return "YouTube API rate limit hit. Please try again in a few minutes."
        if "forbidden" in text.lower() or "'403'" in text:
            return "Access denied (HTTP 403). Check your OAuth scopes and API permissions."
        if "unauthorized" in text.lower() or "'401'" in text:
            return "Authentication failed (HTTP 401). Please log out and log in again."
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return lines[0] if lines else "An unknown API error occurred."

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

        Priority:
          1. app_url from st.secrets (explicit override — recommended for cloud)
          2. Cloud environment: pick the non-localhost URI from client_secrets redirect_uris
          3. Local environment: pick the localhost URI from client_secrets redirect_uris
          4. Hard fallback: http://localhost:8501/

        Environment detection uses _is_cloud_environment(), not hostname headers.
        """
        import streamlit as st

        # 1. Explicit secret override (highest priority)
        try:
            if "app_url" in st.secrets:
                url = st.secrets["app_url"]
                return url if url.endswith("/") else f"{url}/"
        except Exception:
            pass

        # Fetch registered redirect URIs from client secrets
        config = cls.get_client_config()
        web_config = config.get("web", {}) if config else {}
        valid_uris = web_config.get("redirect_uris", [])

        is_cloud = cls._is_cloud_environment()

        if is_cloud:
            # On cloud: return the first non-localhost registered URI
            for uri in valid_uris:
                if "localhost" not in uri and "127.0.0.1" not in uri:
                    return uri
            # Fallback: return any URI (the user must have configured it correctly)
            if valid_uris:
                return valid_uris[0]
            return "https://your-app.streamlit.app/"
        else:
            # Local: prefer localhost URIs registered in client_secrets
            for uri in valid_uris:
                if "localhost" in uri or "127.0.0.1" in uri:
                    return uri
            return "http://localhost:8501/"

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

    @classmethod
    def _encode_state(cls, verifier: str) -> str:
        """
        Encodes the PKCE code_verifier into the OAuth state parameter.

        The state payload is base64url-encoded JSON so Google will echo it back
        verbatim in the redirect URL query string. This means the verifier
        survives Streamlit Cloud app sleep / process restarts without needing
        session_state to persist across the OAuth redirect.
        """
        payload = json.dumps({"cv": verifier})
        encoded = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
        return encoded

    @classmethod
    def _decode_state(cls, state: str) -> Optional[str]:
        """
        Decodes the verifier from the OAuth state parameter echoed back by Google.
        Returns None if decoding fails (e.g. state was not set by this app).
        """
        try:
            # Restore base64 padding
            padding = 4 - len(state) % 4
            if padding != 4:
                state += "=" * padding
            payload = json.loads(base64.urlsafe_b64decode(state).decode())
            return payload.get("cv")
        except Exception:
            return None

    @classmethod
    def get_auth_url(cls, redirect_uri: Optional[str] = None) -> Tuple[str, str]:
        """
        Creates OAuth flow, generates authorization URL, and injects the PKCE
        code_verifier into the OAuth `state` URL parameter.

        Strategy:
          1. Let google_auth_oauthlib call authorization_url() normally.
             The library (google-auth-oauthlib 1.x + requests-oauthlib 2.x)
             auto-generates a PKCE code_verifier and embeds code_challenge in
             the URL.
          2. AFTER the URL is built, read the auto-generated code_verifier from
             the flow object (it is set during authorization_url()).
          3. Replace the `state` param in the URL with a base64-encoded payload
             that contains the verifier. Google echoes `state` back verbatim in
             the redirect URL, so the verifier is recoverable even if the app
             woke from sleep and session_state was wiped.

        This avoids:
          - Passing code_verifier to the /auth endpoint (causes 400 error).
          - Reading flow.code_verifier BEFORE authorization_url() (always None).
          - Double PKCE (we don't add our own code_challenge, the library does).
        """
        flow = cls.create_oauth_flow(redirect_uri=redirect_uri)

        # Let the library build the URL and auto-generate the PKCE verifier
        auth_url, _ = flow.authorization_url(
            prompt="consent",
            access_type="offline",
        )

        # Read the auto-generated verifier — try every known attribute path
        # across google-auth-oauthlib and requests-oauthlib versions
        oauth2session = getattr(flow, "oauth2session", None)
        verifier = (
            getattr(flow, "code_verifier", None)
            or getattr(oauth2session, "code_verifier", None)
            or getattr(oauth2session, "_code_verifier", None)
        )

        if verifier:
            # Inject verifier into the state param — Google echoes it back,
            # so we can recover it on the callback even after app sleep/restart
            state_with_verifier = cls._encode_state(verifier)
            parsed = urllib.parse.urlparse(auth_url)
            params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
            params["state"] = [state_with_verifier]
            new_query = urllib.parse.urlencode(params, doseq=True)
            auth_url = urllib.parse.urlunparse(parsed._replace(query=new_query))

            print(f"[auth] PKCE verifier captured ({len(verifier)} chars), injected into state")

            # Secondary: session_state (same-session shortcut)
            try:
                import streamlit as st
                st.session_state["_oauth_code_verifier"] = verifier
            except Exception as e:
                print(f"Could not save verifier to session_state: {e}")

            # Local disk fallback
            if not cls._is_cloud_environment():
                try:
                    with open(cls.VERIFIER_FILE, "w") as f:
                        f.write(verifier)
                except Exception as e:
                    print(f"Could not save verifier file: {e}")
        else:
            print("[auth] No PKCE verifier found — PKCE may not be active for this flow")

        return auth_url, verifier

    @classmethod
    def exchange_code_for_credentials(
        cls,
        code: str,
        redirect_uri: Optional[str] = None,
        state: Optional[str] = None,
    ):
        """
        Exchanges authorization code for credentials using PKCE code_verifier.

        Verifier lookup order (most-to-least reliable on Streamlit Cloud):
          1. state parameter (echoed by Google in redirect URL — sleep-proof ✅)
          2. st.session_state["_oauth_code_verifier"]  (same-session shortcut)
          3. verifier.txt on disk                       (local-only fallback)
        """
        flow = cls.create_oauth_flow(redirect_uri=redirect_uri)

        verifier = None

        # 1. Primary: decode from OAuth state echoed back by Google — always works
        #    even after app sleep/restart because it comes from the URL itself.
        if state:
            verifier = cls._decode_state(state)
            if verifier:
                print("[auth] code_verifier recovered from OAuth state parameter")

        # 2. Same-session shortcut: session_state (works if app didn't restart)
        if not verifier:
            try:
                import streamlit as st
                verifier = st.session_state.get("_oauth_code_verifier")
                if verifier:
                    print("[auth] code_verifier recovered from session_state")
            except Exception as e:
                print(f"Could not read verifier from session_state: {e}")

        # 3. Local-only disk fallback
        if not verifier:
            try:
                if os.path.exists(cls.VERIFIER_FILE):
                    with open(cls.VERIFIER_FILE, "r") as f:
                        verifier = f.read().strip()
                    if verifier:
                        print("[auth] code_verifier recovered from verifier.txt")
            except Exception as e:
                print(f"Could not read verifier file: {e}")

        if verifier:
            flow.code_verifier = verifier
        else:
            print("[auth] WARNING: no code_verifier found — token exchange may fail")

        flow.fetch_token(code=code)
        cls.save_credentials(flow.credentials)

        # Clean up verifier from secondary storage locations
        try:
            import streamlit as st
            st.session_state.pop("_oauth_code_verifier", None)
        except Exception:
            pass
        try:
            if os.path.exists(cls.VERIFIER_FILE):
                os.remove(cls.VERIFIER_FILE)
        except Exception:
            pass

        return flow.credentials
