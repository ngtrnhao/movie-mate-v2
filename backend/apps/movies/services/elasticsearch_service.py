from apps.movies.models import Movie
from apps.movies.document import MovieDocument
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections

def update_movie_index(movie_id):
    """
    Cập nhật lại index Elasticsearch cho 1 movie khi có thay đổi.
    """
    try:
        movie = Movie.objects.select_related(
            'quality_metrics', 'scheduling', 'admin_control', 'production_metrics'
        ).prefetch_related('genres', 'trailers', 'ratings').get(id=movie_id)
        doc = MovieDocument()
        doc.meta.id = movie.id
        for field in MovieDocument._fields:
            prepare_method = getattr(doc, f'prepare_{field}', None)
            if prepare_method:
                value = prepare_method(movie)
            else:
                value = getattr(movie, field, None)
            setattr(doc, field, value)
        doc.save()
        return True
    except Exception as e:
        print(f"Error updating movie index for {movie_id}: {e}")
        return False

def bulk_update_movie_index(movie_ids):
    """
    Cập nhật lại index Elasticsearch cho nhiều movie khi có thay đổi (bulk action).
    """
    movies = Movie.objects.filter(id__in=movie_ids).select_related(
        'quality_metrics', 'scheduling', 'admin_control', 'production_metrics'
    ).prefetch_related('genres', 'trailers', 'ratings')
    actions = []
    for movie in movies:
        doc = MovieDocument()
        doc.meta.id = movie.id
        for field in MovieDocument._fields:
            prepare_method = getattr(doc, f'prepare_{field}', None)
            if prepare_method:
                value = prepare_method(movie)
            else:
                value = getattr(movie, field, None)
            setattr(doc, field, value)
        actions.append(doc.to_dict(include_meta=True))
    if actions:
        bulk(connections.get_connection(), actions, chunk_size=100, raise_on_error=False)
