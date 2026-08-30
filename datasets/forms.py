from pathlib import Path

from django import forms

from .models import Dataset
from .csv_utils import read_and_normalize_csv
from sales.csv import REQUIRED_COLUMNS as SALES_COLUMNS
from marketing.csv import REQUIRED_COLUMNS as MARKETING_COLUMNS
from finance.csv import REQUIRED_COLUMNS as FINANCE_COLUMNS


class DatasetUploadForm(forms.ModelForm):
    REQUIRED_COLUMNS = {
        "sales": sorted(SALES_COLUMNS),
        "marketing": sorted(MARKETING_COLUMNS),
        "finance": sorted(FINANCE_COLUMNS),
    }

    class Meta:
        model = Dataset
        fields = ("name", "type", "file")

    def clean_file(self):
        file = self.cleaned_data["file"]
        extension = Path(file.name).suffix.lower()

        if extension != ".csv":
            raise forms.ValidationError("Only CSV files are supported.")

        max_size = 10 * 1024 * 1024
        if file.size > max_size:
            raise forms.ValidationError("CSV file must be 10 MB or smaller.")

        return file

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        dataset_type = cleaned_data.get("type")

        if name and dataset_type and Dataset.objects.filter(
            uploaded_by=self.user,
            name=name,
            type=dataset_type,
        ).exists():
            raise forms.ValidationError(
                "You already uploaded a dataset with this name and type."
            )

        file = cleaned_data.get("file")
        if file and dataset_type:
            try:
                df = read_and_normalize_csv(file)
                file.seek(0)
                missing = sorted(set(self.REQUIRED_COLUMNS[dataset_type]) - set(df.columns))
                if missing:
                    self.add_error(
                        "file",
                        "Missing required columns: " + ", ".join(missing)
                    )
            except Exception as exc:
                self.add_error("file", f"CSV could not be validated: {exc}")
            finally:
                file.seek(0)

        return cleaned_data

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
