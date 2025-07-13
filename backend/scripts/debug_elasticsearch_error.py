#!/usr/bin/env python
"""
Debug script để tìm và sửa lỗi Elasticsearch: unsupported operand type(s) for -: 'str' and 'int'
"""

import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.utils import timezone
from apps.movies.services.search_service import MovieSearchService
from apps.movies.models import Movie
import logging

logger = logging.getLogger(__name__)

def debug_elasticsearch_error():
    """Debug Elasticsearch error"""

    print("🔍 DEBUGGING ELASTICSEARCH ERROR")
    print("=" * 50)

    # Initialize search service
    search_service = MovieSearchService()

    if not search_service.connection_available:
        print("❌ Elasticsearch connection not available")
        return

    print("✅ Elasticsearch connection available")

    # Test basic search
    print("\n📊 Testing basic search...")
    try:
        basic_params = {
            'page': 1,
            'page_size': 5
        }

        result = search_service.search(basic_params)
        if result:
            print(f"✅ Basic search successful: {result['total_count']} results")
        else:
            print("❌ Basic search failed")

    except Exception as e:
        print(f"❌ Basic search error: {str(e)}")
        import traceback
        traceback.print_exc()

    # Test search with query
    print("\n🔍 Testing search with query...")
    try:
        query_params = {
            'q': 'test',
            'page': 1,
            'page_size': 5
        }

        result = search_service.search(query_params)
        if result:
            print(f"✅ Query search successful: {result['total_count']} results")
        else:
            print("❌ Query search failed")

    except Exception as e:
        print(f"❌ Query search error: {str(e)}")
        import traceback
        traceback.print_exc()

    # Test search with filters
    print("\n🎯 Testing search with filters...")
    try:
        filter_params = {
            'genres': ['Action'],
            'year_from': 2020,
            'page': 1,
            'page_size': 5
        }

        result = search_service.search(filter_params)
        if result:
            print(f"✅ Filter search successful: {result['total_count']} results")
        else:
            print("❌ Filter search failed")

    except Exception as e:
        print(f"❌ Filter search error: {str(e)}")
        import traceback
        traceback.print_exc()

    # Test admin mode search
    print("\n⚙️ Testing admin mode search...")
    try:
        admin_params = {
            'admin_mode': True,
            'page': 1,
            'page_size': 5
        }

        result = search_service.search(admin_params, admin_mode=True)
        if result:
            print(f"✅ Admin search successful: {result['total_count']} results")
        else:
            print("❌ Admin search failed")

    except Exception as e:
        print(f"❌ Admin search error: {str(e)}")
        import traceback
        traceback.print_exc()

def check_document_mapping():
    """Check Elasticsearch document mapping"""

    print("\n📋 CHECKING ELASTICSEARCH DOCUMENT MAPPING")
    print("=" * 50)

    try:
        from elasticsearch import Elasticsearch
        from django.conf import settings

        # Initialize client
        if hasattr(settings, 'ELASTICSEARCH_DSL') and settings.ELASTICSEARCH_DSL:
            es_config = settings.ELASTICSEARCH_DSL['default']

            # Build connection parameters
            connection_params = {
                'hosts': es_config['hosts'],
                'timeout': es_config.get('timeout', 30),
            }

            # Add authentication if available
            if es_config.get('http_auth'):
                connection_params['http_auth'] = es_config['http_auth']

            # Add SSL configuration if available
            if es_config.get('use_ssl', False):
                connection_params['scheme'] = 'https'
                if es_config.get('verify_certs') is not None:
                    connection_params['verify_certs'] = es_config['verify_certs']

            client = Elasticsearch(**connection_params)
        else:
            client = Elasticsearch(['localhost:9200'])

        # Get mapping
        mapping = client.indices.get_mapping(index='movies')
        print("✅ Successfully retrieved mapping")

        # Check specific fields that might cause type issues
        properties = mapping['movies']['mappings']['properties']

        print("\n🔍 Checking field types:")

        # Check numeric fields
        numeric_fields = ['quality_score', 'content_completeness', 'performance_score',
                         'trending_score', 'engagement_rate', 'homepage_views',
                         'user_favorites_count', 'campaign_priority', 'admin_priority']

        for field in numeric_fields:
            if field in properties:
                field_type = properties[field]['type']
                print(f"   • {field}: {field_type}")

                # Check if numeric field is mapped as text
                if field_type == 'text' and field in ['quality_score', 'content_completeness',
                                                     'performance_score', 'trending_score',
                                                     'engagement_rate', 'homepage_views',
                                                     'user_favorites_count']:
                    print(f"     ⚠️ WARNING: {field} should be numeric but is mapped as text!")
            else:
                print(f"   • {field}: NOT FOUND")

        # Check date fields
        date_fields = ['release_date', 'created_at', 'last_quality_check',
                      'scheduling_publish_date', 'next_action_date']

        for field in date_fields:
            if field in properties:
                field_type = properties[field]['type']
                print(f"   • {field}: {field_type}")
            else:
                print(f"   • {field}: NOT FOUND")

        return True

    except Exception as e:
        print(f"❌ Error checking mapping: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_sample_documents():
    """Check sample documents for type issues"""

    print("\n📄 CHECKING SAMPLE DOCUMENTS")
    print("=" * 50)

    try:
        from elasticsearch import Elasticsearch
        from django.conf import settings

        # Initialize client
        if hasattr(settings, 'ELASTICSEARCH_DSL') and settings.ELASTICSEARCH_DSL:
            es_config = settings.ELASTICSEARCH_DSL['default']

            # Build connection parameters
            connection_params = {
                'hosts': es_config['hosts'],
                'timeout': es_config.get('timeout', 30),
            }

            # Add authentication if available
            if es_config.get('http_auth'):
                connection_params['http_auth'] = es_config['http_auth']

            # Add SSL configuration if available
            if es_config.get('use_ssl', False):
                connection_params['scheme'] = 'https'
                if es_config.get('verify_certs') is not None:
                    connection_params['verify_certs'] = es_config['verify_certs']

            client = Elasticsearch(**connection_params)
        else:
            client = Elasticsearch(['localhost:9200'])

        # Get sample documents
        response = client.search(
            index='movies',
            body={
                'size': 3,
                'query': {'match_all': {}}
            }
        )

        print(f"✅ Retrieved {len(response['hits']['hits'])} sample documents")

        for i, hit in enumerate(response['hits']['hits']):
            print(f"\n📄 Document {i+1} (ID: {hit['_id']}):")
            source = hit['_source']

            # Check problematic fields
            problematic_fields = ['quality_score', 'content_completeness', 'performance_score',
                                'trending_score', 'engagement_rate', 'homepage_views',
                                'user_favorites_count', 'campaign_priority', 'admin_priority']

            for field in problematic_fields:
                if field in source:
                    value = source[field]
                    value_type = type(value).__name__
                    print(f"   • {field}: {value} (type: {value_type})")

                    # Check if numeric field has string value
                    if value_type == 'str' and field in ['quality_score', 'content_completeness',
                                                        'performance_score', 'trending_score',
                                                        'engagement_rate', 'homepage_views',
                                                        'user_favorites_count']:
                        print(f"     ⚠️ WARNING: {field} should be numeric but has string value!")
                else:
                    print(f"   • {field}: NOT PRESENT")

        return True

    except Exception as e:
        print(f"❌ Error checking documents: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def fix_document_mapping():
    """Fix document mapping issues"""

    print("\n🔧 FIXING DOCUMENT MAPPING")
    print("=" * 50)

    try:
        from elasticsearch import Elasticsearch
        from django.conf import settings

        # Initialize client
        if hasattr(settings, 'ELASTICSEARCH_DSL') and settings.ELASTICSEARCH_DSL:
            es_config = settings.ELASTICSEARCH_DSL['default']
            client = Elasticsearch(
                hosts=es_config['hosts'],
                http_auth=es_config.get('http_auth'),
                use_ssl=es_config.get('use_ssl', False),
                verify_certs=es_config.get('verify_certs', True),
                timeout=es_config.get('timeout', 30)
            )
        else:
            client = Elasticsearch(['localhost:9200'])

        # Check if index exists
        if not client.indices.exists(index='movies'):
            print("❌ Index 'movies' does not exist")
            return False

        # Create new index with correct mapping
        new_index = 'movies_fixed'

        # Define correct mapping
        mapping = {
            'mappings': {
                'properties': {
                    'quality_score': {'type': 'float'},
                    'content_completeness': {'type': 'float'},
                    'performance_score': {'type': 'float'},
                    'trending_score': {'type': 'float'},
                    'engagement_rate': {'type': 'float'},
                    'homepage_views': {'type': 'integer'},
                    'user_favorites_count': {'type': 'integer'},
                    'campaign_priority': {'type': 'integer'},
                    'admin_priority': {'type': 'integer'},
                    'release_date': {'type': 'date'},
                    'created_at': {'type': 'date'},
                    'last_quality_check': {'type': 'date'},
                    'scheduling_publish_date': {'type': 'date'},
                    'next_action_date': {'type': 'date'}
                }
            }
        }

        # Create new index
        client.indices.create(index=new_index, body=mapping)
        print(f"✅ Created new index: {new_index}")

        # Reindex data
        reindex_body = {
            'source': {'index': 'movies'},
            'dest': {'index': new_index}
        }

        client.reindex(body=reindex_body, wait_for_completion=True)
        print("✅ Reindexed data to new index")

        # Update search service to use new index
        print("📝 Update search_service.py to use new index name")

        return True

    except Exception as e:
        print(f"❌ Error fixing mapping: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Elasticsearch Error Debug")

    # Run debug steps
    debug_elasticsearch_error()
    check_document_mapping()
    check_sample_documents()

    # Ask user if they want to fix mapping
    print("\n" + "=" * 50)
    print("🔧 Would you like to attempt to fix the mapping? (y/n)")

    # For now, just show the option
    print("To fix mapping issues, run: fix_document_mapping()")

    print("\n�� Debug completed!")
