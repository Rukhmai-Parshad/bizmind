from django.core.exceptions import ValidationError

from decisions.engine import generate_decisions
from finance.csv import process_finance_csv
from finance.models import FinanceRecord


def process_finance_dataset(dataset):
    if dataset.type != "finance":
        raise ValidationError("Dataset type does not match the finance processor.")

    if dataset.is_processed:
        return

    if FinanceRecord.objects.filter(dataset=dataset).exists():
        raise ValidationError("Finance records already exist for this dataset.")

    df = process_finance_csv(dataset.file.path)

    FinanceRecord.objects.bulk_create(
        [
            FinanceRecord(
                dataset=dataset,
                date=row["date"],
                category=row["category"],
                department=row["department"],
                amount=float(row["amount"]),
                type=row["type"],
            )
            for _, row in df.iterrows()
        ]
    )

    generate_decisions(dataset)
