# ============================================================
# API VIEWSETS
# Handles authenticated API access for BizMind resources.
# ============================================================

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

# Project models
from datasets.models import Dataset
from sales.models import SalesRecord
from marketing.models import MarketingRecord
from finance.models import FinanceRecord
from decisions.models import Decision

# Dataset processing service
from datasets.services import process_dataset

# API serializers
from .serializers import (
    DatasetSerializer,
    SalesRecordSerializer,
    MarketingRecordSerializer,
    FinanceRecordSerializer,
    DecisionSerializer,
)

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view


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
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return Dataset.objects.filter(uploaded_by=self.request.user)

    def perform_create(self, serializer):
        dataset = serializer.save(uploaded_by=self.request.user)
        process_dataset(dataset)


@extend_schema_view(
    list=extend_schema(parameters=[DATASET_PARAMETER])
)


# ============================================================
# SALES RECORD VIEWSET
# Handles sales record CRUD operations.
# Users can only access records from their own datasets.
# ============================================================

class SalesRecordViewSet(viewsets.ModelViewSet):
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
# Handles marketing record CRUD operations.
# Users can only access records from their own datasets.
# ============================================================

class MarketingRecordViewSet(viewsets.ModelViewSet):
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
# Handles finance record CRUD operations.
# Users can only access records from their own datasets.
# ============================================================

class FinanceRecordViewSet(viewsets.ModelViewSet):
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