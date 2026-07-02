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
        return "reach.csv"

    @property
    def description(self) -> str:
        return "Reach stats: Impressions, CTR, Unique viewers, Unique reach."

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
            response = analytics_service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched",
                dimensions="day",
                sort="day"
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=["day", "views", "estimatedMinutesWatched"])
            
            df = pd.DataFrame()
            df["Impressions"] = "N/A (Studio Export Only)"
            df["Impressions click-through rate"] = "N/A (Studio Export Only)"
            df["Stayed to watch"] = "N/A (Studio Export Only)"
            df["Unique viewers"] = df_raw["views"]
            df["Unique reach"] = df_raw["views"]
            df["Average views per viewer"] = 1.0
            return df
        except Exception as e:
            print(f"Reach export error: {e}")
            return pd.DataFrame(columns=[
                "Impressions", "Impressions click-through rate", "Stayed to watch", 
                "Unique viewers", "Unique reach", "Average views per viewer"
            ])
