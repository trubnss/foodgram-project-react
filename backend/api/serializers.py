import re

from django.core.validators import MinValueValidator, MaxValueValidator
from drf_extra_fields.fields import Base64ImageField

from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from users.models import CustomUser, Subscription
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)
from .constants import (
    MIN_AMOUNT,
    MAX_AMOUNT,
    MIN_COOKING_TIME,
    MAX_COOKING_TIME,
)


class UserSerializers(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
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
            "password": {"write_only": True, "required": False},
            "is_subscribed": {"read_only": True},
        }

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_authenticated and user != obj:
            return Subscription.objects.filter(
                subscriber=user, subscribed_to=obj
            ).exists()
        return False

    def validate_username(self, value):
        if not re.match(r"^[\w.@+-]+\Z", value):
            raise serializers.ValidationError(
                {
                    "message": "Имя пользователя содержит"
                    " недопустимые символы."
                }
            )

        if value.lower() == "me":
            raise serializers.ValidationError(
                {
                    "message": "Имя 'me' нельзя использовать"
                    " в качестве имени пользователя."
                }
            )

        return value


class CustomSetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    current_password = serializers.CharField()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount", "name", "measurement_unit")


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
        error_messages={
            "does_not_exist": "Ингредиент" " с id {pk_value} не существует."
        },
    )
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(
                MIN_AMOUNT, "Количество не может быть менее 1."
            ),
            MaxValueValidator(MAX_AMOUNT, "Количество слишком большое."),
        ]
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                "Время приготовления должно быть больше или равно 1.",
            ),
            MaxValueValidator(
                MAX_COOKING_TIME, "Время приготовления слишком большое."
            ),
        ]
    )

    class Meta:
        model = Recipe
        fields = [
            "name",
            "image",
            "text",
            "cooking_time",
            "tags",
            "ingredients",
        ]

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                {"message": "Поле image не может быть пустым."}
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                {"message": "Поле tags не может быть пустым."}
            )
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                {"message": "Теги не должны повторяться."}
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                {"message": "Поле ingredients не может быть пустым."}
            )
        ingredient_ids = [item["ingredient"].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {"message": "Ингредиенты не должны повторяться."}
            )
        return value

    def validate(self, data):
        if self.instance and (
            "tags" not in data or "ingredients" not in data
        ):
            raise serializers.ValidationError(
                {
                    "message": "Поля 'tags' и 'ingredients' должны "
                    "быть предоставлены при обновлении."
                }
            )
        return data

    def handle_tags(self, recipe, tags_data):
        recipe.tags.set(tags_data)

    def handle_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data["ingredient"],
                amount=ingredient_data["amount"],
            )

    def create(self, validated_data):
        tags_data = validated_data.pop("tags")
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)

        self.handle_tags(recipe, tags_data)
        self.handle_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.image = validated_data.get("image", instance.image)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )

        tags_data = validated_data.get("tags")
        if tags_data is not None:
            self.handle_tags(instance, tags_data)

        ingredients_data = validated_data.get("ingredients")
        if ingredients_data is not None:
            self.handle_ingredients(instance, ingredients_data)

        instance.save()
        return instance


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializers(read_only=True)
    image = Base64ImageField()
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source="recipe_ingredients", many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.favorites.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.shopping_lists.filter(recipe=obj).exists()
        return False


class RecipeLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="author_recipes.count")
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
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

    def get_recipes(self, obj):
        recipes_limit_param = self.context["request"].query_params.get(
            "recipes_limit"
        )
        recipes_limit = (
            int(recipes_limit_param)
            if recipes_limit_param and recipes_limit_param.isdigit()
            else None
        )
        recipes = obj.author_recipes.all()[:recipes_limit]
        return RecipeLightSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return Subscription.objects.filter(
                subscriber=user, subscribed_to=obj
            ).exists()
        return False


class ManageSubscriptionSerializer(serializers.Serializer):
    def create(self, validated_data):
        subscriber = self.context["request"].user
        pk = self.context["pk"]
        subscribed_to = get_object_or_404(CustomUser, pk=pk)

        if subscriber == subscribed_to:
            raise serializers.ValidationError(
                {"message": "Нельзя подписаться на самого себя."}
            )

        if Subscription.objects.filter(
            subscriber=subscriber, subscribed_to=subscribed_to
        ).exists():
            raise serializers.ValidationError(
                {"message": "Вы уже подписаны на этого пользователя."}
            )

        subscription = Subscription.objects.create(
            subscriber=subscriber, subscribed_to=subscribed_to
        )
        return subscription

    def remove_subscription(self):
        subscriber = self.context["subscriber"]
        pk = self.context["pk"]
        subscribed_to = get_object_or_404(CustomUser, pk=pk)
        subscription = Subscription.objects.filter(
            subscriber=subscriber, subscribed_to=subscribed_to
        )
        if subscription.exists():
            subscription.delete()
            return {"message": "Вы успешно отписались."}
        else:
            raise serializers.ValidationError(
                {"message": "Вы не подписаны на этого пользователя."}
            )
