import django_filters
from django_filters import FilterSet
from recipes.models import Recipe


class RecipeFilter(FilterSet):
    is_favorited = django_filters.BooleanFilter(method='get_is_favorited')
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author',)

    def get_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorite_recipe__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(recipe_in_cart__user=self.request.user)
        return queryset
