from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Кастомная модель пользователя для Фудграма"""
    email = models.EmailField(
        'email address',
        unique=True,
        max_length=254,
    )
    first_name = models.CharField(
        'first name',
        max_length=150,
    )
    last_name = models.CharField(
        'last name', 
        max_length=150,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username
