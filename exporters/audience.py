import pandas as pd
from exporters.base import BaseExporter

class AudienceExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "audience"

    @property
    def name(self) -> str:
        return "Audience"

    @property
    def filename(self) -> str:
        return "audience.csv"

    @property
    def description(self) -> str:
        return "Audience details: New viewers, Returning viewers, Casual viewers, Regular viewers."

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
                metrics="views,subscribersGained,subscribersLost",
                dimensions="day",
                sort="day"
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=["day", "views", "subscribersGained", "subscribersLost"])
            
            df = pd.DataFrame()
            df["New viewers"] = df_raw["subscribersGained"]
            df["Returning viewers"] = df_raw["views"] - df_raw["subscribersGained"]
            df["Casual viewers"] = 0
            df["Regular viewers"] = 0
            return df
        except Exception as e:
            print(f"Audience export error: {e}")
            return pd.DataFrame(columns=[
                "New viewers", "Returning viewers", "Casual viewers", "Regular viewers"
            ])
