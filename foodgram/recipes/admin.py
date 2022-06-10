from django.contrib import admin

from users.models import User
from .models import *


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    extra = 0


class TagRecipeInline(admin.TabularInline):
    model = TagRecipe
    extra = 0


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'id')
    search_fields = ('username', 'email',)
    empty_value_display = 'пусто'
    list_filter = ('username', 'email',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    empty_value_display = 'пусто'
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', )
    empty_value_display = 'пусто'
    list_filter = ('name',)


class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'id')
    search_fields = ('user',)
    empty_value_display = 'пусто'
    list_filter = ('user',)


class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    search_fields = ('user',)
    empty_value_display = 'пусто'
    list_filter = ('user',)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    empty_value_display = 'пусто'
    list_filter = ('user',)


class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientRecipeInline, TagRecipeInline)
    list_display = ('name', 'author', 'cooking_time',
                    'id', 'count_favorite', 'pub_date')
    search_fields = ('name', 'author', 'tags')
    empty_value_display = 'пусто'
    list_filter = ('name', 'author', 'tags')

    def count_favorite(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


admin.site.register(Cart, CartAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Subscribe, SubscribeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)