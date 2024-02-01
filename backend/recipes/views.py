from collections import defaultdict

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, status
from django.utils.text import slugify

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingList,
    RecipeIngredient,
)

from api.serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    FavoriteSerializer,
    ShoppingListSerializer,
    RecipeIngredientSerializer,
)
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
)

from api.filters import IngredientSearchFilter, RecipeFilter

from api.paginations import CustomPagination
from rest_framework.response import Response

from api.permissions import IsRecipeAuthorOrReadOnly


class TagViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_class = [AllowAny]


class IngredientViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = (IngredientSearchFilter,)
    search_fields = ["^name"]


class BaseRecipeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    not_exist_message = "Рецепта не существует"
    already_exists_message = "Рецепт уже существует в данном списке."
    removed_message = "Рецепт удален из списка."

    def add(self, request, pk=None):
        user = request.user
        recipe = Recipe.objects.filter(pk=pk).first()
        if not recipe:
            return Response(
                {"message": self.not_exist_message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if self.model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {"message": self.already_exists_message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item = self.model.objects.create(user=user, recipe=recipe)
        serialized_recipe = self.serializer_class(item.recipe)
        return Response(serialized_recipe.data, status=status.HTTP_201_CREATED)

    def remove(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        item_exists = self.model.objects.filter(user=user,
                                                recipe=recipe).exists()
        if not item_exists:
            return Response(
                {"message": self.not_exist_message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item = self.model.objects.get(user=user, recipe=recipe)
        item.delete()
        return Response(
            {"message": self.removed_message},
            status=status.HTTP_204_NO_CONTENT,
        )


class FavoriteViewSet(BaseRecipeViewSet):
    model = Favorite
    serializer_class = FavoriteSerializer
    already_exists_message = "Рецепт уже в избранном."
    removed_message = "Рецепт удален из избранного."


class ShoppingCartViewSet(BaseRecipeViewSet):
    model = ShoppingList
    serializer_class = ShoppingListSerializer
    already_exists_message = "Рецепт уже в списке покупок."
    removed_message = "Рецепт удален из списка покупок."


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsRecipeAuthorOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        tag_ids = data.get("tags", [])
        ingredient_data = data.get("ingredients", [])

        serializer = self.get_serializer(
            data=data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        recipe = self.perform_create(serializer)

        recipe.tags.set(tag_ids)

        for ingredient in ingredient_data:
            ingredient_obj = get_object_or_404(Ingredient, id=ingredient["id"])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_obj,
                amount=ingredient["amount"],
            )

        response_data = RecipeSerializer(
            recipe, context={"request": request}
        ).data
        response_data["tags"] = TagSerializer(
            Tag.objects.filter(id__in=tag_ids),
            many=True,
            context={"request": request},
        ).data
        response_data["ingredients"] = RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(recipe=recipe),
            many=True,
            context={"request": request},
        ).data

        return Response(response_data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        data = request.data.copy()
        tag_ids = data.get("tags", [])
        ingredient_data = data.pop("ingredients", [])

        instance = self.get_object()

        serializer = self.get_serializer(
            instance, data=data, partial=kwargs.get("partial", False)
        )

        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()

        recipe.tags.set(tag_ids)
        RecipeIngredient.objects.filter(recipe=recipe).delete()

        for ingredient in ingredient_data:
            ingredient_obj = get_object_or_404(Ingredient, id=ingredient["id"])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_obj,
                amount=ingredient["amount"],
            )

        updated_recipe = self.get_serializer(recipe).data
        return Response(updated_recipe, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post", "delete"])
    def favorite(self, request, pk=None):
        favorite_viewset = FavoriteViewSet()
        if request.method == "POST":
            return favorite_viewset.add(request, pk)
        else:
            return favorite_viewset.remove(request, pk)

    @action(detail=True, methods=["post", "delete"])
    def shopping_cart(self, request, pk=None):
        shopping_cart_viewset = ShoppingCartViewSet()
        if request.method == "POST":
            return shopping_cart_viewset.add(request, pk)
        else:
            return shopping_cart_viewset.remove(request, pk)

    @action(detail=False, methods=["get"])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_recipes = ShoppingList.objects.filter(
            user=user
        ).select_related("recipe")

        ingredients_summary = defaultdict(float)

        for item in shopping_cart_recipes:
            recipe = item.recipe
            recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)

            for recipe_ingredient in recipe_ingredients:
                ingredient = recipe_ingredient.ingredient
                amount = recipe_ingredient.amount
                ingredient_name = ingredient.name
                measurement_unit = ingredient.measurement_unit

                ingredients_summary[
                    (ingredient_name, measurement_unit)
                ] += amount

        content = "Список ингредиентов для покупки:\n"
        for (
                ingredient_name,
                measurement_unit,
        ), amount in ingredients_summary.items():
            content += f"{ingredient_name}: {amount} {measurement_unit}\n"

        filename = f"shopping_cart_{user.username}.txt"
        slugified_filename = slugify(filename)

        response = HttpResponse(content, content_type="text/plain")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="{slugified_filename}"'
        return response
