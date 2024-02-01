from django.contrib.auth import update_session_auth_hash
from djoser.serializers import SetPasswordSerializer
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
)
from rest_framework.response import Response

from .models import CustomUser
from api.serializers import (
    UserSerializers,
    SubscriptionSerializer,
    RecipeSerializer,
)

from api.paginations import CustomPagination

from recipes.models import Recipe


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

    def perform_create(self, serializer):
        validated_data = serializer.validated_data
        user = CustomUser.objects.create_user(**validated_data)

        response_data = {
            "email": user.email,
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

        serializer.instance = user
        serializer.fields.pop("is_subscribed", None)
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def subscriptions(self, request, pk=None):
        return SubscriptionViewSet.list(self, request)

    @action(detail=True, methods=["post", "delete"])
    def subscribe(self, request, pk=None):
        subscription_viewset = SubscriptionViewSet()
        if request.method == "POST":
            return subscription_viewset.create(request, pk=pk)
        elif request.method == "DELETE":
            return subscription_viewset.destroy(request, pk=pk)

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
        subscribed_users = user.subscribers.all()
        paginated_subscribed_users = self.paginate_queryset(subscribed_users)
        serializer = SubscriptionSerializer(
            paginated_subscribed_users, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    def create(self, request, pk=None):
        if not CustomUser.objects.filter(pk=pk).exists():
            return Response(
                {"message": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )

        author = CustomUser.objects.get(pk=pk)
        user = request.user

        if author == user:
            return Response(
                {
                    "message": "Нельзя подписаться или"
                               " отписаться на самого себя"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if author in user.subscribers.all():
            return Response(
                {"message": "Вы уже подписаны на этого пользователя"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_subscribed = True
        user.subscribers.add(author)
        user.save()
        recipes = Recipe.objects.filter(author=author)
        serializer = SubscriptionSerializer(user, context={"request": request})
        serialized_data = serializer.data

        serialized_data["recipes"] = RecipeSerializer(
            recipes, many=True, context={"request": request}
        ).data
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        if not CustomUser.objects.filter(pk=pk).exists():
            return Response(
                {"message": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )

        author = CustomUser.objects.get(pk=pk)
        user = request.user

        if author not in user.subscribers.all():
            return Response(
                {"message": "Вы еще не подписаны на этого пользователя"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_subscribed = False
        user.subscribers.remove(author)
        user.save()

        return Response(
            {"message": "Вы отписались от этого пользователя"},
            status.HTTP_204_NO_CONTENT,
        )
