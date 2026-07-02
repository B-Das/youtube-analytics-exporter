from abc import ABC, abstractmethod
import pandas as pd

class BaseExporter(ABC):
    """
    Abstract Base Class for all YouTube Analytics Report Exporters.
    Each exporter module handles fetching, processing, and generating a pandas DataFrame
    for a specific slice of analytics data.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique key identifier for the exporter (e.g., 'overview')."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable display name (e.g., 'Overview')."""
        pass

    @property
    @abstractmethod
    def filename(self) -> str:
        """Target CSV filename inside the ZIP archive (e.g., 'overview.csv')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of what data this exporter includes."""
        pass

    @abstractmethod
    def export(
        self,
        start_date: str,
        end_date: str,
        analytics_service=None,
        data_service=None
    ) -> pd.DataFrame:
        """
        Executes data retrieval and returns a pandas DataFrame.
        
        :param start_date: YYYY-MM-DD string
        :param end_date: YYYY-MM-DD string
        :param analytics_service: YouTube Analytics API service resource (optional)
        :param data_service: YouTube Data API v3 service resource (optional)
        """
        pass

    def estimate_rows(self, start_date: str, end_date: str) -> int:
        """Returns an estimated row count for preview purposes."""
        from datetime import datetime
        try:
            d1 = datetime.strptime(start_date, "%Y-%m-%d")
            d2 = datetime.strptime(end_date, "%Y-%m-%d")
            days = max(1, (d2 - d1).days + 1)
        except Exception:
            days = 30
        return days
