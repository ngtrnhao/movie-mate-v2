from django.core.management.base import BaseCommand
from django_elasticsearch_dsl.registries import registry

class Command(BaseCommand):
    help = 'Setup Elasticsearch indexs'

    def handle(self, *args, **options):
        self.stdou.write('Creating Elasticsearch indexes...')

        try:
            #Create all indexes
            registry.update()
            self.stdout.write(
                self.style.SUCCESS('Successfully created Elasticsearch indexes')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating Elasticsearch indexes: {e}')
            )