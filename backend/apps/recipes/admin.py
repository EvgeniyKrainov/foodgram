from django.contrib import admin
from .models import (
    Tag, Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart, Subscription
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    list_editable = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_editable = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'author', 'cooking_time', 
        'pub_date', 'favorites_count'
    )
    list_filter = ('author', 'name', 'tags')
    search_fields = ('name', 'author__username')
    inlines = [RecipeIngredientInline]
    
    def favorites_count(self, obj):
        return obj.favorites.count()
    favorites_count.short_description = 'В избранном'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user__username', 'author__username')
