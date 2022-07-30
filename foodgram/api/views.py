from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet
from rest_framework import viewsets, status, mixins
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .filters import RecipeFilter, IngredientSearchFilter
from .mixins import CreateDeleteMixins, CartFavorite
from .pagination import RecipesSubscriptionsPagination
from .permissions import AuthorAdminOrReadOnly
from .serializers import (CustomUserSerializer, RegistrationSerializer,
                          TagSerializer, IngredientsSerializer,
                          RecipeGetSerializer, RecipePostSerializer,
                          SubscriptionSerializer, FavoriteSerializer,
                          CartSerializer)
from recipes.models import (Cart, Favorite, Ingredient,
                            Recipe, Subscribe, Tag, IngredientRecipe)
from users.models import User


class CreateUserViewSet(UserViewSet):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CustomUserSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return RegistrationSerializer

    def get_queryset(self):
        return User.objects.all()


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [AllowAny]
    queryset = Tag.objects.all()


class IngredientViewSet(ReadOnlyModelViewSet):
    serializer_class = IngredientsSerializer
    pagination_class = None
    permission_classes = [AllowAny]
    queryset = Ingredient.objects.all()
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filterset_class = RecipeFilter
    pagination_class = RecipesSubscriptionsPagination
    permission_classes = [AuthorAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeGetSerializer
        return RecipePostSerializer


class SubscriptionListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = SubscriptionSerializer
    pagination_class = RecipesSubscriptionsPagination

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


class FavoriteViewSet(CartFavorite, CreateDeleteMixins):
    serializer_class = FavoriteSerializer
    model = Favorite

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)


class CartViewSet(CartFavorite, CreateDeleteMixins):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    pagination_class = None
    model = Cart


class DownloadCartViewSet(viewsets.ModelViewSet):
    def download_shopping_cart(self, request):
        ingredients = (
            IngredientRecipe.objects.filter(
                recipe__recipe_in_cart__user=request.user
            ).values('ingredient__id').
            annotate(quantity=Sum('amount')).
            values_list(
                'ingredient__name', 'ingredient__measurement_unit',
                'quantity'
            )
        )
        shopping_cart = {}
        for item in ingredients:
            name = item[0]
            if name not in shopping_cart:
                shopping_cart[name] = {
                    'measurement_unit': item[1],
                    'quantity': item[2]
                }
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
        for i, (name, data) in enumerate(shopping_cart.items(), start=1):
            if height > 20:
                page.drawString(70, height, (
                    f'{i}. {name} - {data["quantity"]} '
                    f'{data["measurement_unit"]}'
                ))
                height -= 20
        page.drawString(0, height - 10, 200 * '_')
        page.showPage()
        page.save()
        return response
