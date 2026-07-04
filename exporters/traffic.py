import pandas as pd
from exporters.base import BaseExporter

class TrafficExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "traffic"

    @property
    def name(self) -> str:
        return "Traffic source"

    @property
    def filename(self) -> str:
        return "Traffic source.csv"

    @property
    def description(self) -> str:
        return "Viewer distribution by traffic source using supported API metrics."

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
                metrics="engagedViews,views,estimatedMinutesWatched",
                dimensions="insightTrafficSourceType",
                sort="-views",
                channel_id=channel_id
            )
            
            df = pd.DataFrame()
            df["Traffic source"] = df_raw["insightTrafficSourceType"]
            df["Views"] = df_raw["views"]
            df["Engaged views"] = df_raw["engagedViews"]
            df["Watch time (hours)"] = round(df_raw["estimatedMinutesWatched"] / 60.0, 2)
            return df
        except Exception as e:
            print(f"Traffic export error: {e}")
            return pd.DataFrame(columns=[
                "Traffic source", "Views", "Engaged views", "Watch time (hours)"
            ])
