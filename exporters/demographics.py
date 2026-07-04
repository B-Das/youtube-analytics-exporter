import pandas as pd
from exporters.base import BaseExporter

class DemographicsExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "demographics"

    @property
    def name(self) -> str:
        return "Audience"

    @property
    def filename(self) -> str:
        return "Audience.csv"

    @property
    def description(self) -> str:
        return "Audience breakdown by age brackets and gender percentages."

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
                metrics="viewerPercentage",
                dimensions="ageGroup,gender",
                sort="ageGroup",
                channel_id=channel_id
            )
            
            df = pd.DataFrame()
            df["Age group"] = df_raw["ageGroup"]
            df["Gender"] = df_raw["gender"]
            df["Viewer percentage"] = round(df_raw["viewerPercentage"], 2)
            return df
        except Exception as e:
            print(f"Demographics export error: {e}")
            return pd.DataFrame(columns=["Age group", "Gender", "Viewer percentage"])
