from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.following.filter(user=request.user).exists()
        return False


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя"""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 
            'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
