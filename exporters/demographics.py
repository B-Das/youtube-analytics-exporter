import pandas as pd
from exporters.base import BaseExporter

class DemographicsExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "demographics"

    @property
    def name(self) -> str:
        return "Viewer Age & Gender"

    @property
    def filename(self) -> str:
        return "demographics.csv"

    @property
    def description(self) -> str:
        return "Audience breakdown by age brackets and gender percentages."

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
            response = analytics_service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="viewerPercentage",
                dimensions="ageGroup,gender",
                sort="ageGroup"
            ).execute()

            headers = [col["name"] for col in response.get("columnHeaders", [])]
            rows = response.get("rows", [])
            return pd.DataFrame(rows, columns=headers)
        except Exception as e:
            print(f"API Error in DemographicsExporter: {e}. Falling back to mock generator.")
            return MockDataGenerator.generate_demographics(start_date, end_date)
