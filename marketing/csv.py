from datasets.csv_utils import read_and_normalize_csv, validate_required_columns

REQUIRED_COLUMNS = {
    "date",
    "campaign",
    "channel",
    "impressions",
    "clicks",
    "conversions",
    "spend",
    "revenue",
}


def process_marketing_csv(file_path):
    df = read_and_normalize_csv(file_path)
    validate_required_columns(df, REQUIRED_COLUMNS)

    df = df.dropna(subset=REQUIRED_COLUMNS)
    if df.empty:
        raise ValueError("CSV contains no valid rows after removing incomplete records.")

    import pandas as pd
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    numeric_columns = ["impressions", "clicks", "conversions", "spend", "revenue"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if df[["date", *numeric_columns]].isna().any().any():
        raise ValueError("CSV contains invalid dates or numeric values.")

    integer_columns = ["impressions", "clicks", "conversions"]
    for column in integer_columns:
        if (df[column] % 1 != 0).any():
            raise ValueError(f"{column} must contain whole numbers.")
        df[column] = df[column].astype(int)

    if (df[numeric_columns] < 0).any().any():
        raise ValueError("Negative values are not allowed.")
    if (df["clicks"] > df["impressions"]).any():
        raise ValueError("Clicks cannot exceed impressions.")
    if (df["conversions"] > df["clicks"]).any():
        raise ValueError("Conversions cannot exceed clicks.")

    df = df.drop_duplicates(subset=["date", "campaign", "channel"], keep="first")
    if df.empty:
        raise ValueError("All rows were duplicates.")

    return df
