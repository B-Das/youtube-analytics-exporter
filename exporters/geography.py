import pandas as pd
from exporters.base import BaseExporter
from mock_data_generator import MockDataGenerator

class GeographyExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "geography"

    @property
    def name(self) -> str:
        return "Geography"

    @property
    def filename(self) -> str:
        return "countries.csv"

    @property
    def description(self) -> str:
        return "Viewer distribution by country (Geography)."

    def export(
        self,
        start_date: str,
        end_date: str,
        analytics_service=None,
        data_service=None,
        use_mock: bool = True
    ) -> pd.DataFrame:
        if use_mock or analytics_service is None:
            return MockDataGenerator.generate_geography(start_date, end_date)

        try:
            response = analytics_service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched,averageViewDuration",
                dimensions="country",
                sort="-views"
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=["country", "views", "minutes", "duration"])
            
            df = pd.DataFrame()
            df["Geography"] = df_raw["country"]
            df["Views"] = df_raw["views"]
            df["Watch time (hours)"] = round(df_raw["minutes"] / 60.0, 2)
            
            import datetime
            df["Average view duration"] = df_raw["duration"].apply(
                lambda x: str(datetime.timedelta(seconds=int(x)))
            )
            return df
        except Exception:
            return MockDataGenerator.generate_geography(start_date, end_date)
