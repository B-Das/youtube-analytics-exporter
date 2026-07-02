import pandas as pd
import datetime
from exporters.base import BaseExporter

class DailyMetricsExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "daily_metrics"

    @property
    def name(self) -> str:
        return "Daily Metrics"

    @property
    def filename(self) -> str:
        return "daily_metrics.csv"

    @property
    def description(self) -> str:
        return "Daily metrics breakdown for each video: Views, Watch time (hours), Subscribers, Average percentage viewed, CTR, stayed to watch."

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
                metrics="views,redViews,estimatedMinutesWatched,subscribersGained,averageViewDuration,averageViewPercentage,likes,comments,shares",
                dimensions="day,video",
                sort="day",
                maxResults=500
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=[
                "day", "video_id", "views", "redViews", "estimatedMinutesWatched",
                "subscribersGained", "averageViewDuration", "averageViewPercentage",
                "likes", "comments", "shares"
            ])
            
            df = pd.DataFrame()
            df["Date"] = df_raw["day"]
            df["Video"] = df_raw["video_id"]
            df["Views"] = df_raw["views"]
            df["Engaged views"] = df_raw["redViews"]
            df["Watch time (hours)"] = round(df_raw["estimatedMinutesWatched"] / 60.0, 2)
            df["Subscribers"] = df_raw["subscribersGained"]
            df["Average view duration"] = df_raw["averageViewDuration"].apply(
                lambda x: str(datetime.timedelta(seconds=int(x)))
            )
            df["Average percentage viewed"] = round(df_raw["averageViewPercentage"], 2)
            df["Likes"] = df_raw["likes"]
            df["Comments"] = df_raw["comments"]
            df["Shares"] = df_raw["shares"]
            df["Impressions"] = "N/A (Studio Export Only)"
            df["CTR"] = "N/A (Studio Export Only)"
            df["Stayed to watch"] = "N/A (Studio Export Only)"
            return df
        except Exception as e:
            print(f"Daily Metrics export error: {e}")
            return pd.DataFrame(columns=[
                "Date", "Video", "Views", "Engaged views", "Watch time (hours)", "Subscribers",
                "Average view duration", "Average percentage viewed", "Likes", "Comments",
                "Shares", "Impressions", "CTR", "Stayed to watch"
            ])
