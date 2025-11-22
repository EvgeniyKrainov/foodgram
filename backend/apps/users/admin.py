from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from . import models


@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "pk",
        "email",
        "first_name",
        "last_name",
        "avatar",
    )
    list_filter = ("username", "email")
    search_fields = ("username", "email")
    empty_value_display = "-пусто-"

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name",
                                      "last_name",
                                      "email",
                                      "avatar")}),
        ("Permissions", {"fields": ("is_active",
                                    "is_staff",
                                    "is_superuser",
                                    "groups",
                                    "user_permissions")}),
        ("Important dates", {"fields": ("last_login",
                                        "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username",
                       "email",
                       "first_name",
                       "last_name",
                       "password1",
                       "password2",
                       "avatar"),
        }),
    )


@admin.register(models.Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "author")
    list_editable = ("user", "author")
    empty_value_display = "-пусто-"
