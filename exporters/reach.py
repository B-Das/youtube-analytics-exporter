# LEGACY: This class is not used by the active SchemaExporter registry. Do not instantiate directly.
import pandas as pd
from exporters.base import BaseExporter

class ReachExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "reach"

    @property
    def name(self) -> str:
        return "Reach"

    @property
    def filename(self) -> str:
        return "Reach.csv"

    @property
    def description(self) -> str:
        return "Reach-adjacent daily metrics available through the YouTube Analytics API."

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
                dimensions="day",
                sort="day",
                channel_id=channel_id
            )
            
            df = pd.DataFrame()
            df["Date"] = df_raw["day"]
            df["Views"] = df_raw["views"]
            df["Engaged views"] = df_raw["engagedViews"]
            df["Watch time (hours)"] = round(df_raw["estimatedMinutesWatched"] / 60.0, 2)
            df["Average view duration"] = df_raw["averageViewDuration"].apply(
                self.seconds_to_duration
            )
            df["Average percentage viewed"] = round(df_raw["averageViewPercentage"], 2)
            return df
        except Exception as e:
            print(f"Reach export error: {e}")
            return pd.DataFrame(columns=[
                "Date", "Views", "Engaged views", "Watch time (hours)",
                "Average view duration", "Average percentage viewed"
            ])
