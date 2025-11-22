from http import HTTPStatus

from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.filters import IngredientFilter, RecipeFilter
from apps.api.pagination import FoodgramPagination
from apps.api.permissions import IsAuthorOrReadOnly
from apps.api.serializers import (AvatarSerializer, CustomUserCreateSerializer,
                                  CustomUserSerializer, IngredientSerializer,
                                  PasswordSerializer, RecipeCreateSerializer,
                                  RecipeSerializer, ShortRecipeSerializer,
                                  TagSerializer)
from apps.recipes.models import (Favorite, Ingredient, Recipe, ShoppingCart,
                                 Tag)
from apps.users.models import Subscribe

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
            return [AllowAny()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        else:
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
            if Favorite.objects.filter(user=request.user,
                                       recipe=recipe).exists():
                return Response(
                    {'error': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=request.user,
                                               recipe=recipe).first()
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
        favorite = recipe.favorites.filter(user=request.user)
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
            if ShoppingCart.objects.filter(user=request.user,
                                            recipe=recipe).exists():
                return Response(
                    {'error': 'Рецепт уже в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            cart_item = ShoppingCart.objects.filter(user=request.user,
                                                     recipe=recipe).first()
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
        shopping_cart_items = user.shopping_carts.all()
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
        shopping_list = "Список покупок:\n\n"
        for (name, unit), amount in ingredients.items():
            shopping_list += f"- {name}: {amount} {unit}\n"
        response = Response(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"')
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
            if request.user.avatar:
                request.user.avatar.delete()
                request.user.avatar = None
                request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif request.method == 'PUT':
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
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        author = get_object_or_404(User, id=pk)
        if request.method == 'POST':
            if request.user == author:
                return Response(
                    {'error': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Subscribe.objects.filter(user=request.user,
                                        author=author).exists():
                return Response(
                    {'error': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription = Subscribe.objects.create(user=request.user,
                                                    author=author)
            serializer = CustomUserSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            subscription = Subscribe.objects.filter(user=request.user,
                                                    author=author).first()
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
        follow = user.subscribing.filter(author=following)
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
            subscriptions = user.subscribing.all()
            authors = [subscription.author for subscription in subscriptions]
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
        except Exception:
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
        if not request.user.check_password(
            serializer.validated_data['current_password']
        ):
            return Response(
                {'current_password': 'Неверный текущий пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )
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
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'non_field_errors': ['Неверный email или пароль.']}
            )
        user = authenticate(
            request=self.context['request'],
            username=user.username,
            password=password
        )
        if user is None:
            raise serializers.ValidationError(
                {'non_field_errors': ['Неверный email или пароль.']}
            )
        data['user'] = user
        return data
