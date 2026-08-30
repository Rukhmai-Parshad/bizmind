from django.contrib import admin
from .models import FinanceRecord


@admin.register(FinanceRecord)
class FinanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        'dataset',
        'date',
        'category',
        'department',
        'type',
        'amount',
    )

    list_filter = (
        'type',
        'department',
        'date',
    )

    search_fields = (
        'category',
        'department',
    )

    ordering = ('-date',)

    readonly_fields = ('created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
