from http import HTTPStatus

from django.contrib.auth import authenticate, get_user_model
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import serializers, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from apps.api.filters import IngredientFilter, RecipeFilter
from apps.api.serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                             IngredientSerializer, RecipeCreateSerializer,
                             RecipeSerializer, ShortRecipeSerializer,
                             TagSerializer, AvatarSerializer,
                             PasswordSerializer)
from config.constants import DEFAULT_PAGE_SIZE
from apps.recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            Shopping_cart, Tag)
from apps.users.models import Subscribe
from apps.api.pagination import FoodgramPagination
from apps.api.permissions import IsAuthorOrReadOnly

User = get_user_model()


# Вью для рецептов
class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для работы с тегами."""
    permission_classes = [AllowAny]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для работы с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для работы с рецептами."""
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = FoodgramPagination

    def get_permissions(self):
        """Определяет права доступа для различных действий."""
        if self.action in ['list', 'retrieve']:
            # Разрешить анонимный доступ для просмотра списка и деталей
            return [AllowAny()]
        elif self.action == 'create':
            # Для создания рецепта требуется аутентификация
            return [IsAuthenticated()]
        else:
            # Для обновления/удаления - проверка авторства + аутентификация
            return [IsAuthorOrReadOnly()]

    def get_serializer_class(self):
        """Возвращает соответствующий сериализатор для действия."""
        if self.action in ['create', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        """Сохраняет новый рецепт."""
        serializer.save()

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        link = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return Response({'short-link': link}, status=HTTPStatus.OK)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """Добавляет/удаляет рецепт в избранное."""
        # Проверяем аутентификацию пользователя
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
        except ValueError:
            return Response(
                {'error': 'Некорректный ID рецепта'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.method == 'POST':
            # Проверяем, есть ли уже в избранном
            if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'error': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Создаем запись в избранном
            Favorite.objects.create(user=request.user, recipe=recipe)
            
            # Возвращаем сериализованный рецепт
            serializer = ShortRecipeSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif request.method == 'DELETE':
            # Ищем запись в избранном
            favorite = Favorite.objects.filter(user=request.user, recipe=recipe).first()
            if not favorite:
                return Response(
                    {'error': 'Рецепт не найден в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite_delete(self, request, pk=None):
        """Удаляет рецепт из избранного."""
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = recipe.favorited_by.filter(user=request.user)
        if not favorite.exists():
            return Response(
                {'errors': 'Рецепт не в избранном.'},
                status=HTTPStatus.BAD_REQUEST,
            )
        favorite.delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        """Добавляет/удаляет рецепт в список покупок."""
        # Проверяем аутентификацию пользователя
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
        except ValueError:
            return Response(
                {'error': 'Некорректный ID рецепта'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.method == 'POST':
            # Проверяем, есть ли уже в корзине
            if Shopping_cart.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'error': 'Рецепт уже в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Создаем запись в корзине
            Shopping_cart.objects.create(user=request.user, recipe=recipe)
            
            # Возвращаем сериализованный рецепт
            serializer = ShortRecipeSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif request.method == 'DELETE':
            # Ищем запись в корзине
            cart_item = Shopping_cart.objects.filter(user=request.user, recipe=recipe).first()
            if not cart_item:
                return Response(
                    {'error': 'Рецепт не найден в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        """Скачивает список покупок."""
        user = request.user
        if not user.is_authenticated:
            return Response(
                {'error': 'Необходима авторизация'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Получаем рецепты из корзины пользователя
        shopping_cart_items = Shopping_cart.objects.filter(user=user)
        
        # Собираем ингредиенты
        ingredients = {}
        for cart_item in shopping_cart_items:
            recipe = cart_item.recipe
            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient = recipe_ingredient.ingredient
                key = (ingredient.name, ingredient.measurement_unit)
                if key in ingredients:
                    ingredients[key] += recipe_ingredient.amount
                else:
                    ingredients[key] = recipe_ingredient.amount
        
        # Формируем текстовый файл
        shopping_list = "Список покупок:\n\n"
        for (name, unit), amount in ingredients.items():
            shopping_list += f"- {name}: {amount} {unit}\n"
        
        response = Response(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response


# Вью для пользователей
class UsersViewSet(viewsets.ModelViewSet):
    """Представление для работы с пользователями."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = FoodgramPagination


    def get_permissions(self):
        """Определяет права доступа для различных действий."""
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @csrf_exempt
    def create(self, request, *args, **kwargs):
        """Создает нового пользователя."""
        serializer = CustomUserCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=HTTPStatus.CREATED, headers=headers)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Возвращает информацию о текущем пользователе."""
        serializer = CustomUserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data, status=HTTPStatus.OK)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def me_avatar(self, request):
        """Обновляет или удаляет аватар текущего пользователя."""
        if request.method == 'DELETE':
            # Удаляем аватар
            if request.user.avatar:
                request.user.avatar.delete()
                request.user.avatar = None
                request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        elif request.method == 'PUT':
            # Обновляем аватар (существующий код)
            if 'avatar' not in request.data:
                return Response(
                    {'avatar': ['Это поле обязательно.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = AvatarSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=HTTPStatus.OK)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        """Подписаться/отписаться на автора."""
        # Проверяем аутентификацию пользователя
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        author = get_object_or_404(User, id=pk)
        
        if request.method == 'POST':
            # Проверка на подписку на самого себя
            if request.user == author:
                return Response(
                    {'error': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Проверка существующей подписки
            if Subscribe.objects.filter(user=request.user, author=author).exists():
                return Response(
                    {'error': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Создание подписки
            subscription = Subscribe.objects.create(user=request.user, author=author)
            
            # Возвращаем данные автора
            serializer = CustomUserSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif request.method == 'DELETE':
            subscription = Subscribe.objects.filter(user=request.user, author=author).first()
            if not subscription:
                return Response(
                    {'error': 'Вы не подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
    @action(
        detail=True,
        methods=['delete'],
        permission_classes=[IsAuthenticated]
    )
    def unsubscribe(self, request, pk=None):
        """Отписывает пользователя от другого пользователя."""
        user = request.user
        following = self.get_object()
        follow = user.following.filter(following=following)
        if not follow.exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=HTTPStatus.BAD_REQUEST
            )
        follow.delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Возвращает список авторов, на которых подписан пользователь."""
        try:
            user = request.user
            
            # Получаем подписки пользователя
            subscriptions = user.subscriber.all()
            
            # Извлекаем авторов из подписок
            authors = [subscription.author for subscription in subscriptions]
            
            # Применяем пагинацию
            page = self.paginate_queryset(authors)
            if page is not None:
                serializer = CustomUserSerializer(
                    page, many=True, context={'request': request}
                )
                return self.get_paginated_response(serializer.data)
            
            serializer = CustomUserSerializer(
                authors, many=True, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        """Смена пароля текущего пользователя."""
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Проверяем текущий пароль
        if not request.user.check_password(serializer.validated_data['current_password']):
            return Response(
                {'current_password': 'Неверный текущий пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Устанавливаем новый пароль
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(csrf_exempt, name='dispatch')
class CustomAuthToken(APIView):
    """Представление для получения токена аутентификации."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Обрабатывает запрос на получение токена."""
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {
                'auth_token': token.key,
                'user_id': user.pk,
                'email': user.email
            },
            status=HTTPStatus.OK
        )


class LoginSerializer(serializers.Serializer):
    """Сериализатор для аутентификации пользователей."""
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        """Проверяет корректность введенных данных для входа."""
        email = data.get('email')
        password = data.get('password')
        
        # Находим пользователя по email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'non_field_errors': ['Неверный email или пароль.']}
            )
        
        # Аутентифицируем по username (стандартный способ Django)
        user = authenticate(
            request=self.context['request'],
            username=user.username,  # Используем username для аутентификации
            password=password
        )
        
        if user is None:
            raise serializers.ValidationError(
                {'non_field_errors': ['Неверный email или пароль.']}
            )
        
        data['user'] = user
        return data