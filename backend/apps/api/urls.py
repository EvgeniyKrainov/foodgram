from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.views import obtain_auth_token
from apps.users.views import CustomUserViewSet, custom_token_login
from apps.recipes.views import TagViewSet, IngredientViewSet, RecipeViewSet

router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

@api_view(['GET'])
def api_root(request):
    return Response({
        'message': 'Foodgram API is working!',
        'endpoints': {
            'ingredients': '/api/ingredients/',
            'tags': '/api/tags/',
            'recipes': '/api/recipes/',
            'users': '/api/users/',
            'auth': '/api/auth/',
            'admin': '/admin/',
        }
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('', include(router.urls)),
    path('auth/custom-login/', custom_token_login, name='custom-login'),
    path('auth/token/login/', obtain_auth_token, name='login'),
    # Убираем Djoser URLs временно
    # path('auth/', include('djoser.urls')),
    # path('auth/', include('djoser.urls.authtoken')),
]
