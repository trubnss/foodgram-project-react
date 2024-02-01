from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters

from recipes.models import Recipe


class IngredientSearchFilter(SearchFilter):
    search_param = "name"


class RecipeFilter(filters.FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")
    author = filters.NumberFilter(field_name="author__id")
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = ["tags", "author"]

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return (
                queryset.filter(favorite_recipes__user=self.request.user)
                if value
                else queryset
            )
        return queryset.none()

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return (
                queryset.filter(shopping_list_recipes__user=self.request.user)
                if value
                else queryset
            )
        return queryset.none()
