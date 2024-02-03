from django.contrib import admin
from .models import Tag, Ingredient, Recipe, RecipeIngredient


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
        "get_ingredients",
        "get_favorites_count",
    )
    list_filter = (
        "author",
        "name",
        "tags",
    )
    inlines = (RecipeIngredientInline,)

    def get_ingredients(self, obj):
        return ", ".join([ingredient.name for ingredient in
                          obj.ingredients.all()])

    get_ingredients.short_description = "Ингредиенты"

    def get_favorites_count(self, obj):
        return obj.favorite_recipes.count()
    get_favorites_count.short_description = 'Кол-во добавлений в избранное'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        "recipe",
        "ingredient",
        "amount",
    )
