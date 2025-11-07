from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from django.db.models import Q
from .models import User
from .serializers import CustomUserSerializer, CustomUserCreateSerializer
from apps.recipes.models import Subscription


class CustomUserViewSet(viewsets.ModelViewSet):
    """Кастомный ViewSet для пользователей"""
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action in ['list', 'create', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Получить текущего пользователя"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Подписаться/отписаться на автора"""
        author = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            if Subscription.objects.filter(
                user=request.user, 
                author=author
            ).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if request.user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Subscription.objects.create(user=request.user, author=author)
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = get_object_or_404(
                Subscription,
                user=request.user,
                author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Получить список подписок"""
        subscriptions = User.objects.filter(
            following__user=request.user
        )
        page = self.paginate_queryset(subscriptions)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

@api_view(['POST'])
def custom_token_login(request):
    """Кастомный endpoint для получения токена с упрощенной аутентификацией"""
    username = request.data.get('username')
    password = request.data.get('password')

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.get(
            Q(username__iexact=username) | 
            Q(email__iexact=username)
        )

        if user.check_password(password):
            from rest_framework.authtoken.models import Token
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            })
        else:
            return Response({'error': 'Неверный пароль'}, status=400)

    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=400)
