from rest_framework import status
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from django.shortcuts import get_object_or_404
from .serializers import FavoriteSerializer
from recipes.models import Recipe, Cart, Favorite


class CreateDeleteMixins(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    pass


class CartFavorite:
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'recipe_id': self.kwargs.get('recipe_id')})
        return context

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            recipe=get_object_or_404(
                Recipe, id=self.kwargs.get('recipe_id')
            )
        )

    def delete(self, request, recipe_id, serializer):
        if serializer == FavoriteSerializer:
            model = Favorite
        else:
            model = Cart
        get_object_or_404(
            model,
            user=request.user,
            recipe_id=recipe_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
