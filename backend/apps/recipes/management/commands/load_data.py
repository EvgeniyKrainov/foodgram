import csv
import json
import os

from apps.recipes.models import Ingredient, Tag
from config import settings
from django.core.management.base import BaseCommand


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
                slug=tag_data['slug']
            )
            if created:
                created_count += 1
        return created_count

    except FileNotFoundError:
        return -1  # Код ошибки для файла не найден
    except Exception as e:
        return -2  # Код ошибки для других ошибок


class Command(BaseCommand):
    help = "Load ingredients and tags to DB"

    def handle(self, *args, **options):
        ingredients_path = os.path.join(settings.BASE_DIR,
                                        "data",
                                        "ingredients.csv")

        self.stdout.write("📦 Загрузка ингредиентов...")

        try:
            with open(ingredients_path, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader)

                count = 0
                for row in reader:
                    ingredient_create(row)
                    count += 1

                self.stdout.write(
                    self.style.SUCCESS(f"✅ Загружено {count} ингредиентов")
                )

        except FileNotFoundError:
            self.stderr.write("❌ Файл ingredients.csv не найден")
            return

        self.stdout.write("🏷️ Загрузка тегов...")
        tags_count = load_tags()

        if tags_count == -1:
            self.stderr.write("⚠️ Файл tags.json не найден")
        elif tags_count == -2:
            self.stderr.write("❌ Ошибка при загрузке тегов")
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Загружено {tags_count} тегов")
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"[!] Итог: {Ingredient.objects.count()} ингредиентов, "
                f"{Tag.objects.count()} тегов"
            )
        )
