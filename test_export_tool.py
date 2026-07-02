import unittest
from exporters.registry import get_all_exporters

class TestYouTubeAnalyticsExportToolV1(unittest.TestCase):

    def setUp(self):
        self.start_date = "2026-06-01"
        self.end_date = "2026-06-30"
        self.all_exporters = get_all_exporters()

    def test_exporter_registry_count(self):
        self.assertEqual(len(self.all_exporters), 10, "Expected 10 modular exporters registered")

    def test_individual_exporters_raise_on_missing_service(self):
        for exp in self.all_exporters:
            with self.assertRaises(ValueError):
                exp.export(self.start_date, self.end_date, analytics_service=None)

if __name__ == "__main__":
    unittest.main()
