from colorfield.fields import ColorField
from django.db import models
from django.core.validators import MinValueValidator

from users.models import User

class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
    )
    measurement_unit = models.CharField(
        max_length=200,
    )

    def __str__(self):
        return(
            f'name: {self.name}, '
            f'measurement unit: {self.measurement_unit}'
        )

class Tag(models.Model):
    name = models.CharField(
        max_length=200,
    )
    color = ColorField(
        format='hex',
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
    )

class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
    )
    image = models.ImageField()
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipes',
    )
    name = models.CharField(
        max_length=200,
    )
    text = models.TextField()
    pub_date = models.DateTimeField(
        auto_now_add=True,
    )
    cooking_time = models.IntegerField(
        validators=[MinValueValidator(1)]
    )

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_in_cart',
    )

class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='amount'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient'
    )
    amount = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    def __str__(self):
        return f'{self.ingredient} in {self.recipe}, {self.amount}'


class TagRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.recipe.name

class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )