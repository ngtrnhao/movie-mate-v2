# Generated manually to remove old poster_url indexes

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0013_alter_movietrailer_movie'),
    ]

    operations = [
        migrations.RunSQL(
            # Remove old indexes that were created incorrectly
            # Using IF EXISTS to avoid errors if indexes don't exist
            sql="""
            DO $$
            BEGIN
                -- Drop indexes if they exist, ignore errors
                BEGIN
                    DROP INDEX IF EXISTS idx_movie_poster_url;
                EXCEPTION WHEN OTHERS THEN
                    -- Index doesn't exist or can't be dropped, continue
                    NULL;
                END;

                BEGIN
                    DROP INDEX IF EXISTS idx_movie_poster_url_release;
                EXCEPTION WHEN OTHERS THEN
                    NULL;
                END;

                BEGIN
                    DROP INDEX IF EXISTS idx_movie_poster_url_not_null;
                EXCEPTION WHEN OTHERS THEN
                    NULL;
                END;
            END $$;
            """,
            reverse_sql=""
        ),
    ]
