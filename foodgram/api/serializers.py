from django.contrib.auth.hashers import make_password
from django.forms import ValidationError
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.serializers import SerializerMethodField

from recipes.models import (Cart, Favorite, Ingredient, IngredientRecipe,
                            Recipe, Subscribe, Tag, TagRecipe)
from users.models import User

NO_INGREDIENTS = 'Должен быть хотя бы один ингридиент'
REPEAT_TAG = 'Не может быть одинаковых тегов'
REPEAT_INGREDIENTS = 'В одном рецепте не может быть одинаковых ингридиентов'
NO_TAGS = 'Должен быть хотя бы один тег'
CANT_SUBSCRIBE_TO_YOURSELF = 'Вы не можете подписаться на самого себя'
ALREADY_SIGNED = 'Вы уже подписаны на этого автора'
UNACCEPTABLE_COOKING_TIME = 'Время приготовления должно быть больше 0'
UNACCEPTABLE_AMOUNT = 'Колличество ингредиента должно быть больше 0'
ALLREADY_IN_CART = 'Этот тавар уже есть у Вас в корзине'
ALREADY_FAVORITE = 'Этот рецепт уже добавлен в избранное'


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id',
            'username', 'first_name',
            'last_name', 'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Subscribe.objects.filter(
            user=request.user, following=obj.id
        ).exists()


class RegistrationSerializer(UserSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'password', 'is_subscribed',
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
        }

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Subscribe.objects.filter(
            user=request.user, following=obj.id
        ).exists()

    def create(self, validated_data):
        validated_data['password'] = (
            make_password(validated_data.pop('password'))
        )
        return super().create(validated_data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id', 'name',
            'color', 'slug',
        )


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id', 'name',
            'measurement_unit',
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = IngredientRecipe
        fields = (
            'id', 'name',
            'measurement_unit', 'amount',
        )


class IngredientInRecipePostSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = (
            'id', 'amount',
        )


class RecipeGetSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='ingredient'
    )
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author',
            'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name',
            'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return Favorite.objects.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = request.user
        if request is None or request.user.is_anonymous:
            return False
        return Cart.objects.filter(recipe=obj, user=user).exists()


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipePostSerializer(many=True)
    tags = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field='id', queryset=Tag.objects.all()
        )
    )
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def validate(self, attrs):
        if len(attrs['ingredients']) == 0:
            raise ValidationError(NO_INGREDIENTS)
        if len(attrs['tags']) > len(set(attrs['tags'])):
            raise ValidationError(REPEAT_TAG)
        if len(attrs['tags']) == 0:
            raise ValidationError(NO_TAGS)
        if attrs['cooking_time'] < 1:
            raise ValidationError(UNACCEPTABLE_COOKING_TIME)
        id_ingredients = []
        for ingredient in attrs['ingredients']:
            if ingredient['amount'] < 1:
                raise ValidationError(UNACCEPTABLE_AMOUNT)
            id_ingredients.append(ingredient['id'])
        if len(id_ingredients) > len(set(id_ingredients)):
            raise ValidationError(REPEAT_INGREDIENTS)
        return attrs

    def create_tag(self, tags, recipe):
        TagRecipe.objects.bulk_create(
            [
                TagRecipe(
                    tag=get_object_or_404(Tag, id=tag.id),
                    recipe=recipe
                )
                for tag in tags
            ]
        )

    def create_ingredient(self, ingredients, recipe):
        IngredientRecipe.objects.bulk_create(
            [
                IngredientRecipe(
                    ingredient=get_object_or_404(
                        Ingredient, id=ingredient.get('id')
                    ),
                    amount=ingredient.get('amount'),
                    recipe=recipe
                )
                for ingredient in ingredients
            ]
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_tag(tags, recipe)
        self.create_ingredient(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        IngredientRecipe.objects.filter(recipe=instance).delete()
        TagRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredient(validated_data.pop('ingredients'), instance)
        self.create_tag(validated_data.pop('tags'), instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return RecipeGetSerializer(instance, context=context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id', 'name',
            'image', 'cooking_time',
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.CharField(
        source='following.email',
        read_only=True
    )
    id = serializers.IntegerField(
        source='following.id',
        read_only=True
    )
    username = serializers.CharField(
        source='following.username',
        read_only=True
    )
    first_name = serializers.CharField(
        source='following.first_name',
        read_only=True
    )
    last_name = serializers.CharField(
        source='following.last_name',
        read_only=True
    )
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            'email', 'id',
            'username', 'first_name',
            'last_name', 'is_subscribed',
            'recipes', 'recipes_count',
        )

    def validate(self, attrs):
        user = get_object_or_404(User, id=self.context['request'].user.id)
        following = get_object_or_404(User, id=self.context['following_id'])
        if user == following:
            raise ValidationError(CANT_SUBSCRIBE_TO_YOURSELF)
        if Subscribe.objects.filter(user=user, following=following).exists():
            raise ValidationError(ALREADY_SIGNED)
        return attrs

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.following).count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Subscribe.objects.filter(
            user=request.user, following=obj.following
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        queryset = Recipe.objects.filter(author=obj.following)
        recipes_limit = request.query_params.get('recipe_limit')
        if recipes_limit:
            queryset = queryset[:int(recipes_limit)]
        return ShortRecipeSerializer(queryset, many=True).data


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='favorite_recipe.id',
        read_only=True
    )
    name = serializers.CharField(
        source='favorite_recipe.name',
        read_only=True
    )
    cooking_time = serializers.IntegerField(
        source='favorite_recipe.cooking_time',
        read_only=True

    )
    image = serializers.CharField(
        source='favorite_recipe.image',
        read_only=True
    )

    class Meta:
        model = Favorite
        fields = (
            'id', 'name',
            'cooking_time', 'image'
        )

    def validate(self, attrs):
        if Favorite.objects.filter(
            user=get_object_or_404(User, id=self.context['request'].user.id),
            recipe=get_object_or_404(Recipe, id=self.context['recipe_id'])
        ):
            raise ValidationError(ALREADY_FAVORITE)
        return attrs


class CartSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        read_only=True,
        source='recipe.id',
    )
    name = serializers.CharField(
        read_only=True,
        source='recipe.name',
    )
    image = serializers.ImageField(
        read_only=True,
        source='recipe.image',
    )
    cooking_time = serializers.CharField(
        read_only=True,
        source='recipe.cooking_time',
    )

    class Meta:
        model = Cart
        fields = (
            'id', 'name',
            'image', 'cooking_time',
        )

    def validate(self, attrs):
        if Cart.objects.filter(
                user=get_object_or_404(
                    User, id=self.context['request'].user.id
                ),
                recipe=get_object_or_404(Recipe, id=self.context['recipe_id'])
        ).exists():
            raise serializers.ValidationError(ALLREADY_IN_CART)
        return attrs
