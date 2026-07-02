import pandas as pd
from exporters.base import BaseExporter

class DevicesExporter(BaseExporter):

    @property
    def id(self) -> str:
        return "devices"

    @property
    def name(self) -> str:
        return "Devices"

    @property
    def filename(self) -> str:
        return "devices.csv"

    @property
    def description(self) -> str:
        return "Hardware distribution metrics: Device type, Views, Watch time (hours), Average view duration."

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
                dimensions="deviceType",
                sort="-views"
            ).execute()

            rows = response.get("rows", [])
            df_raw = pd.DataFrame(rows, columns=["device", "views", "minutes", "duration"])
            
            df = pd.DataFrame()
            df["Device type"] = df_raw["device"]
            df["Views"] = df_raw["views"]
            df["Watch time (hours)"] = round(df_raw["minutes"] / 60.0, 2)
            
            import datetime
            df["Average view duration"] = df_raw["duration"].apply(
                lambda x: str(datetime.timedelta(seconds=int(x)))
            )
            return df
        except Exception as e:
            raise RuntimeError(f'API Query failed: {e}')
