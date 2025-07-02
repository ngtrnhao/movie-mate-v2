from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
import os

class Command(BaseCommand):
    help = 'Test Elasticsearch connection'

    def handle(self, *args, **options):
        self.stdout.write('Testing Elasticsearch connection...')

        try:
            # Get connection settings
            es_settings = settings.ELASTICSEARCH_DSL['default']

            # Print connection info (without password)
            self.stdout.write(f"Host: {es_settings['hosts']}")
            self.stdout.write(f"Username: {es_settings.get('http_auth', ['', ''])[0] if es_settings.get('http_auth') else 'None'}")

            # Test connection
            if es_settings.get('http_auth'):
                es = Elasticsearch(
                    es_settings['hosts'],
                    http_auth=es_settings['http_auth'],
                    use_ssl=es_settings.get('use_ssl', False),
                    verify_certs=es_settings.get('verify_certs', False),
                    timeout=10
                )
            else:
                es = Elasticsearch(
                    es_settings['hosts'],
                    timeout=10
                )

            # Test cluster health
            health = es.cluster.health()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Connection successful! Cluster status: {health["status"]}')
            )

            # Test if movies index exists
            if es.indices.exists(index='movies'):
                self.stdout.write(self.style.SUCCESS('✅ Movies index exists'))

                # Get index stats
                stats = es.indices.stats(index='movies')
                doc_count = stats['indices']['movies']['total']['docs']['count']
                self.stdout.write(f'📊 Documents in index: {doc_count}')
            else:
                self.stdout.write(self.style.WARNING('⚠️  Movies index does not exist'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Connection failed: {e}')
            )
            self.stdout.write('Environment variables:')
            self.stdout.write(f'  ELASTICSEARCH_CLOUD_URL: {os.environ.get("ELASTICSEARCH_CLOUD_URL", "Not set")}')
            self.stdout.write(f'  ELASTICSEARCH_USERNAME: {os.environ.get("ELASTICSEARCH_USERNAME", "Not set")}')
            self.stdout.write(f'  ELASTICSEARCH_PASSWORD: {"Set" if os.environ.get("ELASTICSEARCH_PASSWORD") else "Not set"}')
