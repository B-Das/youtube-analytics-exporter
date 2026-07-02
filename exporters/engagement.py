import pandas as pd
from exporters.base import BaseExporter
from mock_data_generator import MockDataGenerator

class EngagementExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "engagement"

    @property
    def name(self) -> str:
        return "Engagement"

    @property
    def filename(self) -> str:
        return "engagement.csv"

    @property
    def description(self) -> str:
        return "Engagement metrics: Subscribers gained/lost, Likes, Dislikes, Shares, Comments."

    def export(
        self,
        start_date: str,
        end_date: str,
        analytics_service=None,
        data_service=None,
        use_mock: bool = True
    ) -> pd.DataFrame:
        if use_mock or analytics_service is None:
            return MockDataGenerator.generate_engagement(start_date, end_date)

        try:
            response = analytics_service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="subscribersGained,subscribersLost,likes,dislikes,shares,comments",
                dimensions="day"
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=[
                "day", "subscribersGained", "subscribersLost", "likes", "dislikes", "shares", "comments"
            ])
            
            df = pd.DataFrame()
            df["Subscribers gained"] = df_raw["subscribersGained"]
            df["Subscribers lost"] = df_raw["subscribersLost"]
            df["Likes"] = df_raw["likes"]
            df["Dislikes"] = df_raw["dislikes"]
            df["Likes (vs. dislikes)"] = round((df_raw["likes"] / (df_raw["likes"] + df_raw["dislikes"]).replace(0, 1)) * 100, 2)
            df["Shares"] = df_raw["shares"]
            df["Comments added"] = df_raw["comments"]
            return df
        except Exception:
            return MockDataGenerator.generate_engagement(start_date, end_date)
