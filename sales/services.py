from django.core.exceptions import ValidationError

from decisions.engine import generate_decisions
from sales.csv import process_sales_csv
from sales.models import SalesRecord


def process_sales_dataset(dataset):
    if dataset.type != "sales":
        raise ValidationError("Dataset type does not match the sales processor.")

    if dataset.is_processed:
        return

    if SalesRecord.objects.filter(dataset=dataset).exists():
        raise ValidationError("Sales records already exist for this dataset.")

    df = process_sales_csv(dataset.file.path)

    SalesRecord.objects.bulk_create(
        [
            SalesRecord(
                dataset=dataset,
                date=row["date"],
                product=row["product"],
                region=row["region"],
                units_sold=int(row["units_sold"]),
                unit_price=float(row["unit_price"]),
                revenue=float(row["revenue"]),
            )
            for _, row in df.iterrows()
        ]
    )

    generate_decisions(dataset)
