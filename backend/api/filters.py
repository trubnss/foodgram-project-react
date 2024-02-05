from django_filters import rest_framework as filters

from rest_framework.filters import SearchFilter

from recipes.models import Recipe


class IngredientSearchFilter(SearchFilter):
    search_param = "name"


class RecipeFilter(filters.FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")
    author = filters.AllValuesMultipleFilter(field_name="author__id")
    is_favorited = filters.BooleanFilter(method="filter_is_special")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_is_special")

    class Meta:
        model = Recipe
        fields = ("tags", "author", "is_favorited", "is_in_shopping_cart")

    def filter_is_special(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset.none()

        filter_params = {}
        if name == "is_favorited":
            filter_params["favorite_recipes__user"] = (
                self.request.user if value else None
            )
        elif name == "is_in_shopping_cart":
            filter_params["shopping_list_recipes__user"] = (
                self.request.user if value else None
            )

        filter_params = {
            k: v for k, v in filter_params.items() if v is not None
        }

        if filter_params:
            return queryset.filter(**filter_params)

        return queryset
