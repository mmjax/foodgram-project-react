from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet
from django.shortcuts import get_object_or_404
from recipes.models import Recipe


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
