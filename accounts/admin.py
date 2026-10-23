from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    # 🔐 who can see Users module
    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.role == 'ADMIN'

    # 🔐 who can view users list / detail
    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.role == 'ADMIN'

    readonly_fields = ('consented_at', 'date_joined')
    list_display = ('email', 'role', 'is_active', 'is_staff')
    ordering = ('email',)
    search_fields = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {
            'fields': (
                'role',
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),
        ('Consent record', {'fields': ('consented_at', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'role', 'password1', 'password2'),
        }),
    )
