from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.api.views import (CustomAuthToken, IngredientViewSet, RecipeViewSet,
                       TagViewSet, UsersViewSet)

router = DefaultRouter()
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('users', UsersViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

    path('recipes/<int:pk>/get-link/',
         RecipeViewSet.as_view({'get': 'get_link'}),
         name='recipe-get-link'),
    path('recipes/<int:pk>/favorite/',
         RecipeViewSet.as_view({'post': 'favorite', 'delete': 'favorite'}),
         name='recipe-favorite'),
    path('recipes/<int:pk>/shopping_cart/',
         RecipeViewSet.as_view({'post': 'shopping_cart', 'delete': 'shopping_cart'}),
         name='recipe-shopping-cart'),
    path('recipes/download_shopping_cart/',
         RecipeViewSet.as_view({'get': 'download_shopping_cart'}),
         name='download-shopping-cart'),
    path('users/me/', UsersViewSet.as_view({'get': 'me'}),
         name='user-me'),
    path('users/me/avatar/', UsersViewSet.as_view({'put': 'me_avatar'}),
         name='user-me-avatar'),
    path('users/<int:pk>/subscribe/',
         UsersViewSet.as_view({'post': 'subscribe', 'delete': 'unsubscribe'}),
         name='user-subscribe'),
    path('users/subscriptions/',
         UsersViewSet.as_view({'get': 'subscriptions'}),
         name='user-subscriptions'),
    #path('auth/token/login/', CustomAuthToken.as_view(),
        # name='token-login'),
]
