# Generated manually for performance optimization

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0006_remove_genre_name_en_remove_genre_name_vi'),
    ]

    operations = [
        migrations.RunSQL(
            # Add index for poster_url field to improve query performance
            sql="""
            CREATE INDEX IF NOT EXISTS idx_movie_poster_url
            ON movies_movie (poster_url)
            WHERE poster_url IS NOT NULL AND poster_url != '';
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS idx_movie_poster_url;
            """
        ),
    ]
