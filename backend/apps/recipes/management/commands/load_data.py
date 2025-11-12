import csv
import json
import os

from apps.recipes.models import Ingredient, Tag
from config import settings
from django.core.management.base import BaseCommand
from progress.bar import IncrementalBar


def ingredient_create(row):
    Ingredient.objects.get_or_create(name=row[0], measurement_unit=row[1])


def load_tags():
    """Загрузка тегов из JSON файла"""
    tags_path = os.path.join(settings.BASE_DIR, "data", "tags.json")

    try:
        with open(tags_path, "r", encoding="utf-8") as file:
            tags_data = json.load(file)

        created_count = 0
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                color=tag_data.get('color', '#808080'),
                slug=tag_data['slug']
            )
            if created:
                created_count += 1
                print(f'✅ Создан тег: {tag.name}')

        return created_count

    except FileNotFoundError:
        print("⚠️ Файл tags.json не найден")
        return 0
    except Exception as e:
        print(f"❌ Ошибка при загрузке тегов: {e}")
        return 0


class Command(BaseCommand):
    help = "Load ingredients and tags to DB"

    def handle(self, *args, **options):
        # Загрузка ингредиентов
        ingredients_path = os.path.join(settings.BASE_DIR,
                                        "data",
                                        "ingredients.csv")

        self.stdout.write("📦 Загрузка ингредиентов...")
        with open(ingredients_path, "r", encoding="utf-8") as file:
            row_count = sum(1 for row in file)

        with open(ingredients_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            bar = IncrementalBar("ingredients.csv".ljust(17), max=row_count)
            next(reader)  # Пропускаем заголовок если есть
            for row in reader:
                bar.next()
                ingredient_create(row)
            bar.finish()

        # Загрузка тегов
        self.stdout.write("🏷️ Загрузка тегов...")
        tags_count = load_tags()

        self.stdout.write(
            self.style.SUCCESS(
                "[!] Успешно загружено: " +
                f"{Ingredient.objects.count()} ингредиентов, " +
                f"{tags_count} тегов"
            )
        )
