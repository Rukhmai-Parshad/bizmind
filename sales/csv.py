from datasets.csv_utils import read_and_normalize_csv, validate_required_columns

REQUIRED_COLUMNS = {
    "date",
    "product",
    "region",
    "units_sold",
    "unit_price",
}


def process_sales_csv(file_path):
    df = read_and_normalize_csv(file_path)
    validate_required_columns(df, REQUIRED_COLUMNS)

    df = df.dropna(subset=REQUIRED_COLUMNS)
    if df.empty:
        raise ValueError("CSV contains no valid rows after removing incomplete records.")

    import pandas as pd
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    if df[["date", "units_sold", "unit_price"]].isna().any().any():
        raise ValueError("CSV contains invalid dates or numeric values.")

    if (df["units_sold"] <= 0).any():
        raise ValueError("units_sold must be greater than zero.")
    if (df["unit_price"] <= 0).any():
        raise ValueError("unit_price must be greater than zero.")
    if (df["units_sold"] % 1 != 0).any():
        raise ValueError("units_sold must contain whole numbers.")

    df["units_sold"] = df["units_sold"].astype(int)
    df["unit_price"] = df["unit_price"].astype(float)
    df["revenue"] = df["units_sold"] * df["unit_price"]

    df = df.drop_duplicates(subset=["date", "product", "region"], keep="first")
    if df.empty:
        raise ValueError("All rows were duplicates.")

    return df
