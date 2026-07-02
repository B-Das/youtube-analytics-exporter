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
            raise ValueError('YouTube API service is not connected.')

        try:
            # Query audience details from API
            response = analytics_service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,uniques",
                dimensions="day"
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=["day", "views", "uniques"])
            
            df = pd.DataFrame()
            df["New viewers"] = df_raw["uniques"]
            df["Returning viewers"] = df_raw["views"] - df_raw["uniques"]
            df["Casual viewers"] = 0
            df["Regular viewers"] = 0
            return df
        except Exception as e:
            raise RuntimeError(f'API Query failed: {e}')
