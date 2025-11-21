from django.contrib.auth import get_user_model
from django.templatetags.static import static
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from config.constants import (MAX_AMOUNT, MAX_COOKING_TIME, MIN_AMOUNT,
                              MIN_COOKING_TIME)
from apps.recipes.models import (Ingredient, Recipe, RecipeIngredient,
                                 Tag, Shopping_cart, Favorite)
from apps.users.models import User, Subscribe

User = get_user_model()


# Сериализаторы пользователей
class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового пользователя."""
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'password')
        read_only_fields = ('id',)
        extra_kwargs = {
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'password': {'required': True},
        }

    def create(self, validated_data):
        """Создает нового пользователя с переданными данными."""
        return User.objects.create_user(**validated_data)
    
    def validate(self, data):
        """Проверяет уникальность email и username."""
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError(
                {'email': 'Пользователь с таким email уже существует.'}
            )
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError(
                {'username': 'Пользователь с таким username уже существует.'}
            )
        return data

class UserListSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username', 
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
            # Без recipes и recipes_count
        )

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=request.user, author=obj).exists()


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с данными пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()  # Добавьте это!

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
            'recipes',
            'recipes_count'
        )

    def to_representation(self, instance):
        """Переопределяем представление для разных случаев."""
        request = self.context.get('request')
        
        # Если это запрос на обновление аватара
        if request and request.path.endswith('/me/avatar/'):
            return {
                'avatar': self.get_avatar(instance)
            }
        
        # Получаем стандартное представление
        representation = super().to_representation(instance)
        
        # Оставляем recipes и recipes_count ТОЛЬКО для подписок
        if request and not any([
            '/subscriptions/' in request.path,
            request.path.endswith('/subscribe/')
        ]):
            representation.pop('recipes', None)
            representation.pop('recipes_count', None)
        
        return representation
    
    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        # Проверяем: подписан ли текущий пользователь (request.user) на автора (obj)
        return request.user.subscriber.filter(author=obj).exists()

    def get_recipes(self, obj):
        """Возвращает список рецептов пользователя."""
        try:
            request = self.context.get('request')
            recipes_limit = request.query_params.get('recipes_limit')
            
            queryset = obj.recipes.all().order_by('-id')
            if recipes_limit:
                queryset = queryset[:int(recipes_limit)]
            
            return ShortRecipeSerializer(
                queryset, many=True, context=self.context
            ).data
        except Exception as e:
            return []

    def get_recipes_count(self, obj):
        """Возвращает общее количество рецептов пользователя."""
        return obj.recipes.count()


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

class PasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_new_password(self, value):
        # Дополнительная валидация пароля если нужно
        if len(value) < 8:
            raise serializers.ValidationError("Пароль должен содержать минимум 8 символов")
        return value


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
        read_only_fields = ('author',)

    def validate(self, data):
        """Проверяет корректность данных рецепта."""
        ingredients = self.initial_data.get('ingredients')
        if not ingredients or len(ingredients) == 0:
            raise serializers.ValidationError(
                {'ingredients': 'Необходимо указать хотя бы один ингредиент.'}
            )
        
        # Проверка уникальности ингредиентов
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )
        
        tags = self.initial_data.get('tags')
        if not tags or len(tags) == 0:
            raise serializers.ValidationError(
                {'tags': 'Необходимо указать хотя бы один тег.'}
            )
        
        # Проверка уникальности тегов
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )
        
        return data

    def _create_ingredients(self, recipe, ingredients_data):
        """Создаёт объекты RecipeIngredient с использованием bulk_create."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ])

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
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        self._create_ingredients(instance, ingredients_data)
        return instance

    def to_representation(self, instance):
        """Преобразует рецепт в JSON-представление."""
        return RecipeSerializer(instance, context=self.context).data


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

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

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в список покупок."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Shopping_cart.objects.filter(user=request.user, recipe=obj).exists()
    
    def get_image(self, obj):
        """Возвращает URL изображения или пустую строку если изображения нет."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ""


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ""
