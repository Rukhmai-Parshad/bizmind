from django.test import SimpleTestCase

from .csv import process_marketing_csv


class MarketingCsvTests(SimpleTestCase):
    def test_missing_columns_are_rejected(self):
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as file:
            file.write("campaign,channel\nSummer,Search\n")
            path = file.name

        with self.assertRaises(ValueError):
            process_marketing_csv(path)
