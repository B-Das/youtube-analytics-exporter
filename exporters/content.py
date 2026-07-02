import pandas as pd
import datetime
from exporters.base import BaseExporter

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
                dimensions="video",
                sort="-views",
                maxResults=200
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=[
                "video_id", "views", "redViews", "estimatedMinutesWatched",
                "subscribersGained", "averageViewDuration", "averageViewPercentage",
                "likes", "comments", "shares"
            ])
            
            # Optionally resolve video titles using data_service if available
            title_map = {}
            pub_map = {}
            if data_service and len(df_raw) > 0:
                try:
                    video_ids = df_raw["video_id"].tolist()[:50]
                    v_res = data_service.videos().list(
                        part="snippet",
                        id=",".join(video_ids)
                    ).execute()
                    for item in v_res.get("items", []):
                        v_id = item["id"]
                        snip = item["snippet"]
                        title_map[v_id] = snip.get("title", v_id)
                        pub_map[v_id] = snip.get("publishedAt", "")[:10]
                except Exception:
                    pass

            df = pd.DataFrame()
            df["Video"] = df_raw["video_id"].apply(lambda x: title_map.get(x, x))
            df["Video ID"] = df_raw["video_id"]
            df["Published"] = df_raw["video_id"].apply(lambda x: pub_map.get(x, ""))
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
            print(f"Content export error: {e}")
            return pd.DataFrame(columns=[
                "Video", "Video ID", "Published", "Views", "Engaged views", "Watch time (hours)",
                "Subscribers", "Average view duration", "Average percentage viewed", "Likes", "Comments",
                "Shares", "Impressions", "CTR", "Stayed to watch"
            ])
