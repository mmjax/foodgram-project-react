import django_filters
from django_filters import FilterSet
from rest_framework import filters
from recipes.models import Recipe


class RecipeFilter(FilterSet):
    is_favorited = django_filters.NumberFilter(method='get_is_favorited')
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            if value == 1:
                return queryset.filter(favorite_recipe__user=user)
            return queryset.exclude(favorite_recipe__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            if value == 1:
                return queryset.filter(recipe_in_cart__user=user)
            return queryset.exclude(recipe_in_cart__user=user)
        return queryset


class IngredientSearchFilter(filters.SearchFilter):
    search_param = 'name'
