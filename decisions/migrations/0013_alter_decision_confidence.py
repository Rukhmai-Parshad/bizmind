from django.db import migrations, models
from django.core.validators import MaxValueValidator, MinValueValidator


class Migration(migrations.Migration):
    dependencies = [
        ("decisions", "0012_decision_confidence_reason"),
    ]

    operations = [
        migrations.AlterField(
            model_name="decision",
            name="confidence",
            field=models.FloatField(
                help_text="Value between 0 and 1",
                validators=[
                    MinValueValidator(0.0),
                    MaxValueValidator(1.0),
                ],
            ),
        ),
    ]
