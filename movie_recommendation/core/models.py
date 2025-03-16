from django.db import models

# Create your models here.
class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class BaseModel(TimestampMixin):
    class Meta:
        abstract = True
