import csv
import json

from django.core.management.base import BaseCommand
from progress.bar import IncrementalBar

from apps.recipes.models import Ingredient, Tag
from config import constants


def ingredient_create(row):
    Ingredient.objects.get_or_create(name=row[0], measurement_unit=row[1])


def load_tags(command_instance):
    """Загрузка тегов из JSON файла"""
    try:
        with open(constants.TAGS_FILE_PATH, "r", encoding="utf-8") as file:
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
                command_instance.stdout.write(
                    command_instance.style.SUCCESS(f'✅ Создан тег: {tag.name}')
                )

        return created_count

    except FileNotFoundError:
        command_instance.stderr.write(
            command_instance.style.ERROR("⚠️ Файл tags.json не найден")
        )
        return 0
    except Exception as e:
        command_instance.stderr.write(
            command_instance.style.ERROR(f"❌ Ошибка при загрузке тегов: {e}")
        )
        return 0


class Command(BaseCommand):
    help = "Load ingredients and tags to DB"

    def handle(self, *args, **options):
        # Загрузка ингредиентов
        self.stdout.write("📦 Загрузка ингредиентов...")

        try:
            with open(constants.INGREDIENTS_FILE_PATH,
                      "r", encoding="utf-8") as file:
                row_count = sum(1 for row in file)

            with open(constants.INGREDIENTS_FILE_PATH,
                      "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                bar = IncrementalBar("ingredients.csv".ljust(17),
                                     max=row_count)
                next(reader)
                for row in reader:
                    bar.next()
                    ingredient_create(row)
                bar.finish()

        except FileNotFoundError:
            self.stderr.write(
                self.style.ERROR("⚠️ Файл ingredients.csv не найден")
            )
            return
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"❌ Ошибка при загрузке ингредиентов: {e}")
            )
            return

        # Загрузка тегов
        self.stdout.write("🏷️ Загрузка тегов...")
        tags_count = load_tags(self)

        self.stdout.write(
            self.style.SUCCESS(
                f"[!] Успешно загружено: "
                f"{Ingredient.objects.count()} ингредиентов, "
                f"{tags_count} тегов"
            )
        )
