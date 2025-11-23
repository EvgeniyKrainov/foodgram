from apps.api.views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                            UserViewSet)
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

schema_view = get_schema_view(
    openapi.Info(
        title="Foodgram API",
        default_version='v1',
        description=(
            "Документация для API проекта Foodgram -"
            "«Продуктовый помощник»\n\n"
            "## Основные возможности:\n"
            "- 📝 Управление рецептами (создание, редактирование, удаление)\n"
            "- 👥 Подписки на авторов\n"
            "- ⭐ Добавление рецептов в избранное\n"
            "- 🛒 Формирование списка покупок\n"
            "- 🔍 Фильтрация рецептов по тегам и ингредиентам\n\n"
            "## 🔐 Аутентификация\n"
            "## Аутентификация\n"
            "Для доступа к защищенным эндпоинтам"
            "используйте Token authentication.\n"
            "Получите токен через `/api/auth/token/login/`"
            "и добавьте в заголовки:\n"
            "`Authorization: Token ваш_токен`"
        ),
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="admin@foodgram.ru"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

    path(
        'docs/',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'
    ),
    path(
        'redoc/',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc'
    ),
    path(
        'swagger<format>/',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json'
    ),
]
