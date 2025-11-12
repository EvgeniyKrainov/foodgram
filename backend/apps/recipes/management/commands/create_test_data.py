from apps.recipes.models import Ingredient, Recipe, Tag
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection

User = get_user_model()


class Command(BaseCommand):
    help = 'Создание тестовых данных'

    def handle(self, *args, **options):
        self.stdout.write('=== Создание тестовых данных ===')

        # ПРОПУСКАЕМ создание тегов - они уже существуют
        existing_tags = Tag.objects.all()
        if existing_tags.exists():
            self.stdout.write(
                f'ℹ️  Используем существующие теги: '
                f'{[tag.name for tag in existing_tags]}'
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Теги не найдены, но не создаем новые из-за конфликтов'
                )
            )

        # Проверяем существует ли таблица Recipe_ingredient
        table_exists = ('recipes_recipe_ingredient'
                        in connection.introspection.table_names())

        if not table_exists:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Таблица recipes_recipe_ingredient не существует. '
                    'Пропускаем создание связей рецепт-ингредиент.'
                )
            )

        # Создаем тестовых пользователей
        users_data = [
            {'username': 'chef',
             'email': 'chef@example.com',
             'password': 'testpass123',
             'first_name': 'Шеф',
             'last_name': 'Поваров'},
            {'username': 'baker',
             'email': 'baker@example.com',
             'password': 'testpass123',
             'first_name': 'Пекарь',
             'last_name': 'Булочкин'},
        ]

        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name']
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'✅ Создан пользователь: {user.username}')
            else:
                self.stdout.write(
                    f'ℹ️  Пользователь уже существует: {user.username}'
                )

        # Создаем тестовый рецепт
        chef_user = User.objects.get(username='chef')
        if not Recipe.objects.filter(name='Тестовый рецепт').exists():
            recipe = Recipe.objects.create(
                name='Тестовый рецепт',
                text='Вкусный тестовый рецепт для демонстрации',
                cooking_time=30,
                author=chef_user
            )

            # Добавляем теги к рецепту (используем существующие)
            try:
                tags = Tag.objects.all()[:2]
                if tags.exists():
                    recipe.tags.set(tags)
                    self.stdout.write(
                        f'✅ Добавлены теги к рецепту: '
                        f'{[tag.name for tag in tags]}'
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            '⚠️  Нет тегов для добавления к рецепту'
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка при добавлении тегов: {e}')
                )

            # Добавляем ингредиенты к рецепту (только если таблица существует)
            if table_exists:
                try:
                    from apps.recipes.models import RecipeIngredient
                    ingredients = Ingredient.objects.all()[:3]
                    for i, ingredient in enumerate(ingredients):
                        RecipeIngredient.objects.create(
                            recipe=recipe,
                            ingredient=ingredient,
                            amount=100 + i * 50
                        )
                    self.stdout.write(
                        f'✅ Добавлены ингредиенты к рецепту: '
                        f'{len(ingredients)} шт.'
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Ошибка при добавлении ингредиентов: {e}'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️  Ингредиенты не добавлены (проблема с таблицей)'
                    )
                )

            self.stdout.write(f'✅ Создан рецепт: {recipe.name}')
        else:
            self.stdout.write('ℹ️ Рецепт уже существует: Тестовый рецепт')

        self.stdout.write(
            self.style.SUCCESS('🎉 Тестовые данные успешно созданы')
        )
        self.stdout.write('📊 Статистика:')
        self.stdout.write(f'   👥 Пользователей: {User.objects.count()}')
        self.stdout.write(f'   🥗 Ингредиентов: {Ingredient.objects.count()}')
        self.stdout.write(f'   🏷️ Тегов: {Tag.objects.count()}')
        self.stdout.write(f'   📝 Рецептов: {Recipe.objects.count()}')
