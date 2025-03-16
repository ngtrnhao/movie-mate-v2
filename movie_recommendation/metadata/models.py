from django.db import models
from core.models import BaseModel
# Create your models here.

class Genre(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=['name'])
        ]

    def __str__(self):
        return self.name

class Person(BaseModel):
    name = models.CharField(max_length=255)
    bio = models.TextField(null= True,blank=True)
    date_of_birth = models.DateField(null =True,blank=True)
    photo_url = models.URLField(null=True,blank= True)

    class Meta:
        indexes = [
            models.Index(fields=['name'])
        ]

    def __str__(self):
        return self.name


class MovieCrew(BaseModel):
    ROLE_CHOICES = (
        ('ACTOR','Actor'),
        ('DIRECTOR','Director'),
    )

    movie = models.ForeignKey('movies.Movie',on_delete=models.CASCADE,related_name='crew')
    person = models.ForeignKey(Person,on_delete=models.CASCADE,related_name='movie_roles')
    role = models.CharField(max_length=10,choices=ROLE_CHOICES)
    character_name = models.CharField(max_length=255,null=True,blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['movie','role']),
        ]
        unique_together = ('movie','person','role','character_name')

    def __str__(self):
        return f"{self.person.name} as {self.get_role_display()} in {self.movie.title}"
