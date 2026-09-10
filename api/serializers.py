# ============================================================
# DRF SERIALIZERS
# Converts Django model instances <-> JSON data for the API.
# ============================================================

from rest_framework import serializers

# Project models
from accounts.models import User
from datasets.models import Dataset
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
        """Prevent duplicate datasets for the same user."""
        request = self.context.get("request")
        name = attrs.get("name")
        dataset_type = attrs.get("type")

        if request and Dataset.objects.filter(
            uploaded_by=request.user,
            name=name,
            type=dataset_type,
        ).exists():
            raise serializers.ValidationError(
                {"name": ["A dataset with this name and type already exists."]}
            )

        return attrs


# ============================================================
# SALES RECORD SERIALIZER
# ============================================================

class SalesRecordSerializer(serializers.ModelSerializer):
    """Handles sales record CRUD operations."""

    revenue = serializers.FloatField()

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
        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate_dataset(self, dataset):
        """Prevent access to another user's dataset."""

        request = self.context.get("request")

        if request and dataset.uploaded_by != request.user:
            raise serializers.ValidationError(
                "You do not have permission to use this dataset."
            )

        return dataset


# ============================================================
# MARKETING RECORD SERIALIZER
# ============================================================

class MarketingRecordSerializer(serializers.ModelSerializer):
    """Handles marketing record CRUD operations."""

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
        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate_dataset(self, dataset):
        """Prevent access to another user's dataset."""

        request = self.context.get("request")

        if request and dataset.uploaded_by != request.user:
            raise serializers.ValidationError(
                "You do not have permission to use this dataset."
            )

        return dataset


# ============================================================
# FINANCE RECORD SERIALIZER
# ============================================================

class FinanceRecordSerializer(serializers.ModelSerializer):
    """Handles finance record CRUD operations."""

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
        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate_dataset(self, dataset):
        """Prevent access to another user's dataset."""

        request = self.context.get("request")

        if request and dataset.uploaded_by != request.user:
            raise serializers.ValidationError(
                "You do not have permission to use this dataset."
            )

        return dataset


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