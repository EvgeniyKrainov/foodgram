from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from .models import (
    Tag, Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart, Subscription)
from .serializers import (
    TagSerializer, IngredientSerializer,
    RecipeReadSerializer, RecipeWriteSerializer)
from apps.users.serializers import CustomUserSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для тегов"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингредиентов"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов"""
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return []
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное"""
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=request.user, recipe=recipe)
            return Response(
                {'message': 'Рецепт добавлен в избранное'},
                status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            favorite = get_object_or_404(
                Favorite,
                user=request.user,
                recipe=recipe)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в список покупок"""
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            return Response(
                {'message': 'Рецепт добавлен в список покупок'},
                status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            cart_item = get_object_or_404(
                ShoppingCart,
                user=request.user,
                recipe=recipe)
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачать список покупок"""
        try:
            shopping_cart = ShoppingCart.objects.filter(user=request.user)

            if not shopping_cart.exists():
                return Response(
                    {'error': 'Список покупок пуст'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            recipes = [item.recipe for item in shopping_cart]

            # Суммируем ингредиенты
            ingredients = RecipeIngredient.objects.filter(
                recipe__in=recipes
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit'
            ).annotate(total_amount=Sum('amount'))

            # Формируем текстовый файл
            shopping_list = "🍽️ Foodgram - Список покупок\n\n"
            shopping_list += "=" * 40 + "\n"

            for i, ingredient in enumerate(ingredients, 1):
                shopping_list += (
                    f"{i}. {ingredient['ingredient__name']} "
                    f"({ingredient['ingredient__measurement_unit']}) - "
                    f"{ingredient['total_amount']}\n"
                )

            shopping_list += "\n" + "=" * 40 + "\n"
            shopping_list += f"Всего позиций: {len(ingredients)}\n"
            shopping_list += "Приятных покупок! 🛒"

            response = HttpResponse(shopping_list, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
            return response

        except Exception as e:
            return Response(
                {'error': f'Ошибка при формировании списка: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
