# Deployment Guide — YouTube Analytics Exporter

This guide covers everything needed to deploy the app on Streamlit Cloud for 5–10 trusted users.

---

## 1. Google Cloud API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project (note the **Project ID**).
3. Navigate to **APIs & Services → Library**.
4. Enable the following two APIs:
   - **YouTube Analytics API** (search: "YouTube Analytics API")
   - **YouTube Data API v3** (search: "YouTube Data API v3")

> **Both APIs must be enabled.** The app will show a clear error message if either is missing.

---

## 2. OAuth Client Configuration

1. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**.
2. Set **Application type** to **Web application**.
3. Set a name (e.g., `YouTube Studio Exporter`).
4. Under **Authorized redirect URIs**, add **both**:
   ```
   http://localhost:8501/
   https://your-app-name.streamlit.app/
   ```
   Replace `your-app-name` with your actual Streamlit Cloud app subdomain.
5. Under **Authorized JavaScript origins**, add **both**:
   ```
   http://localhost:8501
   https://your-app-name.streamlit.app
   ```
6. Click **Create** and **download the JSON file** (`client_secrets.json`).

> **Important:** The redirect URI must match exactly — including the trailing slash. A mismatch causes OAuth `redirect_uri_mismatch` errors.

---

## 3. OAuth Consent Screen

1. Go to **APIs & Services → OAuth consent screen**.
2. Set **User type** to **External** (unless all users are within a Google Workspace org).
3. Fill in the required fields (App name, support email).
4. Under **Scopes**, add:
   - `https://www.googleapis.com/auth/yt-analytics.readonly`
   - `https://www.googleapis.com/auth/youtube.readonly`
5. Under **Test users**, add the Google accounts that will use the app (required while the app is in "Testing" status).

> For a small trusted group (≤ 10 users), keeping the app in **Testing** mode is fine. No Google verification is needed.

---

## 4. Local Development

1. Place the downloaded `client_secrets.json` in the project root directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```
4. Visit `http://localhost:8501/` and log in with Google.

The app will save the OAuth token to `token.pickle` locally so you don't need to log in on every browser restart.

---

## 5. Streamlit Secrets Configuration

On Streamlit Cloud, credentials are stored in **Secrets** instead of files.

1. Open your app on [share.streamlit.io](https://share.streamlit.io/).
2. Go to **Settings → Secrets**.
3. Paste the following, replacing all placeholder values:

```toml
# Your app's public URL (must end with a trailing slash)
app_url = "https://your-app-name.streamlit.app/"

[client_secrets]
client_id     = "YOUR_CLIENT_ID.apps.googleusercontent.com"
client_secret = "YOUR_CLIENT_SECRET"
project_id    = "your-gcp-project-id"
auth_uri      = "https://accounts.google.com/o/oauth2/auth"
token_uri     = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
redirect_uris = [
    "https://your-app-name.streamlit.app/",
    "http://localhost:8501/"
]
javascript_origins = [
    "https://your-app-name.streamlit.app",
    "http://localhost:8501"
]
```

The `client_id`, `client_secret`, and other values are found in the downloaded `client_secrets.json` file.

> See `.streamlit/secrets.toml.example` for a fully annotated template.

---

## 6. Streamlit Cloud Deployment Steps

1. **Push your code** to a GitHub repository (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io/) → **New app**.
3. Connect your GitHub repository.
4. Set:
   - **Main file path**: `app.py`
   - **Python version**: 3.10 or 3.11
5. Click **Deploy**.
6. After deployment, go to **Settings → Secrets** and paste your secrets (Step 5 above).
7. **Restart the app** after saving secrets (Manage app → Reboot).

---

## 7. First Login on Streamlit Cloud

1. Visit your deployed app URL.
2. Click **Log in with Google** in the sidebar.
3. You will be redirected to Google's OAuth consent screen.
4. Accept the requested permissions.
5. You are redirected back to the app and authenticated.

> Credentials are stored in your browser session only. If the Streamlit Cloud server restarts, users will need to log in again. This is expected behaviour on the free plan.

---

## 8. Redirect URI Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `redirect_uri_mismatch` | The redirect URI used by the app doesn't match what's registered in GCP | Add the exact URI shown in the error message to your OAuth client's **Authorized redirect URIs** |
| `access_denied` | User not in Test Users list | Add the user's Google account under **OAuth consent screen → Test users** |
| `YouTube Data API v3 is not enabled` | API not enabled in GCP | Go to **APIs & Services → Library** and enable it |
| `quota exceeded` | Daily API quota exhausted | Wait until midnight Pacific Time; quotas reset daily |

---

## 9. Environment Variable Override (Advanced)

To force cloud-mode credential handling locally (for testing):

```bash
# Windows
set YOUTUBE_EXPORTER_ENV=cloud
streamlit run app.py

# macOS / Linux
YOUTUBE_EXPORTER_ENV=cloud streamlit run app.py
```

This makes the app skip `token.pickle` and use `session_state` only — exactly as it behaves on Streamlit Cloud.
