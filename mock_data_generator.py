import pandas as pd
import numpy as np
from datetime import datetime, timedelta

HISTORIC_VIDEOS = [
    {"video_id": "vid_001", "title": "Britishers Cut This Pillar Open", "duration": "00:14:20", "publish_date": "2025-08-12"},
    {"video_id": "vid_002", "title": "Lepakshi Temple Hanging Pillar Mystery", "duration": "00:11:45", "publish_date": "2025-09-05"},
    {"video_id": "vid_003", "title": "Supercomputer in Ancient India?", "duration": "00:18:10", "publish_date": "2025-10-19"},
    {"video_id": "vid_004", "title": "Iron Pillar of Delhi: Rust Resistance Science", "duration": "00:16:05", "publish_date": "2025-11-30"},
    {"video_id": "vid_005", "title": "Kailasa Temple Monolithic Carving Secret", "duration": "00:22:15", "publish_date": "2025-12-15"},
    {"video_id": "vid_006", "title": "Brihadisvara Temple Shadow Mystery Explored", "duration": "00:13:40", "publish_date": "2026-01-10"},
    {"video_id": "vid_007", "title": "Konark Sun Temple Acoustic & Magnetic Engineering", "duration": "00:19:50", "publish_date": "2026-02-22"},
    {"video_id": "vid_008", "title": "Ajanta Caves Acoustic Engineering Secrets", "duration": "00:15:30", "publish_date": "2026-04-05"},
]

def parse_dates(start_date: str, end_date: str):
    try:
        s_dt = datetime.strptime(start_date, "%Y-%m-%d")
        e_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception:
        e_dt = datetime.now()
        s_dt = e_dt - timedelta(days=29)
    if s_dt > e_dt:
        s_dt, e_dt = e_dt, s_dt
    return s_dt, e_dt

def get_date_range(start_date: str, end_date: str):
    s_dt, e_dt = parse_dates(start_date, end_date)
    dates = []
    curr = s_dt
    while curr <= e_dt:
        dates.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)
    return dates

class MockDataGenerator:

    @staticmethod
    def generate_overview(start_date: str, end_date: str) -> pd.DataFrame:
        dates = get_date_range(start_date, end_date)
        np.random.seed(42)
        records = []
        for d in dates:
            views = int(np.random.normal(5000, 1000))
            engaged_views = int(views * np.random.uniform(0.6, 0.8))
            watch_time = round(views * np.random.uniform(0.08, 0.12), 2)
            subs = int(views * np.random.uniform(0.005, 0.012))
            avg_duration = int(np.random.uniform(200, 480))
            # Format average view duration as HH:MM:SS
            avg_duration_str = str(timedelta(seconds=avg_duration))
            avg_pct = round(np.random.uniform(45.0, 75.0), 2)
            
            records.append({
                "Views": max(10, views),
                "Engaged views": max(5, engaged_views),
                "Watch time (hours)": max(0.1, watch_time),
                "Subscribers": subs,
                "Average view duration": avg_duration_str,
                "Average percentage viewed": avg_pct,
                "Videos added": 0 if np.random.rand() > 0.15 else 1,
                "Videos published": 0 if np.random.rand() > 0.15 else 1
            })
        return pd.DataFrame(records)

    @staticmethod
    def generate_reach(start_date: str, end_date: str) -> pd.DataFrame:
        dates = get_date_range(start_date, end_date)
        np.random.seed(43)
        records = []
        for d in dates:
            impressions = int(np.random.normal(60000, 10000))
            ctr = round(np.random.uniform(5.5, 9.8), 2)
            stayed_to_watch = round(np.random.uniform(70.0, 85.0), 2)
            unique_viewers = int(impressions * 0.07)
            unique_reach = int(impressions * 0.95)
            avg_views_per_viewer = round(np.random.uniform(1.2, 1.8), 2)
            
            records.append({
                "Impressions": max(100, impressions),
                "Impressions click-through rate": ctr,
                "Stayed to watch": stayed_to_watch,
                "Unique viewers": unique_viewers,
                "Unique reach": unique_reach,
                "Average views per viewer": avg_views_per_viewer
            })
        return pd.DataFrame(records)

    @staticmethod
    def generate_audience(start_date: str, end_date: str) -> pd.DataFrame:
        dates = get_date_range(start_date, end_date)
        np.random.seed(44)
        records = []
        for d in dates:
            new_v = int(np.random.normal(3500, 800))
            ret_v = int(np.random.normal(1200, 300))
            casual_v = int(new_v * 0.7)
            regular_v = int(ret_v * 0.8)
            records.append({
                "New viewers": max(10, new_v),
                "Returning viewers": max(5, ret_v),
                "Casual viewers": max(5, casual_v),
                "Regular viewers": max(5, regular_v)
            })
        return pd.DataFrame(records)

    @staticmethod
    def generate_engagement(start_date: str, end_date: str) -> pd.DataFrame:
        dates = get_date_range(start_date, end_date)
        np.random.seed(45)
        records = []
        for d in dates:
            gained = int(np.random.normal(60, 15))
            lost = int(gained * np.random.uniform(0.05, 0.15))
            likes = int(np.random.normal(350, 70))
            dislikes = int(likes * np.random.uniform(0.01, 0.04))
            shares = int(np.random.normal(45, 12))
            comments = int(np.random.normal(25, 8))
            
            records.append({
                "Subscribers gained": max(0, gained),
                "Subscribers lost": max(0, lost),
                "Likes": max(0, likes),
                "Dislikes": max(0, dislikes),
                "Likes (vs. dislikes)": round((likes / max(1, likes + dislikes)) * 100, 2),
                "Shares": max(0, shares),
                "Comments added": max(0, comments)
            })
        return pd.DataFrame(records)

    @staticmethod
    def generate_content(start_date: str, end_date: str) -> pd.DataFrame:
        np.random.seed(46)
        records = []
        for v in HISTORIC_VIDEOS:
            views = int(np.random.randint(15000, 250000))
            engaged = int(views * np.random.uniform(0.65, 0.82))
            wt = round(views * np.random.uniform(0.07, 0.11), 2)
            subs = int(views * np.random.uniform(0.003, 0.01))
            avg_duration_sec = int(np.random.randint(180, 500))
            avg_duration_str = str(timedelta(seconds=avg_duration_sec))
            avg_pct = round(np.random.uniform(55.0, 81.31), 2)
            likes = int(views * np.random.uniform(0.04, 0.08))
            comments = int(views * np.random.uniform(0.003, 0.012))
            shares = int(views * np.random.uniform(0.01, 0.03))
            impressions = int(views * np.random.uniform(12, 18))
            ctr = round((views / max(1, impressions)) * 100, 2)
            stayed = round(np.random.uniform(72.0, 84.5), 2)

            records.append({
                "Video": v["title"],
                "Video ID": v["video_id"],
                "Published": v["publish_date"],
                "Views": views,
                "Engaged views": engaged,
                "Watch time (hours)": wt,
                "Subscribers": subs,
                "Average view duration": avg_duration_str,
                "Average percentage viewed": avg_pct,
                "Likes": likes,
                "Comments": comments,
                "Shares": shares,
                "Impressions": impressions,
                "CTR": ctr,
                "Stayed to watch": stayed
            })
        return pd.DataFrame(records)

    @staticmethod
    def generate_daily_metrics(start_date: str, end_date: str) -> pd.DataFrame:
        dates = get_date_range(start_date, end_date)
        np.random.seed(47)
        records = []
        for d in dates:
            for v in HISTORIC_VIDEOS[:3]:  # Generate time-series for top 3 videos
                views = int(np.random.randint(100, 1500))
                engaged = int(views * np.random.uniform(0.6, 0.8))
                wt = round(views * np.random.uniform(0.06, 0.1), 2)
                subs = int(views * np.random.uniform(0.003, 0.008))
                avg_sec = int(np.random.randint(200, 400))
                avg_str = str(timedelta(seconds=avg_sec))
                avg_pct = round(np.random.uniform(50.0, 75.0), 2)
                likes = int(views * 0.05)
                comments = int(views * 0.006)
                shares = int(views * 0.015)
                impressions = int(views * 14)
                ctr = round((views / max(1, impressions)) * 100, 2)
                stayed = round(np.random.uniform(70.0, 80.0), 2)

                records.append({
                    "Date": d,
                    "Video": v["title"],
                    "Views": views,
                    "Engaged views": engaged,
                    "Watch time (hours)": wt,
                    "Subscribers": subs,
                    "Average view duration": avg_str,
                    "Average percentage viewed": avg_pct,
                    "Likes": likes,
                    "Comments": comments,
                    "Shares": shares,
                    "Impressions": impressions,
                    "CTR": ctr,
                    "Stayed to watch": stayed
                })
        return pd.DataFrame(records)

    @staticmethod
    def generate_traffic(start_date: str, end_date: str) -> pd.DataFrame:
        sources = [
            "YouTube Search", "Suggested Videos", "Browse Features", 
            "External", "Direct or Unknown", "Channel Pages"
        ]
        records = []
        for src in sources:
            views = int(np.random.randint(5000, 45000))
            wt = round(views * np.random.uniform(0.05, 0.09), 2)
            avg_sec = int(np.random.randint(180, 360))
            records.append({
                "Traffic source": src,
                "Views": views,
                "Watch time (hours)": wt,
                "Average view duration": str(timedelta(seconds=avg_sec))
            })
        return pd.DataFrame(records)

    @staticmethod
    def generate_geography(start_date: str, end_date: str) -> pd.DataFrame:
        countries = ["India", "United States", "United Kingdom", "Canada", "Australia"]
        records = []
        for c in countries:
            views = int(np.random.randint(2000, 85000))
            wt = round(views * np.random.uniform(0.06, 0.08), 2)
            avg_sec = int(np.random.randint(220, 380))
            records.append({
                "Geography": c,
                "Views": views,
                "Watch time (hours)": wt,
                "Average view duration": str(timedelta(seconds=avg_sec))
            })
        return pd.DataFrame(records)

    @staticmethod
    def generate_devices(start_date: str, end_date: str) -> pd.DataFrame:
        devices = ["Mobile Phone", "TV", "Computer", "Tablet"]
        records = []
        for d in devices:
            views = int(np.random.randint(1000, 95000))
            wt = round(views * np.random.uniform(0.04, 0.07), 2)
            avg_sec = int(np.random.randint(150, 320))
            records.append({
                "Device type": d,
                "Views": views,
                "Watch time (hours)": wt,
                "Average view duration": str(timedelta(seconds=avg_sec))
            })
        return pd.DataFrame(records)

    @staticmethod
    def generate_playlists(start_date: str, end_date: str) -> pd.DataFrame:
        playlists = [
            "Ancient Indian Engineering Mysteries",
            "Temple Architecture Secrets",
            "Unexplained Metallurgy of India"
        ]
        records = []
        for p in playlists:
            starts = int(np.random.randint(1000, 5000))
            views = int(starts * np.random.uniform(2.5, 4.5))
            wt = round(views * np.random.uniform(0.08, 0.12), 2)
            avg_sec = int(np.random.randint(240, 420))
            records.append({
                "Playlist": p,
                "Playlist starts": starts,
                "Views": views,
                "Watch time (hours)": wt,
                "Average view duration": str(timedelta(seconds=avg_sec))
            })
        return pd.DataFrame(records)
