from django.core.exceptions import ValidationError

from decisions.engine import generate_decisions
from marketing.csv import process_marketing_csv
from marketing.models import MarketingRecord


def process_marketing_dataset(dataset):
    if dataset.type != "marketing":
        raise ValidationError("Dataset type does not match the marketing processor.")

    if dataset.is_processed:
        return

    if MarketingRecord.objects.filter(dataset=dataset).exists():
        raise ValidationError("Marketing records already exist for this dataset.")

    df = process_marketing_csv(dataset.file.path)

    MarketingRecord.objects.bulk_create(
        [
            MarketingRecord(
                dataset=dataset,
                date=row["date"],
                campaign=row["campaign"],
                channel=row["channel"],
                impressions=int(row["impressions"]),
                clicks=int(row["clicks"]),
                conversions=int(row["conversions"]),
                spend=float(row["spend"]),
                revenue=float(row["revenue"]),
            )
            for _, row in df.iterrows()
        ]
    )

    generate_decisions(dataset)
