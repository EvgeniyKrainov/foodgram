from http import HTTPStatus

from apps.api.filters import IngredientFilter, RecipeFilter
from apps.api.pagination import FoodgramPagination
from apps.api.permissions import IsAuthorOrReadOnly
from apps.api.serializers import (AvatarSerializer, IngredientSerializer,
                                  RecipeCreateSerializer, RecipeSerializer,
                                  ShortRecipeSerializer, TagSerializer,
                                  UserListSerializer, UserSerializer)
from apps.recipes.models import (Favorite, Ingredient, Recipe,
                                 RecipeIngredient, ShoppingCart, Tag)
from apps.users.models import Subscribe
from config.constants import SAFE_METHODS
from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

User = get_user_model()


# Вью для рецептов
class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для работы с тегами."""

    permission_classes = [AllowAny]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None

    @swagger_auto_schema(
        operation_description="Получить список всех тегов",
        responses={200: TagSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получить детальную информацию о теге",
        responses={200: TagSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None

    @swagger_auto_schema(
        operation_description="Получить список ингредиентов",
        responses={200: IngredientSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получить детальную информацию об ингредиенте",
        responses={200: IngredientSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для работы с рецептами."""

    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = FoodgramPagination
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    @swagger_auto_schema(
        operation_description="Получить список всех рецептов",
        responses={200: RecipeSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получить детальную информацию о рецепте",
        responses={200: RecipeSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создать новый рецепт",
        request_body=RecipeCreateSerializer,
        responses={201: RecipeSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Обновить рецепт",
        request_body=RecipeCreateSerializer,
        responses={200: RecipeSerializer}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частично обновить рецепт",
        request_body=RecipeCreateSerializer,
        responses={200: RecipeSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удалить рецепт",
        responses={204: 'Рецепт успешно удален'}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        """Возвращает соответствующий сериализатор для действия."""
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        """Сохраняет новый рецепт."""
        serializer.save()

    @swagger_auto_schema(
        method='get',
        operation_description="Получить короткую ссылку на рецепт",
        responses={200: openapi.Response(
            description="Ссылка на рецепт",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'short-link': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        )}
    )
    @action(detail=True,
            methods=['get'],
            permission_classes=[AllowAny],
            url_path='get-link')
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        link = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return Response({'short-link': link}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='post',
        operation_description="Добавить рецепт в избранное",
        responses={
            201: ShortRecipeSerializer,
            400: openapi.Response(description="Рецепт уже в избранном")
        }
    )
    @swagger_auto_schema(
        method='delete',
        operation_description="Удалить рецепт из избранного",
        responses={
            204: 'Рецепт удален из избранного',
            400: openapi.Response(description="Рецепт не найден в избранном")
        }
    )
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавляет/удаляет рецепт в избранное."""
        recipe = self.get_object()

        if request.method == 'POST':
            return self._add_to_favorites(request.user, recipe)
        return self._remove_from_favorites(request.user, recipe)

    def _add_to_favorites(self, user, recipe):
        """Добавляет рецепт в избранное."""
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'error': 'Рецепт уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_favorites(self, user, recipe):
        """Удаляет рецепт из избранного."""
        deleted_count, _ = Favorite.objects.filter(
            user=user, recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response(
                {'error': 'Рецепт не найден в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        method='post',
        operation_description="Добавить рецепт в список покупок",
        responses={
            201: ShortRecipeSerializer,
            400: openapi.Response(description="Рецепт уже в корзине")
        }
    )
    @swagger_auto_schema(
        method='delete',
        operation_description="Удалить рецепт из списка покупок",
        responses={
            204: 'Рецепт удален из корзины',
            400: openapi.Response(description="Рецепт не найден в корзине")
        }
    )
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавляет/удаляет рецепт в список покупок."""
        recipe = self.get_object()

        if request.method == 'POST':
            return self._add_to_shopping_cart(request.user, recipe)
        return self._remove_from_shopping_cart(request.user, recipe)

    def _add_to_shopping_cart(self, user, recipe):
        """Добавляет рецепт в корзину."""
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'error': 'Рецепт уже в корзине'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_shopping_cart(self, user, recipe):
        """Удаляет рецепт из корзины."""
        deleted_count, _ = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response(
                {'error': 'Рецепт не найден в корзине'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        method='get',
        operation_description="Скачать список покупок в виде текстового файла",
        responses={200: openapi.Response(
            description="Текстовый файл со списком покупок",
            schema=openapi.Schema(type=openapi.TYPE_STRING)
        )}
    )
    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачивает список покупок."""
        shopping_data = self._get_shopping_cart_data(request.user)
        shopping_list = self._format_shopping_list(shopping_data)
        return self._create_file_response(shopping_list)

    def _get_shopping_cart_data(self, user):
        """Получает данные списка покупок одним запросом."""
        return RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=user
        ).values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit')
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

    def _format_shopping_list(self, shopping_data):
        """Форматирует данные в текстовый список."""
        shopping_list = "Список покупок:\n\n"
        for item in shopping_data:
            shopping_list += (f"- {item['name']}: "
                              f"{item['total_amount']} {item['unit']}\n")
        return shopping_list

    def _create_file_response(self, shopping_list):
        """Создает файловый ответ для скачивания."""
        response = Response(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"')
        return response


# Вью для пользователей
class UserViewSet(DjoserUserViewSet):
    """Наследуем всю базовую функциональность от Djoser."""

    pagination_class = FoodgramPagination

    @swagger_auto_schema(
        operation_description="Получить информацию о текущем пользователе",
        responses={200: UserListSerializer, 401: 'Не авторизован'}
    )
    @action(detail=False, methods=['get'])
    def me(self, request, *args, **kwargs):
        """
        Переопределяем метод me для корректной
        обработки анонимных пользователей.
        """

        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные credentials не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = UserListSerializer(request.user,
                                        context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        method='put',
        operation_description="Обновить аватар текущего пользователя",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['avatar'],
            properties={
                'avatar': openapi.Schema(type=openapi.TYPE_FILE)
            }
        ),
        responses={200: AvatarSerializer, 400: 'Ошибка валидации'}
    )
    @swagger_auto_schema(
        method='delete',
        operation_description="Удалить аватар текущего пользователя",
        responses={204: 'Аватар удален'}
    )
    @action(detail=False, methods=['put', 'delete'],
            permission_classes=[IsAuthenticated],
            url_path='me/avatar')
    def me_avatar(self, request):
        """Обновляет или удаляет аватар текущего пользователя."""
        if request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete()
                request.user.avatar = None
                request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

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

    @swagger_auto_schema(
        method='post',
        operation_description="Подписаться на автора",
        responses={
            201: UserSerializer,
            400: openapi.Response(description="Ошибка подписки")
        }
    )
    @swagger_auto_schema(
        method='delete',
        operation_description="Отписаться от автора",
        responses={
            204: 'Подписка удалена',
            400: openapi.Response(description="Подписка не найдена")
        }
    )
    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        """Подписаться/отписаться на автора."""
        author = self.get_object()

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
            Subscribe.objects.create(user=request.user, author=author)
            serializer = UserSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted_count, _ = Subscribe.objects.filter(
            user=request.user, author=author
        ).delete()

        if deleted_count == 0:
            return Response(
                {'error': 'Подписка не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        method='get',
        operation_description="Получить список подписок текущего пользователя",
        responses={200: UserSerializer(many=True)}
    )
    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Возвращает список авторов, на которых подписан пользователь."""
        try:
            user = request.user
            authors = User.objects.filter(subscribing__user=user)
            page = self.paginate_queryset(authors)
            if page is not None:
                serializer = UserSerializer(
                    page, many=True, context={'request': request}
                )
                return self.get_paginated_response(serializer.data)
            serializer = UserSerializer(
                authors, many=True, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
