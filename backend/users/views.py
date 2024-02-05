from django.contrib.auth import update_session_auth_hash
from django.db import models
from django.db.models import Case, Value, When
from djoser.serializers import SetPasswordSerializer

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.paginations import CustomPagination
from api.serializers import (
    ManageSubscriptionSerializer,
    SubscriptionSerializer,
    UserSerializers,
)
from .models import CustomUser, Subscription


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
