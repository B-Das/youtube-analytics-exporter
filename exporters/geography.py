import pandas as pd
import datetime
from exporters.base import BaseExporter

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
        data_service=None
    ) -> pd.DataFrame:
        if analytics_service is None:
            raise ValueError('YouTube API service is not connected.')

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
            df["Average view duration"] = df_raw["duration"].apply(
                lambda x: str(datetime.timedelta(seconds=int(x)))
            )
            return df
        except Exception as e:
            print(f"Geography export error: {e}")
            return pd.DataFrame(columns=["Geography", "Views", "Watch time (hours)", "Average view duration"])
