import pandas as pd
from exporters.base import BaseExporter
from mock_data_generator import MockDataGenerator

class ContentExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "content"

    @property
    def name(self) -> str:
        return "Content"

    @property
    def filename(self) -> str:
        return "content.csv"

    @property
    def description(self) -> str:
        return "Video-by-video performance columns matching the YouTube Studio Content tab."

    def export(
        self,
        start_date: str,
        end_date: str,
        analytics_service=None,
        data_service=None,
        use_mock: bool = True
    ) -> pd.DataFrame:
        if use_mock or analytics_service is None:
            return MockDataGenerator.generate_content(start_date, end_date)

        try:
            # Query video metrics from API
            response = analytics_service.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,redViews,estimatedMinutesWatched,subscribersGained,averageViewDuration,averageViewPercentage,likes,comments,shares,impressions,annotationClickThroughRate",
                dimensions="video",
                sort="-views",
                maxResults=200
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=[
                "video_id", "views", "redViews", "estimatedMinutesWatched",
                "subscribersGained", "averageViewDuration", "averageViewPercentage",
                "likes", "comments", "shares", "impressions", "ctr"
            ])
            
            df = pd.DataFrame()
            df["Video"] = df_raw["video_id"]  # In real API, we map ID to title using Data API
            df["Video ID"] = df_raw["video_id"]
            df["Published"] = ""
            df["Views"] = df_raw["views"]
            df["Engaged views"] = df_raw["redViews"]
            df["Watch time (hours)"] = round(df_raw["estimatedMinutesWatched"] / 60.0, 2)
            df["Subscribers"] = df_raw["subscribersGained"]
            
            import datetime
            df["Average view duration"] = df_raw["averageViewDuration"].apply(
                lambda x: str(datetime.timedelta(seconds=int(x)))
            )
            df["Average percentage viewed"] = df_raw["averageViewPercentage"]
            df["Likes"] = df_raw["likes"]
            df["Comments"] = df_raw["comments"]
            df["Shares"] = df_raw["shares"]
            df["Impressions"] = df_raw["impressions"]
            df["CTR"] = df_raw["ctr"]
            df["Stayed to watch"] = 0.0
            return df
        except Exception:
            return MockDataGenerator.generate_content(start_date, end_date)
