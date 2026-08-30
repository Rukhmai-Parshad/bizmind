from django.test import SimpleTestCase

from .csv import process_finance_csv


class FinanceCsvTests(SimpleTestCase):
    def test_missing_columns_are_rejected(self):
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as file:
            file.write("category,department\nRent,Operations\n")
            path = file.name

        with self.assertRaises(ValueError):
            process_finance_csv(path)
