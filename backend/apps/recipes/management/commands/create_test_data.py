from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection

from apps.recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


class Command(BaseCommand):
    help = 'Создание тестовых данных'

    def handle(self, *args, **options):
        self.stdout.write('=== Создание тестовых данных ===')

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

        table_exists = ('recipes_recipeingredient'
                        in connection.introspection.table_names())

        if not table_exists:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Таблица recipes_recipeingredient не существует. '
                    'Пропускаем создание связей рецепт-ингредиент.'
                )
            )

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
            {'username': 'foodie',
             'email': 'foodie@example.com',
             'password': 'testpass123',
             'first_name': 'Гурман',
             'last_name': 'Вкуснов'},
            {'username': 'healthy',
             'email': 'healthy@example.com',
             'password': 'testpass123',
             'first_name': 'Зожник',
             'last_name': 'Правильноедов'},
            {'username': 'dessert',
             'email': 'dessert@example.com',
             'password': 'testpass123',
             'first_name': 'Сладкоежка',
             'last_name': 'Тортиков'},
        ]

        created_users = []
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
                created_users.append(user)
                self.stdout.write(f'✅ Создан пользователь: {user.username}')
            else:
                created_users.append(user)
                self.stdout.write(
                    f'ℹ️  Пользователь уже существует: {user.username}'
                )

        recipe_names = [
            "Спагетти Карбонара", "Цезарь с курицей", "Том Ям", "Борщ",
            "Плов узбекский", "Пицца Маргарита", "Стейк Рибай", "Гуакамоле",
            "Паста с лососем", "Греческий салат", "Рататуй", "Чили кон карне",
            "Фо Бо", "Такос", "Пад Тай", "Бигос", "Лазанья", "Мусака",
            "Хачапури", "Шакшука"
        ]

        recipe_descriptions = [
            "Классические спагетти с беконом и сыром пармезан",
            "Салат с листьями айсберг, курицей и соусом цезарь",
            "Острый тайский суп с креветками и грибами",
            "Традиционный украинский суп со свеклой",
            "Ароматный плов с бараниной и морковью",
            "Итальянская пицца с томатами и моцареллой",
            "Сочный стейк с розмарином и чесноком",
            "Мексиканская закуска из авокадо",
            "Паста со сливочным соусом и лососем",
            "Салат с огурцами, помидорами и фетой",
            "Французское овощное рагу",
            "Острое мексиканское блюдо с фасолью",
            "Вьетнамский суп с говядиной и рисовой лапшой",
            "Мексиканская закуска с начинкой",
            "Тайская жареная лапша",
            "Польское блюдо из тушеной капусты с мясом",
            "Итальянская запеканка с мясом и сыром",
            "Греческая запеканка с баклажанами",
            "Грузинские лепешки с сыром",
            "Израильское блюдо из яиц и помидоров"
        ]

        special_user = created_users[0]
        other_users = created_users[1:]
        created_recipes_count = 0

        for i, (name, description) in enumerate(zip(recipe_names,
                                                    recipe_descriptions)):
            if created_recipes_count < 4:
                author = special_user
            else:
                author = other_users[(created_recipes_count - 4)
                                     % len(other_users)]

            if not Recipe.objects.filter(name=name).exists():
                recipe = Recipe.objects.create(
                    name=name,
                    text=description,
                    cooking_time=30 + (i * 5),
                    author=author
                )

                try:
                    tags = Tag.objects.all()[:2]
                    if tags.exists():
                        recipe.tags.set(tags)
                        self.stdout.write(
                            f'✅ Добавлены теги к рецепту "{name}": '
                            f'{[tag.name for tag in tags]}'
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Ошибка при'
                                         f'добавлении тегов к "{name}": {e}')
                    )

                if table_exists:
                    try:
                        ingredients = Ingredient.objects.all()[:3]
                        for j, ingredient in enumerate(ingredients):
                            RecipeIngredient.objects.create(
                                recipe=recipe,
                                ingredient=ingredient,
                                amount=100 + j * 50
                            )
                        self.stdout.write(
                            f'✅ Добавлены ингредиенты к рецепту "{name}": '
                            f'{len(ingredients)} шт.'
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'❌ Ошибка при добавлении'
                                f'ингредиентов к "{name}": {e}'
                            )
                        )

                created_recipes_count += 1
                self.stdout.write(f'✅ Создан рецепт: {name} '
                                  f'(автор: {author.username})')
            else:
                self.stdout.write(f'ℹ️ Рецепт уже существует: {name}')

        self.stdout.write(
            self.style.SUCCESS('🎉 Тестовые данные успешно созданы')
        )
        self.stdout.write('📊 Статистика:')
        self.stdout.write(f'   👥 Пользователей: {User.objects.count()}')
        self.stdout.write(f'   🥗 Ингредиентов: {Ingredient.objects.count()}')
        self.stdout.write(f'   🏷️ Тегов: {Tag.objects.count()}')
        self.stdout.write(f'   📝 Рецептов: {Recipe.objects.count()}')

        self.stdout.write('\n📈 Распределение рецептов по авторам:')
        for user in created_users:
            recipe_count = Recipe.objects.filter(author=user).count()
            self.stdout.write(f'   👤 {user.username}: {recipe_count} рецептов')
