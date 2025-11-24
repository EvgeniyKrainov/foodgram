from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.users.models import User
from config.constants import (
    MAX_AMOUNT,
    MAX_COOKING_TIME,
    MAX_LENGHT_NAME_INGR,
    MAX_LENGHT_NAME_REC,
    MAX_LENGHT_NAME_TAG,
    MAX_LENGHT_SLUG,
    MIN_AMOUNT,
    MIN_COOKING_TIME,

)


class Ingredient(models.Model):
    name = models.CharField("Название", max_length=MAX_LENGHT_NAME_INGR)
    measurement_unit = models.CharField("Единица измерения",
                                        max_length=MAX_LENGHT_NAME_INGR)

    class Meta:
        ordering = ["name"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Tag(models.Model):
    name = models.CharField("Название", max_length=MAX_LENGHT_NAME_TAG)
    slug = models.SlugField(
        "Уникальный слаг", max_length=MAX_LENGHT_SLUG, unique=True, null=True
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField("Название", max_length=MAX_LENGHT_NAME_REC)
    text = models.TextField("Описание")
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления, мин",
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME)
        ]
    )
    image = models.ImageField("Изображение", upload_to="recipes/", blank=True)
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор"
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        through_fields=("recipe", "ingredient"),
        verbose_name="Ингредиенты",
    )
    tags = models.ManyToManyField(Tag, verbose_name="Теги")

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        "Количество",
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        ]
    )

    class Meta:
        ordering = ["recipe", "ingredient"]
        verbose_name = "Ингредиенты в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], name="unique_combination"
            )
        ]

    def __str__(self):
        return (
            f"{self.recipe.name}: "
            f"{self.ingredient.name} - "
            f"{self.amount} "
            f"{self.ingredient.measurement_unit}"
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Добавил в избранное",
        related_name="favorites",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Избранный рецепт",
        related_name="favorites",
    )

    class Meta:
        ordering = ["user", "recipe"]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        default_related_name = "favorites"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Добавил в корзину",
        related_name="shopping_carts",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт в корзине",
        related_name="shopping_carts",
    )

    class Meta:
        ordering = ["user", "recipe"]
        verbose_name = "Корзина"
        verbose_name_plural = "Корзина"
        default_related_name = "shopping_carts"
        db_table = "recipes_shoppingcart"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shopping_cart"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"
