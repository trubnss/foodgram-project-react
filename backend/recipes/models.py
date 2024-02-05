from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from colorfield.fields import ColorField

from users.models import CustomUser
from api.constants import (
    MAX_AMOUNT,
    MAX_COOKING_TIME,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
    RECIPE_MODEL_MAX_LENGTH,
)


class Tag(models.Model):
    name = models.CharField(
        max_length=RECIPE_MODEL_MAX_LENGTH,
        unique=True,
        verbose_name="Название",
    )
    color = ColorField(
        default="#FF0000",
        verbose_name="цвет",
    )
    slug = models.SlugField(
        max_length=RECIPE_MODEL_MAX_LENGTH,
        unique=True,
        verbose_name="слаг",
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=RECIPE_MODEL_MAX_LENGTH,
        verbose_name="Название",
    )
    measurement_unit = models.CharField(
        max_length=RECIPE_MODEL_MAX_LENGTH,
        verbose_name="Единица измерения",
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        CustomUser,
        related_name="author_recipes",
        blank=False,
        on_delete=models.CASCADE,
        verbose_name="Автор",
    )
    name = models.CharField(
        max_length=RECIPE_MODEL_MAX_LENGTH, verbose_name="Название"
    )
    image = models.ImageField(
        upload_to="",
        verbose_name="Картинка",
        blank=False,
    )
    text = models.TextField(
        verbose_name="Описание",
    )
    ingredients = models.ManyToManyField(
        "Ingredient",
        through="RecipeIngredient",
        verbose_name="Ингредиенты",
        related_name="recipes",
        blank=False,
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Теги",
        blank=False,
    )
    cooking_time = models.PositiveIntegerField(
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message="Время приготовления не может быть меньше 1 минуты.",
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message="Время приготовления слишком большое.",
            ),
        ],
        verbose_name="Время приготовления",
        blank=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        "Recipe",
        related_name="recipe_ingredients",
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        "Ingredient",
        on_delete=models.CASCADE,
        verbose_name="Ингредиент",
    )
    amount = models.PositiveIntegerField(
        validators=[
            MinValueValidator(
                MIN_AMOUNT, message="Количество не может быть меньше 1."
            ),
            MaxValueValidator(
                MAX_AMOUNT, message="Количество слишком большое."
            ),
        ],
        verbose_name="Количество",
    )

    class Meta:
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецепта"
        constraints = [
            models.UniqueConstraint(
                fields=("recipe", "ingredient"),
                name="unique_recipe_ingredient",
            ),
        ]

    def __str__(self):
        return (
            f"{self.ingredient.name} - {self.amount}"
            f" {self.ingredient.measurement_unit}"
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        related_name="favorite_recipes",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class ShoppingList(models.Model):
    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="shopping_lists",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        related_name="shopping_list_recipes",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Список продуктов"
        verbose_name_plural = "Списки продуктов"

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"
