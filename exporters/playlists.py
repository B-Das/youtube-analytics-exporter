import pandas as pd
import datetime
from exporters.base import BaseExporter

class PlaylistsExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "playlists"

    @property
    def name(self) -> str:
        return "Playlists"

    @property
    def filename(self) -> str:
        return "playlists.csv"

    @property
    def description(self) -> str:
        return "Playlist performance: Playlist title, Starts, Views, Watch time, Duration."

    def export(
        self,
        start_date: str,
        end_date: str,
        analytics_service=None,
        data_service=None
    ) -> pd.DataFrame:
        if analytics_service is None:
            raise ValueError("YouTube API service is not connected.")

        try:
            # Query playlist metrics if API supports it
            response = analytics_service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched,averageViewDuration",
                dimensions="playlist",
                sort="-views"
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=["playlist", "views", "minutes", "duration"])
            
            df = pd.DataFrame()
            df["Playlist"] = df_raw["playlist"]
            df["Playlist starts"] = 0
            df["Views"] = df_raw["views"]
            df["Watch time (hours)"] = round(df_raw["minutes"] / 60.0, 2)
            df["Average view duration"] = df_raw["duration"].apply(
                lambda x: str(datetime.timedelta(seconds=int(x)))
            )
            return df
        except Exception as e:
            print(f"Playlists export error (unsupported query or no playlists): {e}")
            # Fallback to listing channel playlists via Data API if available
            df_cols = ["Playlist", "Playlist starts", "Views", "Watch time (hours)", "Average view duration"]
            if data_service:
                try:
                    p_res = data_service.playlists().list(
                        part="snippet,contentDetails",
                        mine=True,
                        maxResults=50
                    ).execute()
                    p_rows = []
                    for item in p_res.get("items", []):
                        title = item["snippet"].get("title", "Untitled")
                        p_rows.append({
                            "Playlist": title,
                            "Playlist starts": 0,
                            "Views": 0,
                            "Watch time (hours)": 0.0,
                            "Average view duration": "00:00:00"
                        })
                    return pd.DataFrame(p_rows, columns=df_cols)
                except Exception:
                    pass
            return pd.DataFrame(columns=df_cols)
