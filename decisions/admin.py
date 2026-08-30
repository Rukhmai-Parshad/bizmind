from django.contrib import admin
from .models import Decision

# =========================
# DECISION ADMIN (IMPORTANT)
# =========================
@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):

    list_display = (
        'dataset',
        'rule_name',
        'title',
        'confidence',
        'created_at',
    )

    list_filter = ('rule_name',)
    search_fields = ('title', 'explanation')

    readonly_fields = (
        'dataset',
        'rule_name',
        'title',
        'recommendation',
        'explanation',
        'confidence',
        'created_at',
    )

    # Decisions are system output → never editable
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True