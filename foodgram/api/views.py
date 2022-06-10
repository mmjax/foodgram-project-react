from djoser.views import UserViewSet
from rest_framework import viewsets

from .mixins import ListRetriveViewSet
from recipes.models import *
from users.models import User
from .serializers import *


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
