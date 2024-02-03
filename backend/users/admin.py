from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser
from recipes.models import Recipe


class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'is_staff',
        'get_recipes_count',
        'get_subscribers_count',
    )
    list_filter = (
        'username',
        'email',
    )

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    get_recipes_count.short_description = 'Количество рецептов'

    def get_subscribers_count(self, obj):
        return obj.subscribers.count()

    get_subscribers_count.short_description = ('Количество'
                                               ' подписчиков')


admin.site.register(CustomUser, CustomUserAdmin)
