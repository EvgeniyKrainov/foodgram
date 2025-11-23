from django_filters.rest_framework import (AllValuesMultipleFilter, CharFilter,
                                           FilterSet, filters)

from apps.recipes.models import Ingredient, Recipe


class RecipeFilter(FilterSet):

    tags = AllValuesMultipleFilter(
        field_name='tags__slug',
        label='Tags'
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_carts__user=user)
        return queryset


class IngredientFilter(FilterSet):

    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
