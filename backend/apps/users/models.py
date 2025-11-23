from django.contrib.auth.models import AbstractUser
from django.db import models

from config.constants import MAX_LENGHT_EMAIL, MAX_LENGHT_FIRST_NAME


class User(AbstractUser):
    email = models.EmailField(
        max_length=MAX_LENGHT_EMAIL,
        unique=True,
        verbose_name="Email"
    )
    first_name = models.CharField(
        max_length=MAX_LENGHT_FIRST_NAME,
        verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=MAX_LENGHT_FIRST_NAME,
        verbose_name="Фамилия"
    )
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriber",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscribing",
        verbose_name="Подписан",
    )

    class Meta:
        verbose_name = "Подписка на авторов"
        verbose_name_plural = "Подписки на авторов"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"],
                name="unique_subscribe"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.author.username}"
