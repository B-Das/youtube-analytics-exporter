# ⚡ One-Click YouTube Analytics Export Tool

A fast, lightweight, and completely modular YouTube Analytics Export Tool. Replaces manual YouTube Studio export steps with an automated, single-click ZIP downloader containing all relevant CSV report files and a structured `metadata.json`.

---

## 🌟 Features

- **Google Login & Mock Data Fallback**: Instantly evaluate with built-in realistic channel mock data ("Britishers Cut This Pillar Open", "Lepakshi Temple", "Iron Pillar of Delhi") or link your Google OAuth credentials.
- **Preset Date Range Selector**: Quick buttons for Today, Yesterday, Last 7 Days, Last 28 Days, Last 90 Days, Last 365 Days, Lifetime, or Custom date inputs.
- **Selective Download Checklist**: Toggle individual reports (`overview.csv`, `videos.csv`, `daily_metrics.csv`, `traffic_sources.csv`, `countries.csv`, `demographics.csv`, `devices.csv`, `playlists.csv`).
- **Real-Time Export Preview**: Live calculations for requested time range, estimated file counts, total rows, and compressed archive size.
- **One-Click Download**: Click **[Download Everything]** to generate a single ZIP package containing all CSV sheets and `metadata.json`.
- **Automated Daily Task**: Run `python fetch_daily.py` or run `setup_scheduler.bat` to automatically fetch and save daily exports at 9:00 PM every day without opening YouTube Studio.

---

## 🚀 Quick Start

### 1. Run the Streamlit Dashboard
```bash
streamlit run app.py
```
Open the URL shown in your terminal (usually `http://localhost:8501`).

### 2. Test Automated Daily Downloader
```bash
python fetch_daily.py
```
This saves a daily package inside the `daily_exports/` directory.

### 3. Setup Daily 9 PM Automation (Windows)
Double-click `setup_scheduler.bat` or run in CMD as Administrator to register the daily task in Windows Task Scheduler.

---

## 📁 Output Archive Structure

When downloading `HistoricHeights_Analytics_2026-06-04_to_2026-07-02.zip`, the unzipped contents will contain:

```
HistoricHeights_Analytics.zip
│
├── metadata.json
├── overview.csv
├── videos.csv
├── daily_metrics.csv
├── traffic_sources.csv
├── countries.csv
├── demographics.csv
├── devices.csv
└── playlists.csv
```

### `metadata.json` Example
```json
{
  "channel": "Historic Heights",
  "generated_at": "2026-07-02T13:00:00Z",
  "date_range": {
    "start": "2026-06-04",
    "end": "2026-07-02"
  },
  "total_files": 9,
  "total_rows": 240,
  "files": [
    { "exporter_id": "overview", "filename": "overview.csv", "rows": 28 },
    { "exporter_id": "videos", "filename": "videos.csv", "rows": 8 },
    ...
  ]
}
```
