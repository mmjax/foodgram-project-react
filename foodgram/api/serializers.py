from django.contrib.auth.hashers import make_password
from django.forms import ValidationError
from djoser.serializers import UserSerializer
from rest_framework.serializers import SerializerMethodField
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from rest_framework.generics import get_object_or_404

from recipes.models import (Cart, Favorite, Ingredient, IngredientRecipe,
                            Recipe, Subscribe, Tag, TagRecipe)

from users.models import User


NO_INGREDIENTS = 'Должен быть хотя бы один ингридиент'
REPEAT_TAG = 'Не может быть одинаковых тегов'
REPEAT_INGREDIENTS = 'В одном рецепте не может быть одинаковых ингридиентов'
NO_TAGS = 'Должен быть хотя бы один тег'
UNACCEPTABLE_COOKING_TIME = 'Время приготовления должно быть больше 0'
UNACCEPTABLE_AMOUNT = 'Колличество ингредиента должно быть больше 0'


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
        return(Subscribe.objects.filter(
                user=request.user, following__id=obj.id).exists())


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

    def is_subscribed(self, obj):
        return (
            self.context['request'].user.is_authenticated and obj.is_subscribed
        )

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
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return Cart.objects.filter(recipe=obj, user=user).exists()


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipePostSerializer(many=True)
    tags = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())
    )
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'
        required_fields = (
            'ingredients', 'tags',
            'image', 'name',
            'text', 'cooking_time',
        )

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

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        for ingredient in ingredients:
            IngredientRecipe.objects.create(
                ingredient=get_object_or_404(Ingredient, id=ingredient.get('id')),
                amount = ingredient.get('amount'),
                recipe = recipe
            )

        for tag in tags:
            TagRecipe.objects.create(
                tag=get_object_or_404(Tag, id=tag.id),
                recipe=recipe
            )

        return recipe
    
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)

        IngredientRecipe.objects.filter(recipe=instance).delete()
        for ingredient in ingredients:
            IngredientRecipe.objects.create(
                ingredient=get_object_or_404(Ingredient, id=ingredient.get('id')),
                amount = ingredient.get('amount'),
                recipe = instance
            )

        TagRecipe.objects.filter(recipe=instance).delete()
        for tag in tags:
            TagRecipe.objects.create(
                tag=get_object_or_404(Tag, id=tag.id),
                recipe=instance
            )
        return instance


class RecipeMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id', 'name',
            'image', 'cooking_time',
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 
            'username', 'first_name',
            'last_name', 'is_subscribed', 
            'recipes', 'recipes_count',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        if Subscribe.objects.filter(
                user=request.user, following__id=obj.id).exists():
            return True
        else:
            return False
    
    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author__id=obj.id).count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request.GET.get('recipes_limit'):
            recipes_limit = int(request.GET.get('recipes_limit'))
            queryset = Recipe.objects.filter(author__id=obj.id).order_by('id')[
                :recipes_limit]
        else:
            queryset = Recipe.objects.filter(author__id=obj.id).order_by('id')
        return RecipeMiniSerializer(queryset, many=True).data

class FavoriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField(max_length=None, use_url=False,)


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = (
            'id', 'name',
            'image', 'cooking_time',
        )