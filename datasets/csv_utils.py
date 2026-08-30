import pandas as pd


def read_and_normalize_csv(file_or_path):
    """Read a CSV and normalize headers for predictable schema validation."""
    try:
        df = pd.read_csv(file_or_path)
    except Exception as exc:
        raise ValueError(f"CSV file could not be read: {exc}") from exc

    normalized = [str(column).replace("\ufeff", "").strip().lower() for column in df.columns]

    if len(normalized) != len(set(normalized)):
        raise ValueError("CSV contains duplicate column names.")

    df.columns = normalized
    return df


def validate_required_columns(df, required_columns):
    missing = set(required_columns) - set(df.columns)
    if missing:
        missing_columns = ", ".join(sorted(missing))
        raise ValueError(f"Missing required columns: {missing_columns}")

    if df.empty:
        raise ValueError("CSV contains no data rows.")
