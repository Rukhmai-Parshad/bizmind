from django.core.files.storage import default_storage
from django.db import transaction

from finance.services import process_finance_dataset
from marketing.services import process_marketing_dataset
from sales.services import process_sales_dataset


def process_dataset(dataset):
    processors = {
        "sales": process_sales_dataset,
        "marketing": process_marketing_dataset,
        "finance": process_finance_dataset,
    }

    processor = processors.get(dataset.type)
    if processor is None:
        raise ValueError(f"Unsupported dataset type: {dataset.type}")

    with transaction.atomic():
        processor(dataset)

        stored_file_name = dataset.file.name if dataset.file else None
        dataset.file = ""

        dataset.is_processed = True
        dataset.error_message = None
        dataset.save(update_fields=("file", "is_processed", "error_message"))

        if stored_file_name:
            transaction.on_commit(
                lambda: default_storage.delete(stored_file_name)
            )
