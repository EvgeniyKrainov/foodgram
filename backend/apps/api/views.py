from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from apps.api.filters import IngredientFilter, RecipeFilter
from apps.api.pagination import FoodgramPagination
from apps.api.permissions import IsAuthorOrReadOnly
from apps.api.serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    TagSerializer,
    UserListSerializer,
    UserSerializer,
)
from apps.recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from apps.users.models import Subscribe
from config.constants import SAFE_METHODS

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
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_serializer_class(self):
        """Возвращает соответствующий сериализатор для действия."""
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    @action(detail=True,
            methods=['get'],
            permission_classes=[AllowAny],
            url_path='get-link')
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        link = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return Response({'short-link': link}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавляет/удаляет рецепт в избранное."""
        recipe = self.get_object()
        model = Favorite
        error_messages = {
            'exists': 'Рецепт уже в избранном',
            'not_found': 'Рецепт не найден в избранном'
        }

        if request.method == 'POST':
            return self._add_to_collection(request.user,
                                           recipe,
                                           model,
                                           error_messages)
        return self._remove_from_collection(request.user,
                                            recipe,
                                            model,
                                            error_messages)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавляет/удаляет рецепт в список покупок."""
        recipe = self.get_object()
        model = ShoppingCart
        error_messages = {
            'exists': 'Рецепт уже в корзине',
            'not_found': 'Рецепт не найден в корзине'
        }

        if request.method == 'POST':
            return self._add_to_collection(request.user,
                                           recipe,
                                           model,
                                           error_messages)
        return self._remove_from_collection(request.user,
                                            recipe,
                                            model,
                                            error_messages)

    def _add_to_collection(self, user, recipe, model, error_messages):
        """Добавляет рецепт в указанную коллекцию."""
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'error': error_messages['exists']},
                status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_collection(self, user, recipe, model, error_messages):
        """Удаляет рецепт из указанной коллекции."""
        deleted_count, _ = model.objects.filter(
            user=user, recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response(
                {'error': error_messages['not_found']},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

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
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        serializer = UserListSerializer(request.user,
                                        context={'request': request})
        return Response(serializer.data)

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
