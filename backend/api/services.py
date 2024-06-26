from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response

from api.serializers import RecipeLightSerializer
from recipes.models import Recipe


class RecipeListService:
    """
    Сервис для добавления и удаления рецептов из списка избранных или списка покупок
    """

    @staticmethod
    def add(user, recipe_id, model, error_message):
        """
        Добавляет рецепт в список избранных или списка покупок пользователя.

        :param user: Пользователь, которому принадлежит список
        :param recipe_id: Идентификатор рецепта, который нужно добавить
        :param model: Модель для связи рецепта с пользователем (FavoriteRecipe или ShoppingListRecipe)
        :param error_message: Сообщение об ошибке, если рецепт не удалось добавить
        :return: Ответ с данными добавленного рецепта или сообщением об ошибке
        """

        recipe = Recipe.objects.filter(pk=recipe_id).first()
        if not recipe:
            return Response(
                {"message": "Рецепт не найден."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        _, created = model.objects.get_or_create(user=user, recipe=recipe)
        if created:
            serialized_recipe = RecipeLightSerializer(recipe)
            return Response(
                serialized_recipe.data, status=status.HTTP_201_CREATED
            )
        return Response(
            {"message": error_message}, status=status.HTTP_400_BAD_REQUEST
        )

    #Удаляет рецепт из списка избранных или списка покупок пользователя.
    @staticmethod
    def remove(user, recipe_id, model, error_message):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        item = model.objects.filter(user=user, recipe=recipe)
        if item.exists():
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"message": error_message}, status=status.HTTP_400_BAD_REQUEST
        )
