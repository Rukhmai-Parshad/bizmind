from django import forms
from django.core.exceptions import ValidationError

from .models import Dataset
from .validators import (
    REQUIRED_COLUMNS_BY_TYPE,
    validate_csv_content,
    validate_file_basics,
)


class DatasetUploadForm(forms.ModelForm):
    # Kept as an attribute for any code that reads it; the rules live in validators.py.
    REQUIRED_COLUMNS = REQUIRED_COLUMNS_BY_TYPE

    class Meta:
        model = Dataset
        fields = ("name", "type", "file")

    def clean_file(self):
        file = self.cleaned_data["file"]
        validate_file_basics(file)
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
                validate_csv_content(file, dataset_type)
            except ValidationError as exc:
                self.add_error("file", exc)

        return cleaned_data

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
