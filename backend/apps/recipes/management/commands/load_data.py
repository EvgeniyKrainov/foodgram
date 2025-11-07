import csv
import os
from django.core.management.base import BaseCommand
from ...models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из CSV файла'

    def handle(self, *args, **options):
        csv_file = 'data/ingredients.csv'

        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'Файл {csv_file} не найден')
            )
            return

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            ingredients_created = 0
  
            for row in reader:
                if len(row) == 2:
                    name, measurement_unit = row
                    ingredient, created = Ingredient.objects.get_or_create(
                        name=name.strip(),
                        measurement_unit=measurement_unit.strip()
                    )
                    if created:
                        ingredients_created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Успешно загружено {ingredients_created} ингредиентов'
                )
            )
