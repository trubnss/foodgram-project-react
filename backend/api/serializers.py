from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from users.models import CustomUser

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingList,
    RecipeIngredient,
)


class UserSerializers(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
            "is_subscribed",
        ]
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "is_subscribed": {"read_only": True},
        }

    def get_is_subscribed(self, obj):
        if self.context["request"].user.is_authenticated:
            current_user = self.context["request"].user
            is_subscribed = current_user.subscribers.filter(pk=obj.id).exists()
            return is_subscribed
        return False


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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount", "name", "measurement_unit")


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializers(read_only=True)
    image = Base64ImageField(required=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    ingredients = RecipeIngredientSerializer(
        source="recipe_ingredients", many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
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
        ]

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return Favorite.objects.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return ShoppingList.objects.filter(recipe=obj).exists()
        return False

    def validate(self, data):
        tags = data.get("tags", [])
        if not tags:
            raise serializers.ValidationError(
                {"tags": "Поле tags не может быть пустым."}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {"tags": "Теги не должны повторяться."}
            )

        ingredients = self.context["request"].data.get("ingredients", [])
        if not ingredients:
            raise serializers.ValidationError(
                {"ingredients": "Поле ingredients не может быть пустым."}
            )

        ingredient_ids = [item["id"] for item in ingredients]
        if Ingredient.objects.filter(id__in=ingredient_ids).count() != len(
            ingredient_ids
        ):
            raise serializers.ValidationError(
                {
                    "ingredients": "Один или несколько"
                                   " ингредиентов не существуют."
                }
            )

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {"ingredients": "Ингредиенты не должны повторяться."}
            )

        for item in ingredients:
            amount = item.get("amount", 0)
            if int(amount) < 1:
                raise serializers.ValidationError(
                    {
                        "ingredients": "Количество ингредиента"
                                       " должно быть больше 0."
                    }
                )

        image = data.get("image", None)
        if image is None or image == "":
            raise serializers.ValidationError(
                {"image": "Поле image не может быть пустым."}
            )

        cooking_time = data.get("cooking_time", 0)
        if cooking_time < 1:
            raise serializers.ValidationError(
                {"cooking_time": '"cooking_time" должно быть больше 0.'}
            )

        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        tags_data = TagSerializer(instance.tags.all(), many=True).data
        representation["tags"] = tags_data
        print("Recipe Data:", representation)
        return representation


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]


class ShoppingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = RecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        ]
        extra_kwargs = {
            "is_subscribed": {"read_only": True},
        }

    def get_recipes(self, obj):
        subscribed_user = self.context["request"].user
        recipes = Recipe.objects.filter(
            author=obj, subscribers=subscribed_user
        )
        return RecipeSerializer(
            recipes, many=True, context={"request": self.context["request"]}
        ).data

    def get_recipes_count(self, obj):
        return len(self.get_recipes(obj)) if hasattr(obj, "recipes") else 0

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if "recipes" not in ret:
            ret["recipes"] = []
        return ret
