from datasets.csv_utils import read_and_normalize_csv, validate_required_columns

REQUIRED_COLUMNS = {
    "date",
    "category",
    "department",
    "amount",
    "type",
}


def process_finance_csv(file_path):
    df = read_and_normalize_csv(file_path)
    validate_required_columns(df, REQUIRED_COLUMNS)

    df = df.dropna(subset=REQUIRED_COLUMNS)
    if df.empty:
        raise ValueError("CSV contains no valid rows after removing incomplete records.")

    import pandas as pd
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    if df[["date", "amount"]].isna().any().any():
        raise ValueError("CSV contains invalid dates or amounts.")
    if (df["amount"] <= 0).any():
        raise ValueError("Amount must be greater than zero.")
    if not df["type"].astype(str).str.strip().str.lower().isin(["income", "expense"]).all():
        raise ValueError("type must be either 'income' or 'expense'.")

    df["type"] = df["type"].astype(str).str.strip().str.lower()
    df = df.drop_duplicates(subset=["date", "category", "department", "type"], keep="first")
    if df.empty:
        raise ValueError("All rows were duplicates.")

    return df
