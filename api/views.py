# ============================================================
# API VIEWSETS
# Handles authenticated API access for BizMind resources.
# ============================================================

import logging

from rest_framework import serializers, viewsets
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from .permissions import AdminOrAnalystForWrites

# Project models
from datasets.models import Dataset
from sales.models import SalesRecord
from marketing.models import MarketingRecord
from finance.models import FinanceRecord
from decisions.models import Decision

# Dataset processing service
from datasets.services import save_and_process_dataset

# API serializers
from .serializers import (
    DatasetSerializer,
    SalesRecordSerializer,
    MarketingRecordSerializer,
    FinanceRecordSerializer,
    DecisionSerializer,
)

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view


logger = logging.getLogger(__name__)


class ProcessingFailed(APIException):
    """HTTP 500 with a safe message (the real error goes to the log only)."""

    status_code = 500
    default_detail = "The dataset could not be processed because of an unexpected error."
    default_code = "processing_failed"


DATASET_PARAMETER = OpenApiParameter(
    name="dataset",
    type=int,
    location="query",
    required=False,
    description="Filter records by dataset ID.",
)

# ============================================================
# DATASET VIEWSET
# Handles dataset upload and dataset management.
# Users can only access datasets they own.
# ============================================================

class DatasetViewSet(viewsets.ModelViewSet):
    serializer_class = DatasetSerializer
    permission_classes = [IsAuthenticated, AdminOrAnalystForWrites]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return Dataset.objects.filter(uploaded_by=self.request.user)

    def perform_create(self, serializer):
        dataset = Dataset(uploaded_by=self.request.user, **serializer.validated_data)

        try:
            # All or nothing: on any failure the row, records and file are gone (S5).
            save_and_process_dataset(dataset)
        except ValueError as exc:
            # A problem inside the CSV data, e.g. "units_sold must be greater than zero."
            logger.warning("Dataset validation failed for %r: %s", dataset.name, exc)
            raise serializers.ValidationError({"file": [str(exc)]})
        except Exception:
            logger.exception("Dataset processing failed for %r", dataset.name)
            raise ProcessingFailed()

        serializer.instance = dataset


@extend_schema_view(
    list=extend_schema(parameters=[DATASET_PARAMETER])
)


# ============================================================
# SALES RECORD VIEWSET
# Read-only (audit S2): records are created only by CSV processing.
# Users can only access records from their own datasets.
# ============================================================

class SalesRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SalesRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = SalesRecord.objects.filter(
            dataset__uploaded_by=self.request.user
        )

        dataset_id = self.request.query_params.get("dataset")

        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)

        return queryset


@extend_schema_view(
    list=extend_schema(parameters=[DATASET_PARAMETER])
)


# ============================================================
# MARKETING RECORD VIEWSET
# Read-only (audit S2): records are created only by CSV processing.
# Users can only access records from their own datasets.
# ============================================================

class MarketingRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MarketingRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = MarketingRecord.objects.filter(
            dataset__uploaded_by=self.request.user
        )

        dataset_id = self.request.query_params.get("dataset")

        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)

        return queryset


@extend_schema_view(
    list=extend_schema(parameters=[DATASET_PARAMETER])
)


# ============================================================
# FINANCE RECORD VIEWSET
# Read-only (audit S2): records are created only by CSV processing.
# Users can only access records from their own datasets.
# ============================================================

class FinanceRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FinanceRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FinanceRecord.objects.filter(
            dataset__uploaded_by=self.request.user
        )

        dataset_id = self.request.query_params.get("dataset")

        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)

        return queryset


# ============================================================
# DECISION VIEWSET
# Exposes generated business decisions as read-only data.
# Users can only access decisions from their own datasets.
# ============================================================

class DecisionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DecisionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Decision.objects.filter(
            dataset__uploaded_by=self.request.user
        )