import os
import json
import time
import random
import datetime
import pandas as pd
from abc import ABC, abstractmethod
from transforms.registry import apply_transform, seconds_to_duration

class BaseExporter(ABC):
    """
    Abstract Base Class for YouTube Analytics Report Exporters.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def filename(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def export(
        self,
        start_date: str,
        end_date: str,
        analytics_service=None,
        data_service=None,
        channel_id: str = None
    ) -> pd.DataFrame:
        pass

    def estimate_rows(self, start_date: str, end_date: str) -> int:
        try:
            d1 = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            d2 = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            return max(1, (d2 - d1).days + 1)
        except Exception:
            return 30

    def _execute_with_retry(self, request_callable, max_retries: int = 3):
        """
        Execute a YouTube API request callable with exponential backoff.

        Retries only on transient errors:
          - HTTP 429 (rate limit)
          - HTTP 500, 502, 503, 504 (server errors)
          - HTTP 403 with reason 'quotaExceeded' (temporary quota exhaustion)

        Never retries permanent errors:
          - HTTP 400 (bad request)
          - HTTP 401 (auth failure)
          - HTTP 403 with reason 'accessNotConfigured' or 'forbidden'
        """
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                return request_callable()
            except Exception as e:
                error_text = str(e)
                status_code = getattr(e, "status_code", None) or getattr(e, "resp", {}).get("status")
                try:
                    status_code = int(status_code)
                except (TypeError, ValueError):
                    status_code = None

                # Extract reason from HttpError detail if available
                reason = ""
                if hasattr(e, "error_details") and e.error_details:
                    reason = e.error_details[0].get("reason", "")
                elif "quotaExceeded" in error_text:
                    reason = "quotaExceeded"
                elif "rateLimitExceeded" in error_text:
                    reason = "rateLimitExceeded"
                elif "accessNotConfigured" in error_text:
                    reason = "accessNotConfigured"

                # Determine whether this error is transient (retryable)
                is_transient = False
                if status_code in (429, 500, 502, 503, 504):
                    is_transient = True
                elif status_code == 403 and reason in ("quotaExceeded", "rateLimitExceeded"):
                    is_transient = True

                last_error = e

                if not is_transient or attempt == max_retries:
                    raise

                # Exponential backoff: 1s → 2s → 4s + jitter
                wait = (2 ** attempt) + random.uniform(0, 0.5)
                print(f"[Retry {attempt + 1}/{max_retries}] Transient error, retrying in {wait:.1f}s: {self.api_error_summary(e)}")
                time.sleep(wait)

        raise last_error

    def query_analytics(
        self,
        analytics_service,
        start_date: str,
        end_date: str,
        metrics: str,
        dimensions: str = None,
        sort: str = None,
        max_results: int = None,
        filters: str = None,
        channel_id: str = None
    ) -> pd.DataFrame:
        """Run a reports.query request and return rows using API header names."""
        request_args = {
            "ids": f"channel=={channel_id}" if channel_id else "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": metrics
        }
        if dimensions:
            request_args["dimensions"] = dimensions
        if sort:
            request_args["sort"] = sort
        if filters:
            request_args["filters"] = filters

        started_at = time.perf_counter()
        try:
            page_size = max_results or 200
            start_index = 1
            columns = []
            rows = []

            while True:
                page_args = {
                    **request_args,
                    "maxResults": page_size,
                    "startIndex": start_index
                }
                response = self._execute_with_retry(
                    lambda pa=page_args: analytics_service.reports().query(**pa).execute()
                )
                if not columns:
                    columns = [
                        header["name"] for header in response.get("columnHeaders", [])
                    ]
                page_rows = response.get("rows", [])
                rows.extend(page_rows)
                if len(page_rows) < page_size:
                    break
                start_index += page_size

            self.last_query_details = {
                "API endpoint": "youtubeAnalytics.reports.query",
                "Metrics requested": metrics,
                "Dimensions requested": dimensions or "",
                "Rows returned": len(rows),
                "API execution time (ms)": round((time.perf_counter() - started_at) * 1000, 2),
                "Status": "Success"
            }
            return pd.DataFrame(rows, columns=columns)
        except Exception as error:
            self.last_query_details = {
                "API endpoint": "youtubeAnalytics.reports.query",
                "Metrics requested": metrics,
                "Dimensions requested": dimensions or "",
                "Rows returned": 0,
                "API execution time (ms)": round((time.perf_counter() - started_at) * 1000, 2),
                "Status": "Failed",
                "Error": str(error)
            }
            raise

    def api_error_summary(self, error) -> str:
        """Return a human-readable error message for common YouTube API errors."""
        text = str(error)

        if "accessNotConfigured" in text or "YouTube Data API v3 has not been used" in text:
            return (
                "YouTube Data API v3 is not enabled for this Google Cloud project. "
                "Enable it at console.cloud.google.com under APIs & Services."
            )
        if "YouTube Analytics API has not been used" in text:
            return (
                "YouTube Analytics API is not enabled for this Google Cloud project. "
                "Enable it at console.cloud.google.com under APIs & Services."
            )
        if "quotaExceeded" in text:
            return (
                "YouTube API daily quota exceeded. "
                "Please wait until midnight Pacific Time and try again."
            )
        if "rateLimitExceeded" in text or "429" in text:
            return "YouTube API rate limit hit. The request will be retried automatically."
        if "badRequest" in text or "'400'" in text:
            return (
                "Invalid API request (HTTP 400). "
                "This report configuration may not be supported for your channel type."
            )
        if "forbidden" in text.lower() or "'403'" in text:
            return "Access denied (HTTP 403). Check your OAuth scopes and API permissions."
        if "unauthorized" in text.lower() or "'401'" in text:
            return "Authentication failed (HTTP 401). Please log out and log in again."
        if "503" in text or "backendError" in text:
            return "YouTube API is temporarily unavailable. Please try again in a few minutes."

        # Fallback: strip HTTP boilerplate and return first meaningful line
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return lines[0] if lines else "An unknown API error occurred."

    def resolve_video_metadata(self, data_service, video_ids):
        """Resolve YouTube video IDs to title and publish date using Data API batches."""
        if not data_service or not video_ids:
            return {}

        unique_ids = []
        seen = set()
        for video_id in video_ids:
            if video_id and video_id not in seen:
                unique_ids.append(video_id)
                seen.add(video_id)

        metadata = {}
        for idx in range(0, len(unique_ids), 50):
            batch = unique_ids[idx:idx + 50]
            try:
                response = data_service.videos().list(
                    part="snippet",
                    id=",".join(batch)
                ).execute()
                for item in response.get("items", []):
                    snippet = item.get("snippet", {})
                    metadata[item.get("id")] = {
                        "title": snippet.get("title", item.get("id", "")),
                        "published": snippet.get("publishedAt", "")[:10]
                    }
            except Exception as e:
                print(f"Video metadata lookup skipped: {self.api_error_summary(e)}")

        return metadata

    def resolve_playlist_metadata(self, data_service, playlist_ids):
        """Resolve YouTube playlist IDs to titles using Data API batches."""
        if not data_service or not playlist_ids:
            return {}

        unique_ids = []
        seen = set()
        for playlist_id in playlist_ids:
            if playlist_id and playlist_id not in seen:
                unique_ids.append(playlist_id)
                seen.add(playlist_id)

        metadata = {}
        for idx in range(0, len(unique_ids), 50):
            batch = unique_ids[idx:idx + 50]
            try:
                response = data_service.playlists().list(
                    part="snippet",
                    id=",".join(batch),
                    maxResults=50
                ).execute()
                for item in response.get("items", []):
                    snippet = item.get("snippet", {})
                    metadata[item.get("id")] = {
                        "title": snippet.get("title", item.get("id", ""))
                    }
            except Exception as e:
                print(f"Playlist metadata lookup skipped: {self.api_error_summary(e)}")

        return metadata

class SchemaExporter(BaseExporter):
    """
    Generic Schema-driven Exporter that configures itself via a JSON schema file.
    """

    def __init__(self, schema_path: str):
        if not os.path.exists(schema_path):
            raise ValueError(f"Schema path not found: {schema_path}")
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

    @property
    def id(self) -> str:
        return self.schema["id"]

    @property
    def name(self) -> str:
        return self.schema["name"]

    @property
    def filename(self) -> str:
        return self.schema["filename"]

    @property
    def description(self) -> str:
        return f"Official report for {self.name} matching YouTube Studio specifications."

    def export(
        self,
        start_date: str,
        end_date: str,
        analytics_service=None,
        data_service=None,
        channel_id: str = None
    ) -> pd.DataFrame:
        if analytics_service is None:
            raise ValueError("YouTube API service is not connected.")

        columns_def = self.schema["columns"]
        dimensions = [c["api_name"] for c in columns_def if c["type"] == "dimension"]
        metrics = [c["api_name"] for c in columns_def if c["type"] == "metric"]

        dim_str = ",".join(dimensions) if dimensions else None
        metric_str = ",".join(metrics)

        # Read optional filters & sort from schema
        schema_filters = self.schema.get("filters")
        schema_sort = self.schema.get("sort_api")

        df_raw = self.query_analytics(
            analytics_service=analytics_service,
            start_date=start_date,
            end_date=end_date,
            metrics=metric_str,
            dimensions=dim_str,
            sort=schema_sort,
            filters=schema_filters,
            channel_id=channel_id
        )

        if df_raw.empty:
            empty_cols = [c["display_name"] for c in columns_def]
            return pd.DataFrame(columns=empty_cols)

        # Resolve Video Metadata if required
        video_metadata = {}
        if "video" in dimensions and data_service:
            video_ids = df_raw["video"].tolist()
            video_metadata = self.resolve_video_metadata(data_service, video_ids)

        # Resolve Playlist Metadata if required
        playlist_metadata = {}
        if "playlist" in dimensions and data_service:
            playlist_ids = df_raw["playlist"].tolist()
            playlist_metadata = self.resolve_playlist_metadata(data_service, playlist_ids)

        df_out = pd.DataFrame()

        for c in columns_def:
            api_name = c["api_name"]
            display_name = c["display_name"]
            col_type = c["type"]
            transform_key = c.get("transform")

            if col_type == "metadata":
                if api_name == "video_title":
                    df_out[display_name] = df_raw["video"].apply(
                        lambda x: video_metadata.get(x, {}).get("title", x)
                    )
                elif api_name == "video_published":
                    df_out[display_name] = df_raw["video"].apply(
                        lambda x: video_metadata.get(x, {}).get("published", "")
                    )
                elif api_name == "playlist_title":
                    df_out[display_name] = df_raw["playlist"].apply(
                        lambda x: playlist_metadata.get(x, {}).get("title", x)
                    )
            else:
                if api_name in df_raw.columns:
                    val_series = df_raw[api_name]
                    if transform_key:
                        df_out[display_name] = val_series.apply(
                            lambda x: apply_transform(transform_key, x)
                        )
                    else:
                        df_out[display_name] = val_series
                else:
                    if c.get("required", True):
                        raise KeyError(f"Required API column '{api_name}' not returned in response.")
                    df_out[display_name] = 0

        # Apply Sorting if configured in schema
        sort_config = self.schema.get("sort", [])
        if sort_config:
            by_cols = []
            ascending_flags = []
            for item in sort_config:
                parts = item.split()
                col_name = parts[0]
                direction = parts[1].upper() if len(parts) > 1 else "ASC"
                if col_name in df_out.columns:
                    by_cols.append(col_name)
                    ascending_flags.append(direction == "ASC")
            if by_cols:
                df_out = df_out.sort_values(by=by_cols, ascending=ascending_flags)

        return df_out
