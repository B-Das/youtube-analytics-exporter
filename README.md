# ⚡ YouTube Analytics Exporter

A fast, lightweight, and professional YouTube Analytics Export tool. It replaces manual YouTube Studio export steps with an automated, single-click ZIP downloader containing all relevant CSV report files and a structured `metadata.json` matching YouTube Studio columns.

**Live Application:** [https://youtube-analytics-exporter-heq3jymvqjomfxeycxwrsf.streamlit.app/](https://youtube-analytics-exporter-heq3jymvqjomfxeycxwrsf.streamlit.app/)

---

## 🌟 Features

- **Google OAuth Authentication**: Securely log in with your YouTube-linked Google account to directly fetch authenticated analytics via the YouTube Data and Analytics APIs.
- **Dynamic Channel Identity**: Channel ID, name, handle, thumbnail, counts, and creation date are loaded from YouTube Data API v3. Accounts with multiple owned channels can select one before exporting.
- **Preset Date Range Selector**: Quick buttons for Today, Yesterday, Last 7 Days, Last 28 Days, Last 90 Days, Last 365 Days, Lifetime, or Custom date inputs.
- **Selective Download Checklist**: Toggle individual reports (`overview.csv`, `content.csv`, `reach.csv`, `audience.csv`, `daily_metrics.csv`, `playlists.csv`, etc.).
- **Real-Time Export Preview**: Live preview table of your YouTube channel's real data before you download.
- **One-Click Download**: Click **[Download Everything]** to generate a single ZIP package containing all CSV sheets and `metadata.json`.
- **Automated Daily Task**: Run `python fetch_daily.py` to automatically fetch and save daily exports locally.
- **API Inspector**: Inspect each report's API endpoint, metrics, dimensions, filters, row count, execution time, and errors.

---

## 🚀 Quick Start

### 1. Prerequisites
Create a `client_secrets.json` file in your root directory (or configure Streamlit Cloud secrets in TOML format) containing your Google Cloud project OAuth credentials. Enable both **YouTube Analytics API** and **YouTube Data API v3** in your Google Cloud project.

### 2. Run the Streamlit Dashboard Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Open the URL shown in your terminal (usually `http://localhost:8501`).

### 3. Test Automated Daily Downloader
```bash
python fetch_daily.py
```
This saves each owned channel's package inside a dynamically named `daily_exports/<channel name>/` directory.

---

## 📁 Output Archive Structure

When downloading your ZIP archive, the unzipped contents will contain:

```
<Actual Channel Name>_2026-06-04_to_2026-07-02.zip
│
├── metadata.json
├── Overview.csv
├── Content.csv
├── Reach.csv
├── Audience.csv
├── Daily Metrics.csv
└── Playlists.csv
```

### `metadata.json` Example
```json
{
  "channel": "Actual Connected Channel Name",
  "channel_id": "UCxxxxxxxx",
  "handle": "@channelhandle",
  "Generated At": "2026-07-02T13:00:00Z",
  "Date Range": {
    "start": "2026-06-04",
    "end": "2026-07-02"
  },
  "API Version": "YouTube Analytics API v2 / Data v3",
  "Export Version": "1.0.0",
  "Total Files": 7,
  "Total Rows": 240,
  "Manifest": [
    { "Report Name": "Overview", "Filename": "Overview.csv", "Rows": 28 },
    { "Report Name": "Content", "Filename": "Content.csv", "Rows": 8 }
  ]
}
```
