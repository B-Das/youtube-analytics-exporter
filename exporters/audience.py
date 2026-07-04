# LEGACY: This class is not used by the active SchemaExporter registry. Do not instantiate directly.
import pandas as pd
from exporters.base import BaseExporter

class AudienceExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "audience"

    @property
    def name(self) -> str:
        return "Audience subscription status"

    @property
    def filename(self) -> str:
        return "Audience subscription status.csv"

    @property
    def description(self) -> str:
        return "Audience split by subscribed and unsubscribed viewer activity."

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
                metrics="engagedViews,views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
                dimensions="subscribedStatus",
                channel_id=channel_id
            )
            
            df = pd.DataFrame()
            df["Viewer subscribed status"] = df_raw["subscribedStatus"]
            df["Views"] = df_raw["views"]
            df["Engaged views"] = df_raw["engagedViews"]
            df["Watch time (hours)"] = round(df_raw["estimatedMinutesWatched"] / 60.0, 2)
            df["Average view duration"] = df_raw["averageViewDuration"].apply(
                self.seconds_to_duration
            )
            df["Average percentage viewed"] = round(df_raw["averageViewPercentage"], 2)
            return df
        except Exception as e:
            print(f"Audience export error: {e}")
            return pd.DataFrame(columns=[
                "Viewer subscribed status", "Views", "Engaged views",
                "Watch time (hours)", "Average view duration",
                "Average percentage viewed"
            ])
