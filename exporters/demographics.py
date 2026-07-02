import pandas as pd
from exporters.base import BaseExporter
from mock_data_generator import MockDataGenerator

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
        data_service=None,
        use_mock: bool = True
    ) -> pd.DataFrame:
        if use_mock or analytics_service is None:
            return MockDataGenerator.generate_demographics(start_date, end_date)

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
