from functools import partial
from turtle import st
from django.shortcuts import get_list_or_404, get_object_or_404
from djoser.views import UserViewSet
from http import HTTPStatus
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action

from .mixins import CreateDeleteMixins
from recipes.models import *
from users.models import User
from .serializers import *


class CreateUserViewSet(UserViewSet):
    serializer_class = RegistrationSerializer

    def get_queryset(self):
        return User.objects.all()


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(viewsets.ModelViewSet):
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


class SubscriptionListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return Subscribe.objects.filter(user=self.request.user)


class SubscriptionViewSet(CreateDeleteMixins, mixins.ListModelMixin):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return Subscribe.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['following_id'] = self.kwargs.get('users_id')
        return context

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            following=get_object_or_404(
                User, id=self.kwargs.get('users_id')
            ))

    def delete(self, request, users_id):
        get_object_or_404(
            Subscribe,
            user=request.user,
            following=users_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(CreateDeleteMixins):
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('recipe_id')
        return context

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            recipe=get_object_or_404(
                Recipe, id=self.kwargs.get('recipe_id')
            ))

    def delete(self, request, recipe_id):
        get_object_or_404(
            Favorite,
            user=self.request.user,
            recipe=recipe_id
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartViewSet(CreateDeleteMixins):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('recipe_id')
        return context

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            recipe=get_object_or_404(
                Recipe, id=self.kwargs.get('recipe_id')
            ))

    def delete(self, request, recipe_id):
        get_object_or_404(
            Cart,
            user=request.user,
            recipe_id=recipe_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DownloadCartViewSet(viewsets.ModelViewSet):
    pass
