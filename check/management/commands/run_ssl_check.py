from django.core.management.base import BaseCommand

from check.models import Domain


class Command(BaseCommand):
    help = 'Scan domains and verify SSL certificates'

    def handle(self, *args, **options):
        Domain.objects.check_certs()

        self.stdout.write(self.style.SUCCESS('Complete'))
