from functools import partial
from turtle import st
from django.shortcuts import get_list_or_404, get_object_or_404
from djoser.views import UserViewSet
from http import HTTPStatus
from rest_framework import viewsets, status
from rest_framework.response import Response

from .mixins import ListRetriveViewSet
from recipes.models import *
from users.models import User
from .serializers import *


ALREADY_SIGNED = {'errors': 'Вы уже подписаны на этого автора'}
ALREADY_FAVORITE = {'errors': 'Этот рецепт уже добавлен в избранное'}
CANT_SUBSCRIBE_TO_YOURSELF = {'errors': 'Вы не можете подписаться на самого себя'}
WASNT_SIGNED = {'errors': 'Вы не были подписаны на этого атора'}
WASNT_FAVORITE = {'errors': 'Этот рецепт не был добавлен в избранное'}


class CreateUserViewSet(UserViewSet):
    serializer_class = RegistrationSerializer

    def get_queryset(self):
        return User.objects.all()


class TagViewSet(ListRetriveViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(ListRetriveViewSet):
    serializer_class = IngredientsSerializer
    queryset = Ingredient.objects.all()


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeGetSerializer
        return RecipePostSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serializer = RecipeGetSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partisl', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        serializer = RecipeGetSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer

    def get_subscribtion_serializer(self, *args, **kwargs):
        kwargs.setdefault('context', self.get_serializer_context())
        return SubscriptionSerializer(*args, **kwargs)

    def get_queryset(self):
        return get_list_or_404(User, following__user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        user = get_object_or_404(User, id=self.kwargs.get('users_id'))
        if Subscribe.objects.filter(user=request.user, following__id=user.id).exists():
            return Response(ALREADY_SIGNED, status=status.HTTP_400_BAD_REQUEST)
        if user == request.user:
            return Response(CANT_SUBSCRIBE_TO_YOURSELF, status=status.HTTP_400_BAD_REQUEST)
        subscribe = Subscribe.objects.create(
            user=request.user, following=user
        )
        serializer = self.get_subscribtion_serializer(subscribe.following)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def delete(self, request, *args, **kwargs):
        if not Subscribe.objects.filter(user=request.user.id, following__id=self.kwargs['users_id']).exists():
            return Response(WASNT_SIGNED, status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(
            Subscribe,
            user__id=request.user.id, following__id=self.kwargs['users_id']
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()
    model = Favorite

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs['recipes_id']
        if Favorite.objects.filter(user=request.user.id, recipe__id=recipe_id).exists():
            return Response(ALREADY_FAVORITE, status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.model.objects.create(
            user=request.user, recipe=recipe)
        return Response(status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = int(self.kwargs['recipes_id'])
        if not Favorite.objects.filter(user=request.user, recipe__id=recipe_id).exists():
            return Response(WASNT_FAVORITE, status=status.HTTP_404_NOT_FOUND)
        user_id = request.user.id
        object = get_object_or_404(
            self.model, user__id=user_id, recipe__id=recipe_id)
        object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    