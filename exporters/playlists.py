import pandas as pd
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
            raise ValueError('YouTube API service is not connected.')

        try:
            response = analytics_service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="playlistStarts,views,estimatedMinutesWatched,averageViewDuration",
                dimensions="playlist",
                sort="-views"
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=["playlist", "starts", "views", "minutes", "duration"])
            
            df = pd.DataFrame()
            df["Playlist"] = df_raw["playlist"]
            df["Playlist starts"] = df_raw["starts"]
            df["Views"] = df_raw["views"]
            df["Watch time (hours)"] = round(df_raw["minutes"] / 60.0, 2)
            
            import datetime
            df["Average view duration"] = df_raw["duration"].apply(
                lambda x: str(datetime.timedelta(seconds=int(x)))
            )
            return df
        except Exception as e:
            raise RuntimeError(f'API Query failed: {e}')
