from email.mime import base
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import *


app_name = 'api'
router = DefaultRouter()
router.register('users', CreateUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]