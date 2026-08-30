from django.contrib import admin
from .models import SalesRecord


@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    list_display = (
        'dataset',
        'date',
        'product',
        'region',
        'units_sold',
        'unit_price',
        'revenue',
    )

    list_filter = (
        'region',
        'product',
        'date',
    )

    search_fields = (
        'product',
        'region',
    )

    ordering = ('-date',)

    readonly_fields = ('revenue', 'created_at')

    def has_add_permission(self, request):
        # Raw data should come ONLY from CSV processing
        return False

    def has_change_permission(self, request, obj=None):
        # Prevent manual tampering
        return False

    def has_delete_permission(self, request, obj=None):
        # Deleting sales data is dangerous
        return True
