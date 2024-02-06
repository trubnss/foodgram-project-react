from django.contrib import admin
from django.forms import CheckboxSelectMultiple

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingList,
    Tag,
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "color",
        "slug",
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "measurement_unit",
    )
    list_filter = ("name",)
    search_fields = ("name",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "author",
        "get_tags",
        "get_ingredients",
        "get_favorites_count",
    )
    list_filter = (
        "author",
        "name",
        "tags",
    )
    inlines = (RecipeIngredientInline,)

    @admin.display(description="Теги")
    def get_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])

    @admin.display(description="Ингредиенты")
    def get_ingredients(self, obj):
        return ", ".join(
            [ingredient.name for ingredient in obj.ingredients.all()]
        )

    @admin.display(description="Кол-во добавлений в избранное")
    def get_favorites_count(self, obj):
        return obj.favorite_recipes.count()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "tags":
            kwargs["widget"] = CheckboxSelectMultiple()
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        "recipe",
        "ingredient",
        "amount",
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = ("user", "recipe")


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = ("user", "recipe")
