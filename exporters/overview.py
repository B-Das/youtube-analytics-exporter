import pandas as pd
import datetime
from exporters.base import BaseExporter

class OverviewExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "overview"

    @property
    def name(self) -> str:
        return "Overview"

    @property
    def filename(self) -> str:
        return "overview.csv"

    @property
    def description(self) -> str:
        return "Aggregated channel stats: Views, Engaged views, Watch time (hours), Subscribers, Average view duration, etc."

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
                metrics="views,redViews,estimatedMinutesWatched,subscribersGained,averageViewDuration,averageViewPercentage",
                dimensions="day",
                sort="day"
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=[
                "day", "views", "redViews", "estimatedMinutesWatched", 
                "subscribersGained", "averageViewDuration", "averageViewPercentage"
            ])
            
            df = pd.DataFrame()
            df["Views"] = df_raw["views"]
            df["Engaged views"] = df_raw["redViews"]
            df["Watch time (hours)"] = round(df_raw["estimatedMinutesWatched"] / 60.0, 2)
            df["Subscribers"] = df_raw["subscribersGained"]
            df["Average view duration"] = df_raw["averageViewDuration"].apply(
                lambda x: str(datetime.timedelta(seconds=int(x)))
            )
            df["Average percentage viewed"] = round(df_raw["averageViewPercentage"], 2)
            df["Videos added"] = 0
            df["Videos published"] = 0
            return df
        except Exception as e:
            print(f"Overview export error: {e}")
            df = pd.DataFrame(columns=[
                "Views", "Engaged views", "Watch time (hours)", "Subscribers", 
                "Average view duration", "Average percentage viewed", "Videos added", "Videos published"
            ])
            return df
