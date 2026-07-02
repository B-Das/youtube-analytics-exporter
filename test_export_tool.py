import unittest
import io
import json
import zipfile
import pandas as pd
from exporters.registry import get_all_exporters

class TestYouTubeAnalyticsExportToolV1(unittest.TestCase):

    def setUp(self):
        self.start_date = "2026-06-01"
        self.end_date = "2026-06-30"
        self.all_exporters = get_all_exporters()

    def test_exporter_registry_count(self):
        # 10 exporters (Overview, Content, Reach, Audience, Engagement, Geography, Traffic, Devices, Playlists, Daily Metrics)
        self.assertEqual(len(self.all_exporters), 10, "Expected 10 modular exporters registered")

    def test_individual_exporters_output(self):
        for exp in self.all_exporters:
            df = exp.export(self.start_date, self.end_date, use_mock=True)
            self.assertIsInstance(df, pd.DataFrame, f"{exp.name} should return a pandas DataFrame")
            self.assertGreater(len(df), 0, f"{exp.name} should return non-empty DataFrame")
            self.assertTrue(exp.filename.endswith(".csv"), f"{exp.name} filename should end with .csv")

    def test_overview_columns(self):
        exp = next(e for e in self.all_exporters if e.id == "overview")
        df = exp.export(self.start_date, self.end_date, use_mock=True)
        expected_cols = [
            "Views", "Engaged views", "Watch time (hours)", "Subscribers", 
            "Average view duration", "Average percentage viewed", "Videos added", "Videos published"
        ]
        self.assertEqual(list(df.columns), expected_cols)

    def test_reach_columns(self):
        exp = next(e for e in self.all_exporters if e.id == "reach")
        df = exp.export(self.start_date, self.end_date, use_mock=True)
        expected_cols = [
            "Impressions", "Impressions click-through rate", "Stayed to watch", 
            "Unique viewers", "Unique reach", "Average views per viewer"
        ]
        self.assertEqual(list(df.columns), expected_cols)

if __name__ == "__main__":
    unittest.main()
