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
CANT_SUBSCRIBE_TO_YOURSELF = {'errors': 'Вы не можете подписаться на самого себя'}
WASNT_SIGNED = {'errors': 'Вы не были подписаны на этого атора'}


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
    serializer_class = RecipeSerializer


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
