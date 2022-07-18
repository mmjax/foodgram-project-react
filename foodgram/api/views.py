from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from reportlab.lib.pagesizes import A4
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .mixins import CreateDeleteMixins
from recipes.models import (Cart, Favorite, Ingredient,
                            Recipe, Subscribe, Tag, IngredientRecipe)
from users.models import User
from .serializers import (CustomUserSerializer, RegistrationSerializer,
                          TagSerializer, IngredientsSerializer,
                          RecipeGetSerializer, RecipePostSerializer,
                          SubscriptionSerializer, FavoriteSerializer,
                          CartSerializer)


class CreateUserViewSet(UserViewSet):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CustomUserSerializer
        return RegistrationSerializer

    def get_queryset(self):
        return User.objects.all()


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(ReadOnlyModelViewSet):
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
        partial = kwargs.pop('partial', False)
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'following_id': self.kwargs.get('users_id')})
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
        context.update({'recipe_id': self.kwargs.get('recipe_id')})
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
        context.update({'recipe_id': self.kwargs.get('recipe_id')})
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
    def download_shopping_cart(self, request):
        final_list = {}
        ingredients = IngredientRecipe.objects.filter(
            recipe__author=request.user).values_list(
            'ingredient__name', 'ingredient__measurement_unit',
            'amount')
        for item in ingredients:
            name = item[0]
            if name not in final_list:
                final_list[name] = {
                    'measurement_unit': item[1],
                    'amount': item[2]
                }
            else:
                final_list[name]['amount'] += item[2]
        pdfmetrics.registerFont(
            TTFont('KawashiroGothic', 'data/KawashiroGothic.ttf', 'UTF-8'))
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; ''filename="shopping_cart.pdf"'
            )
        page = canvas.Canvas(response, pagesize=A4)
        page.setFont('KawashiroGothic', size=18)
        page.drawString(250, 800, 'Корзина')
        page.setFont('KawashiroGothic', size=14)
        height = 770
        for i, (name, data) in enumerate(final_list.items(), start=1):
            if height > 20:
                page.drawString(70, height, (
                    f'{i}. {name} - {data["amount"]},'
                    f'{data["measurement_unit"]}'
                    ))
                height -= 20
        page.showPage()
        page.save()
        return response
