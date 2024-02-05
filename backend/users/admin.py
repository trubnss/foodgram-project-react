from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from rest_framework.authtoken.models import TokenProxy

from recipes.models import Recipe
from .models import CustomUser, Subscription


class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "is_staff",
        "get_recipes_count",
        "get_subscribers_count",
    )
    list_filter = (
        "username",
        "email",
    )

    @admin.display(description="Количество рецептов")
    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    @admin.display(description="Количество" " подписчиков")
    def get_subscribers_count(self, obj):
        return obj.followers.count()


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("subscriber", "subscribed_to")
    list_filter = ("subscriber", "subscribed_to")


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subscription)
admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
