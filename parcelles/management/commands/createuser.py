from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Crée un utilisateur standard'

    def handle(self, *args, **options):
        username = 'testuser'
        password = 'testpassword123'
        if not User.objects.filter(username=username).exists():
            User.objects.create_user(username=username, password=password)
            self.stdout.write(self.style.SUCCESS(f'Utilisateur {username} créé avec succès !'))
        else:
            self.stdout.write(self.style.WARNING(f'L\'utilisateur {username} existe déjà.'))