import pandas as pd
from exporters.base import BaseExporter
from mock_data_generator import MockDataGenerator

class TrafficExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "traffic"

    @property
    def name(self) -> str:
        return "Traffic Source"

    @property
    def filename(self) -> str:
        return "traffic_sources.csv"

    @property
    def description(self) -> str:
        return "Viewer distribution by traffic source (Search, Suggested, External)."

    def export(
        self,
        start_date: str,
        end_date: str,
        analytics_service=None,
        data_service=None,
        use_mock: bool = True
    ) -> pd.DataFrame:
        if use_mock or analytics_service is None:
            return MockDataGenerator.generate_traffic(start_date, end_date)

        try:
            response = analytics_service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched,averageViewDuration",
                dimensions="insightTrafficSourceType",
                sort="-views"
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=["traffic_source", "views", "minutes", "duration"])
            
            df = pd.DataFrame()
            df["Traffic source"] = df_raw["traffic_source"]
            df["Views"] = df_raw["views"]
            df["Watch time (hours)"] = round(df_raw["minutes"] / 60.0, 2)
            
            import datetime
            df["Average view duration"] = df_raw["duration"].apply(
                lambda x: str(datetime.timedelta(seconds=int(x)))
            )
            return df
        except Exception:
            return MockDataGenerator.generate_traffic(start_date, end_date)
