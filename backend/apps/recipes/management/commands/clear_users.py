from django.core.management.base import BaseCommand

from apps.users.models import User


class Command(BaseCommand):
    help = 'Удаляет всех пользователей кроме суперпользователей'

    def handle(self, *args, **options):
        count, _ = User.objects.exclude(is_superuser=True).delete()
        self.stdout.write(
            self.style.SUCCESS(f'Удалено {count} пользователей')
        )
