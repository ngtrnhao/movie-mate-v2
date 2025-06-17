from django.db import models
from django.utils.text import slugify


class Genre(models.Model):
    name = models.CharField(max_length=100)
    # name_en = models.CharField(max_length=100, blank=True, null=True)
    # name_vi = models.CharField(max_length=100, blank=True, null=True)
    language = models.CharField(max_length=10, blank=True, null=True)  # 'en' hoặc 'vi'
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'metadata_genre'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['language']),
            models.Index(fields=['slug']),
        ]
        unique_together = ("name", "language")

    def __str__(self):
        return f"{self.name} ({self.language})"

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)
        if self.language:
            self.slug = f"{base_slug}-{self.language}"
        else:
            self.slug = base_slug
        super().save(*args,**kwargs)

class Person(models.Model) :
    name = models.CharField(max_length=255)
    biography = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null =True)
    date_of_death = models.DateField(blank=True, null= True)
    place_of_birth = models.CharField(max_length=255, blank=True,null= True)
    photo_url = models.CharField(max_length=255, blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'metadata_person'
        indexes  = [
            models.Index(fields=['name']),
        ]

class MovieCrew(models.Model):
    ROLE_CHOICES = [
        ('ACTOR','Actor'),
        ('DIRECTOR','Director'),
        ('WRITER','Writer'),
        ('PRODUCER','Producer'),
    ]

    movie = models.ForeignKey('movies.Movie',on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    character_name = models.CharField(max_length=255, blank=True,null=True)
    order_credit = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'metadata_moviecrew'
        unique_together = ('movie','person','role')
        indexes = [
            models.Index(fields=['movie','role']),
        ]
