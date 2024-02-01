from colorfield.fields import ColorField
from django.db import models

from users.models import CustomUser


class Tag(models.Model):
    name = models.CharField(
        max_length=50, unique=True, verbose_name="Название"
    )
    color = ColorField(
        default="#FF0000",
        verbose_name="цвет",
    )
    slug = models.SlugField(
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
        max_length=100,
        verbose_name="Название",
    )
    measurement_unit = models.CharField(
        max_length=50,
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
        blank=False,
        on_delete=models.CASCADE,
        verbose_name="Автор",
    )
    name = models.CharField(max_length=100, verbose_name="Название")
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
        verbose_name="Время приготовления",
        blank=False,
    )

    class Meta:
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
    amount = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецепта"
        unique_together = ("recipe", "ingredient")

    def __str__(self):
        return (f"{self.ingredient.name} - {self.amount}"
                f" {self.ingredient.measurement_unit}")


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
