from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from movies.models import Movie
from metadata.models import Genre,Person


@registry.register_document
class MovieDocument(Document):
    title = fields.TextField(analyzer='standard')
    overview = fields.TextField()


    #Nested fields
    genres = fields.NestedField(properties={
        'name': fields.TextField(),
        'slug': fields.KeywordField(),
    })
    release_date = fields.DateField()

    class Index:
        name ='movies'
        settings = {'number_of_shards':5,'number_of_replicas':1}

    class Django:
        model = Movie
        fields = ['id','poster_url','imdb_rating']

        #Sử dụng related_models để tự động cập nhật document khi có thay đôổi
        related_models = [Genre]

    def get_instances_from_related(self, related_instance):
        """Cập nhật document khi các model liên quan thay đổi"""
        if isinstance(related_instance, Genre):
            return related_instance.movies.all()

@registry.register_document
class GenreDocument(Document):
    name = fields.TextField(analyzer='standard')
    slug = fields.KeywordField()

    class Index:
        name = 'genres'
        settings = {'number_of_shards':1,'number_of_replicas':0}
    class Django:
        model = Genre
        fields = ['id']
@registry.register_document
class PersonDocument(Document):
    name= fields.TextField(analyzer='standard')
    bio=fields.TextField()

    class Index:
        name = 'persons'
        settings={'number_of_shards':3,'number_of_replicas':1}
    class Django:
        model = Person
        fields = ['id','date_of_birth','photo_url']