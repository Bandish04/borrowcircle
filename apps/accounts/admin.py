from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, ReliabilitySummary

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'role', 'account_status', 'is_verified', 'is_staff')
    list_filter = ('role', 'account_status', 'is_verified', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('BorrowCircle Info', {'fields': ('role', 'account_status', 'is_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('BorrowCircle Info', {'fields': ('email', 'role', 'account_status', 'is_verified')}),
    )
    search_fields = ('email', 'username')
    ordering = ('email',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile)
admin.site.register(ReliabilitySummary)