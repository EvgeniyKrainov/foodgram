from config.constants import DEFAULT_EXTRA_FORMS, MIN_REQUIRED_FORMS
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet

from . import models


class RecipeIngredientInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if not any(form.cleaned_data.get('ingredient')
                   for form in self.forms if not form.cleaned_data.get(
                       'DELETE', False)):
            raise ValidationError('Рецепт должен '
                                  'содержать хотя бы один ингредиент')


class RecipeIngredientInline(admin.TabularInline):
    model = models.RecipeIngredient
    formset = RecipeIngredientInlineFormSet
    extra = DEFAULT_EXTRA_FORMS
    min_num = MIN_REQUIRED_FORMS


class RecipeTagInline(admin.TabularInline):
    model = models.Recipe.tags.through
    extra = DEFAULT_EXTRA_FORMS
    min_num = MIN_REQUIRED_FORMS


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "measurement_unit")
    list_filter = ("name",)
    search_fields = ("name",)


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "slug")
    list_editable = ("name", "slug")
    empty_value_display = "-пусто-"


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "name",
        "author",
        "in_favorites",
        "image",
        "cooking_time",
        "text",
    )
    list_editable = ("name", "cooking_time", "text", "image", "author")
    readonly_fields = ("in_favorites",)
    list_filter = ("name", "author", "tags")
    empty_value_display = "-пусто-"

    inlines = [RecipeIngredientInline, RecipeTagInline]

    exclude = ('tags',)

    @admin.display(description="В избранном")
    def in_favorites(self, obj):
        return obj.favorite_recipe.count()


@admin.register(models.RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("pk", "recipe", "ingredient", "amount")
    list_editable = ("recipe", "ingredient", "amount")


@admin.register(models.Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")
    list_editable = ("user", "recipe")


@admin.register(models.ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")
    list_editable = ("user", "recipe")
