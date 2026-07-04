# LEGACY: This class is not used by the active SchemaExporter registry. Do not instantiate directly.
import pandas as pd
from exporters.base import BaseExporter

class GeographyExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "geography"

    @property
    def name(self) -> str:
        return "Geography"

    @property
    def filename(self) -> str:
        return "Geography.csv"

    @property
    def description(self) -> str:
        return "Viewer distribution and engagement metrics by country."

    def export(
        self,
        start_date: str,
        end_date: str,
        analytics_service=None,
        data_service=None,
        channel_id: str = None
    ) -> pd.DataFrame:
        if analytics_service is None:
            raise ValueError('YouTube API service is not connected.')

        try:
            df_raw = self.query_analytics(
                analytics_service=analytics_service,
                start_date=start_date,
                end_date=end_date,
                metrics=(
                    "engagedViews,views,redViews,estimatedMinutesWatched,"
                    "estimatedRedMinutesWatched,subscribersGained,subscribersLost,"
                    "averageViewDuration,averageViewPercentage,likes,dislikes,comments,"
                    "shares,videosAddedToPlaylists,videosRemovedFromPlaylists"
                ),
                dimensions="country",
                sort="-views",
                channel_id=channel_id
            )
            
            df = pd.DataFrame()
            df["Country"] = df_raw["country"]
            df["Views"] = df_raw["views"]
            df["Engaged views"] = df_raw["engagedViews"]
            df["YouTube Premium views"] = df_raw["redViews"]
            df["Watch time (hours)"] = round(df_raw["estimatedMinutesWatched"] / 60.0, 2)
            df["YouTube Premium watch time (hours)"] = round(df_raw["estimatedRedMinutesWatched"] / 60.0, 2)
            df["Subscribers gained"] = df_raw["subscribersGained"]
            df["Subscribers lost"] = df_raw["subscribersLost"]
            df["Average view duration"] = df_raw["averageViewDuration"].apply(
                self.seconds_to_duration
            )
            df["Average percentage viewed"] = round(df_raw["averageViewPercentage"], 2)
            df["Likes"] = df_raw["likes"]
            df["Dislikes"] = df_raw["dislikes"]
            df["Comments"] = df_raw["comments"]
            df["Shares"] = df_raw["shares"]
            df["Videos added to playlists"] = df_raw["videosAddedToPlaylists"]
            df["Videos removed from playlists"] = df_raw["videosRemovedFromPlaylists"]
            return df
        except Exception as e:
            print(f"Geography export error: {e}")
            return pd.DataFrame(columns=[
                "Country", "Views", "Engaged views", "YouTube Premium views",
                "Watch time (hours)", "YouTube Premium watch time (hours)",
                "Subscribers gained", "Subscribers lost",
                "Average view duration", "Average percentage viewed", "Likes",
                "Dislikes", "Comments", "Shares", "Videos added to playlists",
                "Videos removed from playlists"
            ])
