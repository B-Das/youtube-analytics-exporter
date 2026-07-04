# LEGACY: This class is not used by the active SchemaExporter registry. Do not instantiate directly.
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
        return "Playlists.csv"

    @property
    def description(self) -> str:
        return "Playlist performance using playlist-specific YouTube Analytics metrics."

    def export(
        self,
        start_date: str,
        end_date: str,
        analytics_service=None,
        data_service=None,
        channel_id: str = None
    ) -> pd.DataFrame:
        if analytics_service is None:
            raise ValueError("YouTube API service is not connected.")

        try:
            df_raw = self.query_analytics(
                analytics_service=analytics_service,
                start_date=start_date,
                end_date=end_date,
                metrics=(
                    "playlistViews,playlistEstimatedMinutesWatched,"
                    "playlistAverageViewDuration,playlistSaves,playlistStarts,"
                    "viewsPerPlaylistStart,averageTimeInPlaylist"
                ),
                dimensions="playlist",
                sort="-playlistViews",
                max_results=200,
                channel_id=channel_id
            )
            playlist_metadata = self.resolve_playlist_metadata(data_service, df_raw["playlist"].tolist())
            
            df = pd.DataFrame()
            df["Playlist"] = df_raw["playlist"].apply(
                lambda x: playlist_metadata.get(x, {}).get("title", "")
            )
            df["Playlist ID"] = df_raw["playlist"]
            df["Playlist views"] = df_raw["playlistViews"]
            df["Playlist starts"] = df_raw["playlistStarts"]
            df["Playlist saves"] = df_raw["playlistSaves"]
            df["Playlist watch time (hours)"] = round(df_raw["playlistEstimatedMinutesWatched"] / 60.0, 2)
            df["Average view duration"] = df_raw["playlistAverageViewDuration"].apply(
                self.seconds_to_duration
            )
            df["Views per playlist start"] = round(df_raw["viewsPerPlaylistStart"], 2)
            df["Average time in playlist"] = df_raw["averageTimeInPlaylist"].apply(
                self.seconds_to_duration
            )
            return df
        except Exception as e:
            print(f"Playlists export error (unsupported query or no playlists): {e}")
            return pd.DataFrame(columns=[
                "Playlist", "Playlist ID", "Playlist views", "Playlist starts",
                "Playlist saves", "Playlist watch time (hours)",
                "Average view duration", "Views per playlist start",
                "Average time in playlist"
            ])
