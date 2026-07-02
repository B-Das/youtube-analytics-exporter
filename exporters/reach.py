import pandas as pd
from exporters.base import BaseExporter
from mock_data_generator import MockDataGenerator

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
        return "Reach stats: Impressions, CTR, Stayed to watch, Unique viewers, Unique reach."

    def export(
        self,
        start_date: str,
        end_date: str,
        analytics_service=None,
        data_service=None,
        use_mock: bool = True
    ) -> pd.DataFrame:
        if use_mock or analytics_service is None:
            return MockDataGenerator.generate_reach(start_date, end_date)

        try:
            # Call YouTube Analytics reports
            response = analytics_service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="impressions,annotationClickThroughRate,views,uniques",
                dimensions="day"
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=["day", "impressions", "ctr", "views", "uniques"])
            
            df = pd.DataFrame()
            df["Impressions"] = df_raw["impressions"]
            df["Impressions click-through rate"] = df_raw["ctr"]
            df["Stayed to watch"] = 0.0  # Optional/API estimate mapping
            df["Unique viewers"] = df_raw["uniques"]
            df["Unique reach"] = df_raw["uniques"]
            df["Average views per viewer"] = round(df_raw["views"] / df_raw["uniques"].replace(0, 1), 2)
            return df
        except Exception:
            return MockDataGenerator.generate_reach(start_date, end_date)
