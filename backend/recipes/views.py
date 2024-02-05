from django.db.models import Sum
from django.http import HttpResponse
from django.utils.text import slugify
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.filters import IngredientSearchFilter, RecipeFilter
from api.paginations import CustomPagination
from api.permissions import IsRecipeAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)
from api.services import RecipeListService
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingList,
    Tag,
)


class TagViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_class = [AllowAny]
    pagination_class = None


class IngredientViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = (IngredientSearchFilter,)
    search_fields = ["^name"]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsRecipeAuthorOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(author=request.user)

        read_serializer = RecipeReadSerializer(
            recipe, context={"request": request}
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()

        read_serializer = RecipeReadSerializer(
            recipe, context={"request": request}
        )
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=[])
    def favorite(self, request, pk=None):
        pass

    @favorite.mapping.post
    def add_favorite(self, request, *args, **kwargs):
        recipe_id = kwargs.get("pk")
        response = RecipeListService.add(
            request.user, recipe_id, Favorite, "Рецепт уже в избранном."
        )
        return response

    @favorite.mapping.delete
    def remove_favorite(self, request, *args, **kwargs):
        recipe_id = kwargs.get("pk")
        response = RecipeListService.remove(
            request.user, recipe_id, Favorite, "Рецепт не найден в избранном."
        )
        return response

    @action(detail=True, methods=[])
    def shopping_cart(self, request, *args, **kwargs):
        pass

    @shopping_cart.mapping.post
    def add_to_shopping_cart(self, request, *args, **kwargs):
        recipe_id = kwargs.get("pk")
        response = RecipeListService.add(
            request.user,
            recipe_id,
            ShoppingList,
            "Рецепт уже в списке покупок.",
        )
        return response

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, *args, **kwargs):
        recipe_id = kwargs.get("pk")
        response = RecipeListService.remove(
            request.user,
            recipe_id,
            ShoppingList,
            "Рецепт не найден в списке покупок.",
        )
        return response

    @action(detail=False, methods=["get"])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_items = ShoppingList.objects.filter(
            user=user
        ).values_list("recipe", flat=True)

        ingredients_summary = (
            RecipeIngredient.objects.filter(recipe__in=shopping_cart_items)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        content = "Список ингредиентов для покупки:\n"
        for ingredient in ingredients_summary:
            name = ingredient["ingredient__name"]
            measurement_unit = ingredient["ingredient__measurement_unit"]
            amount = ingredient["total_amount"]
            content += f"{name}: {amount} {measurement_unit}\n"

        filename = f"shopping_cart_{user.username}.txt"
        slugified_filename = slugify(filename)

        response = HttpResponse(content, content_type="text/plain")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="{slugified_filename}"'
        return response
