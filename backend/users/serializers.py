import re
from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.models import Follow, Recipe
from users.models import User
import api.serializers


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer для чтения / создания пользователя модели User.
    Переопределён метод create для возможности получения токена по
    кастомным url. - шифрование пароля по правилам djosera.
    """

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
            "is_subscribed",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "is_subscribed": {"read_only": True},
        }

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if (request and hasattr(request, "user")
                and not request.user.is_anonymous):
            return Follow.objects.filter(user=request.user,
                                         author=obj).exists()
        return False

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get("request")
        if request and hasattr(request, "method") and request.method == "POST":
            ret.pop("is_subscribed", None)
        return ret

    def validate_username(self, value):
        if not re.match(r"^[\w.@+-]+$", value):
            raise serializers.ValidationError()
        return value


class FollowSerializer(serializers.ModelSerializer):
    """Serializer для модели Follow."""

    email = serializers.ReadOnlyField(source="author.email")
    id = serializers.ReadOnlyField(source="author.id")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        if not user.is_anonymous:
            return Follow.objects.filter(user=obj.user,
                                         author=obj.author).exists()
        return False

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        recipes = Recipe.objects.filter(author=obj.author)
        if limit and limit.isdigit():
            recipes = recipes[: int(limit)]
        return api.serializers.RecipeMiniSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def validate(self, data):
        author = self.context.get("author")
        user = self.context.get("request").user
        if Follow.objects.filter(author=author, user=user).exists():
            raise ValidationError(
                detail="Вы уже подписаны на этого пользователя!",
                code=status.HTTP_400_BAD_REQUEST,
            )
        if user == author:
            raise ValidationError(
                detail="Невозможно подписаться на себя!",
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data
