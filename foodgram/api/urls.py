from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
     CreateUserViewSet, SubscriptionListViewSet,
     TagViewSet, IngredientViewSet, RecipesViewSet, CartViewSet,
     SubscriptionViewSet, FavoriteViewSet, DownloadCartViewSet,
)

app_name = 'api'
router_v1 = DefaultRouter()
router_v1.register(
     'users/subscriptions', SubscriptionListViewSet, basename='subscriptions'
     )
router_v1.register('users', CreateUserViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('recipes', RecipesViewSet, basename='recipes')
router_v1.register(
     r'recipes/(?P<recipe_id>\d+)/shopping_cart', CartViewSet,
     basename='shopping_cart'
     )
router_v1.register(
     r'users/(?P<users_id>\d+)/subscribe', SubscriptionViewSet,
     basename='subscribe'
     )
router_v1.register(
     r'recipes/(?P<recipe_id>\d+)/favorite', FavoriteViewSet,
     basename='favorite'
     )


urlpatterns = [
     path(
          'recipes/download_shopping_cart/',
          DownloadCartViewSet.as_view({'get': 'download_shopping_cart'}),
          name='download'),
     path('', include(router_v1.urls)),
     path('auth/', include('djoser.urls.authtoken')),
]
