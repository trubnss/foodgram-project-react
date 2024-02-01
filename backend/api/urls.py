from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from users.views import UserViewSet

from recipes.views import TagViewSet, RecipeViewSet, IngredientViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("recipes", RecipeViewSet)
router.register("tags", TagViewSet)
router.register("ingredients", IngredientViewSet)

urlpatterns = [
    path("", include(router.urls)),
    re_path(r"auth/", include("djoser.urls.authtoken")),
]
