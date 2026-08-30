from django.test import SimpleTestCase

from .csv import process_sales_csv


class SalesCsvTests(SimpleTestCase):
    def test_missing_columns_are_rejected(self):
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as file:
            file.write("product,region\nLaptop,North\n")
            path = file.name

        with self.assertRaises(ValueError):
            process_sales_csv(path)
