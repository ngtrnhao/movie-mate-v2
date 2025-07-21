from django.core.management.base import BaseCommand
from django.db import transaction
from apps.movies.models import Movie, MovieQualityMetrics, MovieScheduling
from apps.movies.document import MovieDocument
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections
from elasticsearch import ConnectionTimeout, ConnectionError, RequestError
import logging
import time
import json
import os
from django.db import models
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Index movies in Elasticsearch with enhanced normalized structure support and connection resilience'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Number of movies to process per batch (default: 500)'
        )
        parser.add_argument(
            '--rebuild',
            action='store_true',
            help='Rebuild the index from scratch'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean orphaned documents'
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Verify index integrity after indexing'
        )
        parser.add_argument(
            '--quality-metrics-only',
            action='store_true',
            help='Only index movies with quality metrics'
        )
        parser.add_argument(
            '--scheduling-only',
            action='store_true',
            help='Only index movies with scheduling data'
        )
        parser.add_argument(
            '--start-id',
            type=int,
            help='Start indexing from specific movie ID'
        )
        parser.add_argument(
            '--end-id',
            type=int,
            help='End indexing at specific movie ID'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reindexing even if document already exists'
        )
        parser.add_argument(
            '--all-movies',
            action='store_true',
            help='Index ALL movies including those without poster/tmdb_id (717,981 total)'
        )
        parser.add_argument(
            '--resume',
            action='store_true',
            help='Resume from last checkpoint if available'
        )
        parser.add_argument(
            '--max-retries',
            type=int,
            default=5,
            help='Maximum number of retries for failed operations (default: 5)'
        )
        parser.add_argument(
            '--retry-delay',
            type=float,
            default=2.0,
            help='Delay between retries in seconds (default: 2.0)'
        )
        parser.add_argument(
            '--checkpoint-interval',
            type=int,
            default=10,
            help='Save checkpoint every N batches (default: 10)'
        )
        parser.add_argument(
            '--connection-timeout',
            type=int,
            default=60,
            help='Elasticsearch connection timeout in seconds (default: 60)'
        )

    def handle(self, *args, **options):
        self.batch_size = options.get('batch_size', 500)
        self.rebuild = options.get('rebuild', False)
        self.clean = options.get('clean', False)
        self.verify = options.get('verify', False)
        self.quality_metrics_only = options.get('quality_metrics_only', False)
        self.scheduling_only = options.get('scheduling_only', False)
        self.start_id = options.get('start_id')
        self.end_id = options.get('end_id')
        self.force = options.get('force', False)
        self.all_movies = options.get('all_movies', False)
        self.resume = options.get('resume', False)
        self.max_retries = options.get('max_retries', 5)
        self.retry_delay = options.get('retry_delay', 2.0)
        self.checkpoint_interval = options.get('checkpoint_interval', 10)
        self.connection_timeout = options.get('connection_timeout', 60)

        # Set internal flag for filtering
        self._index_all_movies = self.all_movies

        # Initialize checkpoint system
        self.checkpoint_file = os.path.join(settings.BASE_DIR, 'index_movies_checkpoint.json')
        self.checkpoint_data = self._load_checkpoint()

        self.stdout.write(self.style.SUCCESS('🚀 Enhanced Movie Indexing with Connection Resilience'))
        self.stdout.write(f'📊 Batch size: {self.batch_size}')
        self.stdout.write(f'🔄 Max retries: {self.max_retries}')
        self.stdout.write(f'⏱️ Retry delay: {self.retry_delay}s')
        self.stdout.write(f'💾 Checkpoint interval: {self.checkpoint_interval} batches')

        if self.all_movies:
            self.stdout.write(self.style.WARNING('🌍 ALL MOVIES MODE: Indexing all 717,981 movies'))

        # Check Elasticsearch connection with retry
        if not self._check_elasticsearch_connection():
            return

        if self.rebuild:
            if not self._rebuild_index():
                return

        # Build optimized query for movies with normalized relationships
        movies_queryset = self._build_movies_queryset(
            self.quality_metrics_only, self.scheduling_only, self.start_id, self.end_id
        )

        total = movies_queryset.count()
        self.stdout.write(f'📊 Found {total:,} movies to index')

        if total == 0:
            self.stdout.write(self.style.WARNING('⚠️ No movies found to index'))
            return

        # Resume from checkpoint if requested
        start_batch = 0
        if self.resume and self.checkpoint_data:
            start_batch = self.checkpoint_data.get('last_batch', 0)
            self.stdout.write(f'🔄 Resuming from batch {start_batch}')

        # Index movies in batches with resilience
        self._index_movies_with_resilience(movies_queryset, total, start_batch)

        # Verify index integrity
        if self.verify:
            self._verify_index_integrity()

        # Clean orphaned documents
        if self.clean:
            self._clean_orphaned_documents()

        # Final index statistics
        self._show_index_statistics()

        # Clean up checkpoint
        self._cleanup_checkpoint()

    def _load_checkpoint(self):
        """Load checkpoint data from file"""
        try:
            if os.path.exists(self.checkpoint_file):
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load checkpoint: {e}")
        return {}

    def _save_checkpoint(self, batch_start, indexed_count, error_count, skipped_count):
        """Save checkpoint data to file"""
        try:
            checkpoint_data = {
                'last_batch': batch_start,
                'indexed_count': indexed_count,
                'error_count': error_count,
                'skipped_count': skipped_count,
                'timestamp': time.time(),
                'options': {
                    'batch_size': self.batch_size,
                    'all_movies': self.all_movies,
                    'quality_metrics_only': self.quality_metrics_only,
                    'scheduling_only': self.scheduling_only,
                    'start_id': self.start_id,
                    'end_id': self.end_id,
                    'force': self.force
                }
            }

            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

        except Exception as e:
            logger.warning(f"Could not save checkpoint: {e}")

    def _cleanup_checkpoint(self):
        """Remove checkpoint file after successful completion"""
        try:
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)
                self.stdout.write(self.style.SUCCESS('🗑️ Checkpoint file cleaned up'))
        except Exception as e:
            logger.warning(f"Could not cleanup checkpoint: {e}")

    def _check_elasticsearch_connection(self):
        """Check Elasticsearch connection with retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                es = connections.get_connection()
                health = es.cluster.health(timeout=f"{self.connection_timeout}s")
                self.stdout.write(self.style.SUCCESS(f'✅ Elasticsearch cluster health: {health["status"]}'))
                return True
            except (ConnectionError, ConnectionTimeout) as e:
                if attempt < self.max_retries:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Elasticsearch connection attempt {attempt + 1}/{self.max_retries + 1} failed: {e}')
                    )
                    self.stdout.write(f'⏳ Retrying in {self.retry_delay}s...')
                    time.sleep(self.retry_delay)
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Elasticsearch connection failed after {self.max_retries + 1} attempts: {e}'))
                    return False
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Elasticsearch connection failed: {e}'))
                return False

    def _rebuild_index(self):
        """Rebuild Elasticsearch index with retry logic"""
        self.stdout.write('🔄 Rebuilding Elasticsearch index...')

        for attempt in range(self.max_retries + 1):
            try:
                es = connections.get_connection()

                # Delete existing index
                if es.indices.exists(index='movies'):
                    es.indices.delete(index='movies')
                    self.stdout.write(self.style.SUCCESS('🗑️ Deleted existing index'))

                # Create new index with updated mapping
                MovieDocument.init()
                self.stdout.write(self.style.SUCCESS('🏗️ Created new index with normalized structure mapping'))
                return True

            except (ConnectionError, ConnectionTimeout) as e:
                if attempt < self.max_retries:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Rebuild attempt {attempt + 1}/{self.max_retries + 1} failed: {e}')
                    )
                    self.stdout.write(f'⏳ Retrying in {self.retry_delay}s...')
                    time.sleep(self.retry_delay)
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Error rebuilding index after {self.max_retries + 1} attempts: {e}'))
                    return False
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error rebuilding index: {e}'))
                return False

    def _index_movies_with_resilience(self, movies_queryset, total, start_batch=0):
        """Index movies with connection resilience and checkpoint system"""
        indexed_count = self.checkpoint_data.get('indexed_count', 0)
        error_count = self.checkpoint_data.get('error_count', 0)
        skipped_count = self.checkpoint_data.get('skipped_count', 0)
        start_time = time.time()

        self.stdout.write(f'🔄 Starting indexing process from batch {start_batch}...')

        for batch_start in range(start_batch, total, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total)
            batch_success = False

            # Retry logic for each batch
            for retry_attempt in range(self.max_retries + 1):
                try:
                    # Get batch with all necessary relationships
                    batch_movies = movies_queryset[batch_start:batch_end]

                    # Index batch with enhanced error handling
                    batch_result = self._index_batch_with_resilience(batch_movies, force=self.force)

                    indexed_count += batch_result['indexed']
                    error_count += batch_result['errors']
                    skipped_count += batch_result['skipped']

                    batch_success = True
                    break

                except (ConnectionError, ConnectionTimeout) as e:
                    if retry_attempt < self.max_retries:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️ Batch {batch_start}-{batch_end} attempt {retry_attempt + 1}/{self.max_retries + 1} failed: {e}')
                        )
                        self.stdout.write(f'⏳ Retrying in {self.retry_delay}s...')
                        time.sleep(self.retry_delay)
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Batch {batch_start}-{batch_end} failed after {self.max_retries + 1} attempts: {e}')
                        )
                        error_count += len(batch_movies) if 'batch_movies' in locals() else self.batch_size

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error processing batch {batch_start}-{batch_end}: {e}')
                    )
                    error_count += len(batch_movies) if 'batch_movies' in locals() else self.batch_size
                    break

            # Progress report
            progress = (batch_end / total) * 100
            elapsed = time.time() - start_time
            estimated_total = (elapsed / batch_end) * total if batch_end > 0 else 0
            remaining = max(0, estimated_total - elapsed)

            self.stdout.write(
                f'📈 Progress: {progress:.1f}% ({batch_end:,}/{total:,}) - '
                f'✅ Indexed: {indexed_count:,} | '
                f'❌ Errors: {error_count:,} | '
                f'⏭️ Skipped: {skipped_count:,} | '
                f'⏰ ETA: {remaining:.0f}s'
            )

            # Save checkpoint periodically
            if batch_start % (self.checkpoint_interval * self.batch_size) == 0:
                self._save_checkpoint(batch_start, indexed_count, error_count, skipped_count)
                self.stdout.write(f'💾 Checkpoint saved at batch {batch_start}')

        # Final report
        total_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f'🎉 Indexing completed in {total_time:.1f}s'))
        self.stdout.write(f'📊 Final stats:')
        self.stdout.write(f'  ✅ Successfully indexed: {indexed_count:,}')
        self.stdout.write(f'  ❌ Errors: {error_count:,}')
        self.stdout.write(f'  ⏭️ Skipped: {skipped_count:,}')
        self.stdout.write(f'  🚀 Rate: {indexed_count/total_time:.1f} docs/sec')

    def _index_batch_with_resilience(self, movies, force=False):
        """Index a batch of movies with enhanced error handling and retry logic"""
        actions = []
        indexed = 0
        errors = 0
        skipped = 0

        for movie in movies:
            try:
                # Check if document should be skipped
                if not force and self._should_skip_movie(movie):
                    skipped += 1
                    continue

                # Create document
                doc = MovieDocument()
                doc.meta.id = movie.id

                # Map all fields using prepare methods
                self._prepare_document_fields(doc, movie)

                # Add to bulk actions
                actions.append(doc.to_dict(include_meta=True))
                indexed += 1

            except Exception as e:
                logger.error(f"Error preparing movie {movie.id}: {str(e)}")
                errors += 1
                continue

        # Bulk index the batch with retry logic
        if actions:
            for retry_attempt in range(self.max_retries + 1):
                try:
                    success_count, failed_items = bulk(
                        connections.get_connection(),
                        actions,
                        chunk_size=100,
                        raise_on_error=False,
                        request_timeout=self.connection_timeout
                    )

                    if failed_items:
                        errors += len(failed_items)
                        for item in failed_items:
                            logger.error(f"Failed to index item: {item}")

                    break

                except (ConnectionError, ConnectionTimeout) as e:
                    if retry_attempt < self.max_retries:
                        logger.warning(f"Bulk indexing attempt {retry_attempt + 1}/{self.max_retries + 1} failed: {e}")
                        time.sleep(self.retry_delay)
                    else:
                        logger.error(f"Bulk indexing failed after {self.max_retries + 1} attempts: {e}")
                        errors += len(actions)
                        break

                except Exception as e:
                    logger.error(f"Bulk indexing error: {str(e)}")
                    errors += len(actions)
                    break

        return {
            'indexed': indexed,
            'errors': errors,
            'skipped': skipped
        }

    def _build_movies_queryset(self, quality_metrics_only, scheduling_only, start_id, end_id):
        """Build optimized queryset with all necessary relationships"""
        queryset = Movie.objects.select_related(
            'moviemetadata',
            'quality_metrics',
            'scheduling',
            'production_metrics'
        ).prefetch_related(
            'genres',
            'ratings',
            'trailers',
            'cast',
            'movieimage_set'
        )

        # Minimal filter - only exclude movies without basic title or completely empty titles
        # This allows indexing of ALL movies (717,981 total)
        if not self._index_all_movies:
            queryset = queryset.filter(
                title__isnull=False,
            ).exclude(
                title__exact=''
            )

        # Quality metrics filtering
        if quality_metrics_only:
            queryset = queryset.filter(quality_metrics__isnull=False)
            self.stdout.write('🎯 Filtering: Only movies with quality metrics')

        # Scheduling filtering
        if scheduling_only:
            queryset = queryset.filter(scheduling__isnull=False)
            self.stdout.write('🎯 Filtering: Only movies with scheduling data')

        # ID range filtering
        if start_id:
            queryset = queryset.filter(id__gte=start_id)
            self.stdout.write(f'🎯 Filtering: Starting from ID {start_id}')

        if end_id:
            queryset = queryset.filter(id__lte=end_id)
            self.stdout.write(f'🎯 Filtering: Ending at ID {end_id}')

        return queryset.order_by('id')

    def _index_batch(self, movies, force=False):
        """Index a batch of movies with enhanced error handling"""
        actions = []
        indexed = 0
        errors = 0
        skipped = 0

        for movie in movies:
            try:
                # Check if document should be skipped
                if not force and self._should_skip_movie(movie):
                    skipped += 1
                    continue

                # Create document
                doc = MovieDocument()
                doc.meta.id = movie.id

                # Map all fields using prepare methods
                self._prepare_document_fields(doc, movie)

                # Add to bulk actions
                actions.append(doc.to_dict(include_meta=True))
                indexed += 1

            except Exception as e:
                logger.error(f"Error preparing movie {movie.id}: {str(e)}")
                errors += 1
                continue

        # Bulk index the batch
        if actions:
            try:
                success_count, failed_items = bulk(
                    connections.get_connection(),
                    actions,
                    chunk_size=100,
                    raise_on_error=False,
                    request_timeout=60
                )

                if failed_items:
                    errors += len(failed_items)
                    for item in failed_items:
                        logger.error(f"Failed to index item: {item}")

            except Exception as e:
                logger.error(f"Bulk indexing error: {str(e)}")
                errors += len(actions)

        return {
            'indexed': indexed,
            'errors': errors,
            'skipped': skipped
        }

    def _prepare_document_fields(self, doc, movie):
        """Prepare all document fields with enhanced relationship handling"""
        # Use all prepare methods from MovieDocument
        for field_name in MovieDocument._fields:
            try:
                prepare_method = getattr(doc, f'prepare_{field_name}', None)
                if prepare_method:
                    value = prepare_method(movie)
                    setattr(doc, field_name, value)
                else:
                    # Direct field mapping
                    value = getattr(movie, field_name, None)
                    setattr(doc, field_name, value)
            except Exception as e:
                logger.warning(f"Error preparing field {field_name} for movie {movie.id}: {str(e)}")

    def _should_skip_movie(self, movie):
        """Determine if a movie should be skipped during indexing"""
        # If --all-movies flag is used, skip very few movies
        if hasattr(self, '_index_all_movies') and self._index_all_movies:
            # Only skip movies with completely empty titles
            if not movie.title or movie.title.strip() == '':
                return True
            return False

        # Default behavior: Skip movies without essential data
        if not movie.poster_url or not movie.title:
            return True

        # Skip movies that are not ready for indexing
        if hasattr(movie, 'quality_metrics') and movie.quality_metrics:
            if not movie.quality_metrics.minimum_quality_met:
                return True

        return False

    def _verify_index_integrity(self):
        """Verify index integrity and consistency"""
        self.stdout.write('🔍 Verifying index integrity...')

        try:
            es = connections.get_connection()

            # Check index health
            health = es.cluster.health(index='movies')
            self.stdout.write(f'📊 Index health: {health["status"]}')

            # Check document count
            stats = es.indices.stats(index='movies')
            doc_count = stats['indices']['movies']['total']['docs']['count']

            # Compare with database count
            db_count = Movie.objects.filter(
                poster_url__isnull=False,
                title__isnull=False
            ).exclude(
                poster_url__exact='',
                title__exact=''
            ).count()

            self.stdout.write(f'📊 Documents in index: {doc_count}')
            self.stdout.write(f'📊 Movies in database: {db_count}')

            coverage = (doc_count / db_count) * 100 if db_count > 0 else 0
            self.stdout.write(f'📊 Index coverage: {coverage:.1f}%')

            if coverage < 95:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Low index coverage: {coverage:.1f}%')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Good index coverage: {coverage:.1f}%')
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error verifying index: {e}'))

    def _clean_orphaned_documents(self):
        """Clean orphaned documents from the index"""
        self.stdout.write('🧹 Cleaning orphaned documents...')

        try:
            es = connections.get_connection()

            # Get all document IDs from index
            search_body = {
                'query': {'match_all': {}},
                '_source': False,
                'size': 10000
            }

            response = es.search(index='movies', body=search_body)
            indexed_ids = {int(hit['_id']) for hit in response['hits']['hits']}

            # Get all movie IDs from database
            db_ids = set(Movie.objects.filter(
                poster_url__isnull=False,
                title__isnull=False
            ).exclude(
                poster_url__exact='',
                title__exact=''
            ).values_list('id', flat=True))

            # Find orphaned documents
            orphaned_ids = indexed_ids - db_ids

            if orphaned_ids:
                self.stdout.write(f'🗑️ Found {len(orphaned_ids)} orphaned documents')

                # Delete orphaned documents
                actions = []
                for doc_id in orphaned_ids:
                    actions.append({
                        '_op_type': 'delete',
                        '_index': 'movies',
                        '_id': doc_id
                    })

                success_count, failed_items = bulk(
                    es,
                    actions,
                    chunk_size=100,
                    raise_on_error=False
                )

                self.stdout.write(f'🗑️ Deleted {success_count} orphaned documents')

                if failed_items:
                    self.stdout.write(f'❌ Failed to delete {len(failed_items)} documents')
            else:
                self.stdout.write('✅ No orphaned documents found')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error cleaning orphaned documents: {e}'))

    def _show_index_statistics(self):
        """Show comprehensive index statistics"""
        self.stdout.write('📊 Index Statistics:')

        try:
            es = connections.get_connection()

            # Basic stats
            stats = es.indices.stats(index='movies')
            movie_stats = stats['indices']['movies']

            total_docs = movie_stats['total']['docs']['count']
            index_size = movie_stats['total']['store']['size_in_bytes']

            self.stdout.write(f'  📄 Total documents: {total_docs:,}')
            self.stdout.write(f'  💾 Index size: {index_size / (1024*1024):.1f} MB')

            # Quality metrics statistics
            quality_agg = es.search(
                index='movies',
                body={
                    'size': 0,
                    'aggs': {
                        'avg_quality_score': {'avg': {'field': 'quality_score'}},
                        'avg_completeness': {'avg': {'field': 'content_completeness'}},
                        'quality_distribution': {
                            'range': {
                                'field': 'quality_score',
                                'ranges': [
                                    {'to': 3, 'key': 'poor'},
                                    {'from': 3, 'to': 6, 'key': 'fair'},
                                    {'from': 6, 'to': 8, 'key': 'good'},
                                    {'from': 8, 'key': 'excellent'}
                                ]
                            }
                        }
                    }
                }
            )

            aggs = quality_agg['aggregations']
            avg_quality = aggs['avg_quality_score']['value']
            avg_completeness = aggs['avg_completeness']['value']

            if avg_quality:
                self.stdout.write(f'  🎯 Average quality score: {avg_quality:.1f}')
            if avg_completeness:
                self.stdout.write(f'  📋 Average completeness: {avg_completeness:.1f}')

            # Quality distribution
            quality_dist = aggs['quality_distribution']['buckets']
            for bucket in quality_dist:
                self.stdout.write(f'  📊 {bucket["key"]}: {bucket["doc_count"]:,} movies')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error showing statistics: {e}'))
