"""Upload rules shared by the web form AND the REST API (audit S1).

Every rule about "may this user upload this file?" lives here, so the two
entry points cannot drift apart again. Functions raise Django's
``ValidationError``; the form shows the message under the file field and the
API turns it into an HTTP 400.
"""
from pathlib import Path

from django.core.exceptions import ValidationError

from finance.csv import REQUIRED_COLUMNS as FINANCE_COLUMNS
from marketing.csv import REQUIRED_COLUMNS as MARKETING_COLUMNS
from sales.csv import REQUIRED_COLUMNS as SALES_COLUMNS

from .csv_utils import read_and_normalize_csv

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_ROWS = 50_000  # data rows, header not counted

REQUIRED_COLUMNS_BY_TYPE = {
    "sales": sorted(SALES_COLUMNS),
    "marketing": sorted(MARKETING_COLUMNS),
    "finance": sorted(FINANCE_COLUMNS),
}


def can_upload(user):
    """Only ADMIN and ANALYST users may upload (VIEWER is read-only)."""
    return bool(user and user.is_authenticated and (user.is_admin() or user.is_analyst()))


def validate_file_basics(file):
    """Cheap checks that do not need to read the file: extension and size."""
    if Path(file.name).suffix.lower() != ".csv":
        raise ValidationError("Only CSV files are supported.")

    if file.size > MAX_UPLOAD_BYTES:
        raise ValidationError("CSV file must be 10 MB or smaller.")


def validate_csv_content(file, dataset_type):
    """Read the CSV and check headers, row count and required columns."""
    try:
        df = read_and_normalize_csv(file)
    except Exception as exc:
        raise ValidationError(f"CSV could not be validated: {exc}")
    finally:
        file.seek(0)

    if len(df) > MAX_ROWS:
        raise ValidationError(
            f"CSV has {len(df):,} rows; the limit is {MAX_ROWS:,} rows per file."
        )

    required = REQUIRED_COLUMNS_BY_TYPE.get(dataset_type)
    if required:
        missing = sorted(set(required) - set(df.columns))
        if missing:
            raise ValidationError("Missing required columns: " + ", ".join(missing))


def validate_csv_upload(file, dataset_type):
    """All file rules in order. Used by the API; the form calls the two parts."""
    validate_file_basics(file)
    validate_csv_content(file, dataset_type)
