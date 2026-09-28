from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserProfile


@admin.register(User)
class UserAdminConfig(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "username", "is_staff", "is_active")
    search_fields = ("email", "username", "first_name", "last_name")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "department", "phone")
    list_filter = ("role", "department")
    search_fields = ("user__email", "user__username", "department")
