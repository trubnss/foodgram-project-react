from django.db.models import Sum, Case, Value, When
from django.http import HttpResponse
from django.utils.text import slugify
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import update_session_auth_hash
from django.db import models
from djoser.serializers import SetPasswordSerializer

from rest_framework import mixins, status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from api.filters import IngredientSearchFilter, RecipeFilter
from api.paginations import CustomPagination
from api.permissions import IsRecipeAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    ManageSubscriptionSerializer,
    SubscriptionSerializer,
    UserSerializers,
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
from users.models import CustomUser, Subscription


class BaseViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    permission_classes = [AllowAny]
    pagination_class = None


class TagViewSet(BaseViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(BaseViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
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

    """
    Не могу убрать переопределение методов, сразу все ломается,
    поскольку возвращаю ответ другим сериализатором
    в рамках вызванного метода.
    """

    def get_serializer_response(self, recipe, context, status_code):
        read_serializer = RecipeReadSerializer(recipe, context=context)
        return Response(read_serializer.data, status=status_code)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        return self.get_serializer_response(
            recipe, {"request": request}, status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        return self.get_serializer_response(
            recipe, {"request": request}, status.HTTP_200_OK
        )

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

        ingredients_summary = (
            RecipeIngredient.objects.filter(
                recipe__shopping_list_recipes__user=user
            )
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


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializers
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == "create":
            return []
        elif self.action == "me":
            return [permissions.IsAuthenticated()]
        else:
            return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        user = self.request.user
        queryset = CustomUser.objects.all()
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_subscribed=Case(
                    When(followers__subscriber=user, then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                )
            )
        return queryset

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def subscriptions(self, request, pk=None):
        return SubscriptionViewSet.list(self, request)

    @action(detail=True, methods=["post", "delete"])
    def subscribe(self, request, pk=None):
        subscription_viewset = SubscriptionViewSet(request=request)
        if request.method == "POST":
            return subscription_viewset.subscribe(request, pk)
        else:
            return subscription_viewset.unsubscribe(request, pk)

    @action(detail=False, methods=["post"])
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = request.user
            new_password = serializer.validated_data["new_password"]
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            return Response(
                {"message": "Пароль успешно изменен"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


class SubscriptionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def list(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(
            subscriber=user
        ).select_related("subscribed_to")

        subscribed_users = [
            subscription.subscribed_to for subscription in subscriptions
        ]

        page = self.paginate_queryset(subscribed_users)
        if page is not None:
            serialized_data = SubscriptionSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serialized_data.data)

        serialized_data = SubscriptionSerializer(
            subscribed_users, many=True, context={"request": request}
        )
        return Response(serialized_data.data)

    def subscribe(self, request, pk=None):
        serializer = ManageSubscriptionSerializer(
            data={},
            context={
                "request": request,
                "pk": pk,
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        subscribed_user = CustomUser.objects.get(pk=pk)
        return Response(
            SubscriptionSerializer(
                subscribed_user, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def unsubscribe(self, request, pk=None):
        user_to_unsubscribe = get_object_or_404(CustomUser, pk=pk)
        serializer = ManageSubscriptionSerializer(
            instance=user_to_unsubscribe,
            context={
                "request": request,
                "subscriber": request.user,
                "subscribed_to": user_to_unsubscribe,
                "pk": pk,
            },
        )
        result = serializer.remove_subscription()
        return Response(result, status=status.HTTP_204_NO_CONTENT)
