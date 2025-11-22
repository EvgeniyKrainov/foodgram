from apps.recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from config.constants import (MAX_AMOUNT, MAX_COOKING_TIME, MIN_AMOUNT,
                              MIN_COOKING_TIME)
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

User = get_user_model()


# Сериализаторы пользователей
class UserListSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + (
            'is_subscribed',
            'avatar'
        )

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and request.
                user.is_authenticated and request.
                user.subscribing.filter(author=obj).exists())


class UserSerializer(UserListSerializer):
    """Сериализатор для работы с данными пользователя."""

    recipes_count = serializers.ReadOnlyField(source='recipes.count')
    recipes = serializers.SerializerMethodField()

    class Meta(UserListSerializer.Meta):
        fields = UserListSerializer.Meta.fields + (
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        """Возвращает список рецептов пользователя."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        queryset = obj.recipes.all().order_by('-id')

        if recipes_limit:
            try:
                limit = int(recipes_limit)
                queryset = queryset[:limit]
            except (ValueError, TypeError):
                pass

        return ShortRecipeSerializer(
            queryset, many=True, context=self.context
        ).data


class AvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def to_representation(self, instance):
        """Возвращает полный URL аватара."""
        request = self.context.get('request')
        if instance.avatar:
            avatar_url = instance.avatar.url
            if request:
                return {
                    'avatar': request.build_absolute_uri(avatar_url)
                }
            return {
                'avatar': avatar_url
            }
        return {
            'avatar': None
        }


# Сериализаторы рецептов
class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.Serializer):
    """Сериализатор для ингредиентов в рецепте."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT, max_value=MAX_AMOUNT
    )

    def validate_id(self, value):
        """Проверяет существование ингредиента по id."""
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f'Ингредиент с id={value} не существует.'
            )
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME, max_value=MAX_COOKING_TIME
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'author'
        )

    def validate_image(self, value):
        """Проверяет, что изображение не пустое при создании."""
        if not value and self.context['request'].method == 'POST':
            raise serializers.ValidationError(
                'Изображение обязательно для создания рецепта.'
            )
        return value

    def validate(self, data):
        """Проверяет корректность данных рецепта."""
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Необходимо указать хотя бы один ингредиент.'}
            )

        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Необходимо указать хотя бы один тег.'}
            )

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )
        return data

    def _create_ingredients(self, recipe, ingredients_data):
        """Создаёт объекты RecipeIngredient с использованием bulk_create."""
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        )

    def create(self, validated_data):
        """Создает новый рецепт."""
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags)
        self._create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет существующий рецепт."""
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        self._create_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Преобразует рецепт в JSON-представление."""
        return RecipeSerializer(instance, context=self.context).data


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserListSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_ingredients(self, obj):
        """Возвращает список ингредиентов рецепта."""
        recipe_ingredients = obj.recipe_ingredients.all()
        return [
            {
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                'measurement_unit': ri.ingredient.measurement_unit,
                'amount': ri.amount
            }
            for ri in recipe_ingredients
        ]

    def _check_user_relation(self, obj, related_manager_name):
        """Общий метод для проверки отношений пользователя с рецептом."""
        request = self.context.get('request')
        return (request and request.
                user.is_authenticated and getattr(obj,
                                                  related_manager_name
                                                  ).filter(
                                                      user=request.user
                                                      ).exists())

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        return self._check_user_relation(obj, 'favorites')

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в список покупок."""
        return self._check_user_relation(obj, 'shopping_carts')


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
