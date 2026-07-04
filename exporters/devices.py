import pandas as pd
from exporters.base import BaseExporter

class DevicesExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "devices"

    @property
    def name(self) -> str:
        return "Devices"

    @property
    def filename(self) -> str:
        return "Devices.csv"

    @property
    def description(self) -> str:
        return "Hardware distribution metrics by device type."

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
                dimensions="deviceType",
                sort="-views",
                channel_id=channel_id
            )
            
            df = pd.DataFrame()
            df["Device type"] = df_raw["deviceType"]
            df["Views"] = df_raw["views"]
            df["Engaged views"] = df_raw["engagedViews"]
            df["Watch time (hours)"] = round(df_raw["estimatedMinutesWatched"] / 60.0, 2)
            return df
        except Exception as e:
            print(f"Devices export error: {e}")
            return pd.DataFrame(columns=[
                "Device type", "Views", "Engaged views", "Watch time (hours)"
            ])
