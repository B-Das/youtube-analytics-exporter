import io
import json
import unittest
import zipfile
from unittest.mock import Mock

import pandas as pd

from exporters.base import BaseExporter
from exporters.registry import get_all_exporters
from youtube_auth import YouTubeAuthHandler
from zip_archiver import build_analytics_zip


class StubExporter(BaseExporter):
    @property
    def id(self):
        return "stub"

    @property
    def name(self):
        return "Overview"

    @property
    def filename(self):
        return "Overview.csv"

    @property
    def description(self):
        return "Test exporter"

    def export(
        self,
        start_date,
        end_date,
        analytics_service=None,
        data_service=None,
        channel_id=None
    ):
        self.received_channel_id = channel_id
        return pd.DataFrame({"Views": [42]})

class TestYouTubeAnalyticsExportToolV1(unittest.TestCase):

    def setUp(self):
        self.start_date = "2026-06-01"
        self.end_date = "2026-06-30"
        self.all_exporters = get_all_exporters()

    def test_exporter_registry_count(self):
        self.assertEqual(len(self.all_exporters), 9, "Expected 9 modular schema exporters registered")

    def test_individual_exporters_raise_on_missing_service(self):
        for exp in self.all_exporters:
            with self.assertRaises(ValueError):
                exp.export(self.start_date, self.end_date, analytics_service=None)

    def test_channel_identity_is_normalized_from_data_api(self):
        data_service = Mock()
        data_service.channels.return_value.list.return_value.execute.return_value = {
            "items": [{
                "id": "UC123",
                "snippet": {
                    "title": "Example Channel",
                    "customUrl": "@example",
                    "publishedAt": "2020-01-02T03:04:05Z",
                    "thumbnails": {"high": {"url": "https://img.example/channel.jpg"}}
                },
                "statistics": {
                    "subscriberCount": "1234",
                    "videoCount": "56",
                    "hiddenSubscriberCount": False
                },
                "contentDetails": {"relatedPlaylists": {"uploads": "UU123"}}
            }]
        }

        channels = YouTubeAuthHandler.get_channels(data_service)

        self.assertEqual(channels[0]["id"], "UC123")
        self.assertEqual(channels[0]["handle"], "@example")
        self.assertEqual(channels[0]["video_count"], "56")
        self.assertEqual(channels[0]["created_at"], "2020-01-02T03:04:05Z")

    def test_selected_channel_identity_reaches_zip_and_metadata(self):
        exporter = StubExporter()
        channel_info = {
            "id": "UC123",
            "title": "My / Channel",
            "handle": "@mychannel",
            "thumbnail": "https://img.example/channel.jpg",
            "custom_url": "@mychannel",
            "subscribers": "100",
            "video_count": "5",
            "created_at": "2020-01-01T00:00:00Z"
        }

        zip_bytes, stats = build_analytics_zip(
            selected_exporters=[exporter],
            start_date=self.start_date,
            end_date=self.end_date,
            channel_info=channel_info,
            analytics_service=Mock(),
            data_service=Mock()
        )

        self.assertEqual(exporter.received_channel_id, "UC123")
        self.assertEqual(stats["filename"], "My _ Channel_2026-06-01_to_2026-06-30.zip")
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            metadata = json.loads(archive.read("metadata.json"))
            self.assertEqual(metadata["Channel"], "My / Channel")
            self.assertEqual(metadata["Channel ID"], "UC123")
            self.assertEqual(metadata["Channel Handle"], "@mychannel")
            self.assertIn("Overview.csv", archive.namelist())

    def test_analytics_query_uses_selected_channel_id(self):
        analytics_service = Mock()
        analytics_service.reports.return_value.query.return_value.execute.return_value = {
            "columnHeaders": [{"name": "views"}],
            "rows": [[42]]
        }
        exporter = StubExporter()

        exporter.query_analytics(
            analytics_service=analytics_service,
            start_date=self.start_date,
            end_date=self.end_date,
            metrics="views",
            channel_id="UC123"
        )

        query_args = analytics_service.reports.return_value.query.call_args.kwargs
        self.assertEqual(query_args["ids"], "channel==UC123")

if __name__ == "__main__":
    unittest.main()
