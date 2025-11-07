from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ...models import Tag, Recipe, Ingredient, RecipeIngredient

User = get_user_model()


class Command(BaseCommand):
    help = 'Создание тестовых данных'

    def handle(self, *args, **options):
        # Создаем теги
        tags_data = [
            {'name': 'Завтрак', 'color': '#FF5733', 'slug': 'breakfast'},
            {'name': 'Обед', 'color': '#33FF57', 'slug': 'lunch'},
            {'name': 'Ужин', 'color': '#3357FF', 'slug': 'dinner'},
        ]

        for tag_data in tags_data:
            Tag.objects.get_or_create(**tag_data)

        # Создаем тестовых пользователей
        users_data = [
            {'username': 'chef', 'email': 'chef@example.com', 'password': 'testpass123'},
            {'username': 'baker', 'email': 'baker@example.com', 'password': 'testpass123'},
        ]

        for user_data in users_data:
            User.objects.get_or_create(
                username=user_data['username'],
                email=user_data['email'],
                defaults={'password': user_data['password']}
            )

        self.stdout.write(
            self.style.SUCCESS('Тестовые данные успешно созданы')
        )
