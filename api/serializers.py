# ============================================================
# DRF SERIALIZERS
# Converts Django model instances <-> JSON data for the API.
# ============================================================

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

# Project models
from accounts.models import User
from datasets.models import Dataset
from datasets.validators import validate_csv_upload
from sales.models import SalesRecord
from marketing.models import MarketingRecord
from finance.models import FinanceRecord
from decisions.models import Decision


# ============================================================
# USER SERIALIZER
# ============================================================

class UserSerializer(serializers.ModelSerializer):
    """Exposes basic user information in API responses."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
        ]
        read_only_fields = ["id"]


# ============================================================
# DATASET SERIALIZER
# ============================================================

class DatasetSerializer(serializers.ModelSerializer):
    """Handles dataset upload and dataset information."""

    file = serializers.FileField()

    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = Dataset
        fields = [
            "id",
            "name",
            "type",
            "file",
            "uploaded_by",
            "uploaded_at",
            "is_processed",
            "error_message",
        ]
        read_only_fields = [
            "id",
            "uploaded_by",
            "uploaded_at",
            "is_processed",
            "error_message",
        ]

    def validate(self, attrs):
        """Prevent duplicate datasets for the same user.

        On PATCH/PUT the dataset being edited must not count as its own
        duplicate (S7), and a field that was not sent keeps its current value.
        """
        request = self.context.get("request")
        instance = self.instance
        name = attrs.get("name", instance.name if instance else None)
        dataset_type = attrs.get("type", instance.type if instance else None)

        duplicates = Dataset.objects.filter(
            uploaded_by=request.user if request else None,
            name=name,
            type=dataset_type,
        )
        if instance:
            duplicates = duplicates.exclude(pk=instance.pk)

        if request and duplicates.exists():
            raise serializers.ValidationError(
                {"name": ["A dataset with this name and type already exists."]}
            )

        # Same file rules as the web form (extension, size, rows, columns).
        file = attrs.get("file")
        if file is not None:
            try:
                validate_csv_upload(file, dataset_type)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"file": exc.messages})

        return attrs


# ============================================================
# SALES RECORD SERIALIZER
# ============================================================

class SalesRecordSerializer(serializers.ModelSerializer):
    """Read-only view of sales records. Revenue is computed by the server."""

    class Meta:
        model = SalesRecord
        fields = [
            "id",
            "dataset",
            "date",
            "product",
            "region",
            "units_sold",
            "unit_price",
            "revenue",
            "created_at",
        ]
        read_only_fields = fields


# ============================================================
# MARKETING RECORD SERIALIZER
# ============================================================

class MarketingRecordSerializer(serializers.ModelSerializer):
    """Read-only view of marketing records."""

    class Meta:
        model = MarketingRecord
        fields = [
            "id",
            "dataset",
            "date",
            "campaign",
            "channel",
            "impressions",
            "clicks",
            "conversions",
            "spend",
            "revenue",
            "created_at",
        ]
        read_only_fields = fields


# ============================================================
# FINANCE RECORD SERIALIZER
# ============================================================

class FinanceRecordSerializer(serializers.ModelSerializer):
    """Read-only view of finance records."""

    class Meta:
        model = FinanceRecord
        fields = [
            "id",
            "dataset",
            "date",
            "category",
            "department",
            "amount",
            "type",
            "created_at",
        ]
        read_only_fields = fields


# ============================================================
# DECISION SERIALIZER
# ============================================================

class DecisionSerializer(serializers.ModelSerializer):
    """Exposes generated business decisions and insights."""

    class Meta:
        model = Decision
        fields = [
            "id",
            "dataset",
            "title",
            "rule_name",
            "domain",
            "insight",
            "recommendation",
            "explanation",
            "action",
            "impact",
            "confidence",
            "confidence_reason",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]