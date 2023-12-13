from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework import mixins
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS

from users.models import User
from api.models import Recipe, Tag, Ingredient, Favorite, ShoppingCart
from api.serializers import (
    RecipeListSerializer,
    TagSerializer,
    IngredientSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
    RecipeWriteSerializer,
)
from .services import shopping_cart
from api.permissions import IsOwnerOrAdminOrReadOnly
from api.filters import IngredientSearchFilter, RecipeFilter
from api.paginations import ApiPagination


class TagViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Функция для модели тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Функция для модели ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ("^name",)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет модели Recipe: [GET, POST, DELETE, PATCH]."""

    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    pagination_class = ApiPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeListSerializer
        return RecipeWriteSerializer

    @action(
        detail=True, methods=["post", "delete"],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get("pk")
        user = self.request.user

        recipe = Recipe.objects.filter(id=recipe_id).first()

        if request.method == "POST":
            if not recipe:
                return Response(
                    {"errors": "Рецепт не найден!"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            favorite_entry, created = Favorite.objects.get_or_create(
                author=user, recipe=recipe
            )
            if not created:
                return Response(
                    {"errors": "Рецепт уже добавлен!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = FavoriteSerializer(favorite_entry)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            if not recipe:
                return Response(
                    {"errors": "Рецепт не найден!"},
                    status=status.HTTP_404_NOT_FOUND
                )
            favorite_entry = Favorite.objects.filter(
                author=user, recipe=recipe).first()
            if favorite_entry:
                favorite_entry.delete()
                return Response(
                    "Рецепт успешно удалён из избранного.",
                    status=status.HTTP_204_NO_CONTENT,
                )
            else:
                return Response(
                    {"errors": "Рецепт не был добавлен в избранное!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    @action(
        detail=True, methods=["post", "delete"],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, **kwargs):
        """
        Получить / Добавить / Удалить  рецепт
        из списка покупок у текущего пользоватля.
        """

        recipe_id = self.kwargs.get("pk")
        user = self.request.user

        recipe = Recipe.objects.filter(id=recipe_id).first()

        if request.method == "POST":
            if not recipe:
                return Response(
                    {"errors": "Рецепт не найден!"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if ShoppingCart.objects.filter(author=user,
                                           recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже добавлен!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = ShoppingCartSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == "DELETE":
            if not recipe:
                return Response(
                    {"errors": "Рецепт не найден!"},
                    status=status.HTTP_404_NOT_FOUND
                )

            shopping_cart_entry = ShoppingCart.objects.filter(
                author=user, recipe=recipe
            ).first()
            if shopping_cart_entry:
                shopping_cart_entry.delete()
                return Response(
                    "Рецепт успешно удалён из списка покупок.",
                    status=status.HTTP_204_NO_CONTENT,
                )
            else:
                return Response(
                    {"errors": "Рецепт не был добавлен в список покупок!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    @action(detail=False, methods=["get"],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """
        Скачать список покупок для выбранных рецептов,
        данные суммируются.
        """
        author = User.objects.get(id=self.request.user.pk)
        if author.shopping_cart.exists():
            return shopping_cart(self, request, author)
        return Response("Список покупок пуст.",
                        status=status.HTTP_404_NOT_FOUND)
