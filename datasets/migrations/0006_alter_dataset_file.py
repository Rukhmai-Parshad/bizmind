from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("datasets", "0005_remove_dataset_unique_dataset_file_per_type_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dataset",
            name="file",
            field=models.FileField(blank=True, upload_to="datasets/"),
        ),
    ]
