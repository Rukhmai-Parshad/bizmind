from django.contrib import admin
from .models import MarketingRecord


@admin.register(MarketingRecord)
class MarketingRecordAdmin(admin.ModelAdmin):
    list_display = (
        'dataset',
        'date',
        'campaign',
        'channel',
        'impressions',
        'clicks',
        'conversions',
        'spend',
        'revenue',
    )

    list_filter = (
        'channel',
        'date',
    )

    search_fields = (
        'campaign',
        'channel',
    )

    ordering = ('-date',)

    readonly_fields = (
        'created_at',
    )

    # 🔒 Data must come only from CSV processing
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    # ⚠️ Allow delete only for superuser (data correction)
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
