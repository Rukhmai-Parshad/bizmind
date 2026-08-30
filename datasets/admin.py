from django.contrib import admin
from .models import Dataset
from decisions.models import Decision


class DecisionInline(admin.TabularInline):
    model = Decision
    extra = 0
    can_delete = False
    readonly_fields = (
        'rule_name',
        'title',
        'recommendation',
        'confidence',
        'created_at',
    )


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'type',
        'uploaded_by',
        'uploaded_at',
        'is_processed',
    )

    readonly_fields = (
        'uploaded_at',
        'is_processed',
        'error_message',
        'decisions_generated',
    )

    inlines = [DecisionInline]

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_processed:
            return False
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_processed:
            return False
        return request.user.is_superuser
