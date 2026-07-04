import pandas as pd
from exporters.base import BaseExporter

class EngagementExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "engagement"

    @property
    def name(self) -> str:
        return "Engagement"

    @property
    def filename(self) -> str:
        return "Engagement.csv"

    @property
    def description(self) -> str:
        return "Engagement metrics: Subscribers gained/lost, Likes, Dislikes, Shares, Comments."

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
                metrics="subscribersGained,subscribersLost,likes,dislikes,shares,comments",
                dimensions="day",
                sort="day",
                channel_id=channel_id
            )
            
            df = pd.DataFrame()
            df["Date"] = df_raw["day"]
            df["Subscribers gained"] = df_raw["subscribersGained"]
            df["Subscribers lost"] = df_raw["subscribersLost"]
            df["Likes"] = df_raw["likes"]
            df["Dislikes"] = df_raw["dislikes"]
            df["Shares"] = df_raw["shares"]
            df["Comments added"] = df_raw["comments"]
            return df
        except Exception as e:
            print(f"Engagement export error: {e}")
            return pd.DataFrame(columns=[
                "Date", "Subscribers gained", "Subscribers lost",
                "Likes", "Dislikes", "Shares",
                "Comments added"
            ])
