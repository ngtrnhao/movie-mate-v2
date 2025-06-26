from django.db import migrations, models
import django.db.models.deletion
from django.db.models import JSONField


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0006_remove_genre_name_en_remove_genre_name_vi'),
    ]

    operations = [
        # Tạo bảng GenreSummary
        migrations.CreateModel(
            name='GenreSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(max_length=10)),
                ('movie_count', models.IntegerField(default=0)),
                ('latest_movie_data', JSONField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('genre', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='summary', to='metadata.genre')),
            ],
            options={
                'db_table': 'metadata_genre_summary',
            },
        ),

        # Tạo unique constraint
        migrations.AlterUniqueTogether(
            name='genresummary',
            unique_together={('genre', 'language')},
        ),

        # Tạo function để cập nhật summary
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION update_genre_summary()
            RETURNS TRIGGER AS $$
            DECLARE
                genre_id INTEGER;
            BEGIN
                -- Xác định genre_id dựa trên operation
                IF TG_OP = 'DELETE' THEN
                    genre_id := OLD.genre_id;
                ELSE
                    genre_id := NEW.genre_id;
                END IF;

                -- Cập nhật summary cho genre
                INSERT INTO metadata_genre_summary (genre_id, language, movie_count, latest_movie_data, last_updated)
                SELECT
                    g.id,
                    g.language,
                    COUNT(mg.movie_id) as movie_count,
                    (
                        SELECT json_build_object(
                            'id', m.id,
                            'title', m.title,
                            'poster_url', m.poster_url,
                            'release_date', m.release_date
                        )
                        FROM movies_movie m
                        INNER JOIN movies_movie_genres mg2 ON m.id = mg2.movie_id
                        WHERE mg2.genre_id = g.id
                        AND m.poster_url IS NOT NULL
                        AND m.poster_url != ''
                        ORDER BY m.release_date DESC
                        LIMIT 1
                    ) as latest_movie_data,
                    NOW()
                FROM metadata_genre g
                LEFT JOIN movies_movie_genres mg ON g.id = mg.genre_id
                WHERE g.id = genre_id
                GROUP BY g.id, g.language
                ON CONFLICT (genre_id, language)
                DO UPDATE SET
                    movie_count = EXCLUDED.movie_count,
                    latest_movie_data = EXCLUDED.latest_movie_data,
                    last_updated = NOW();

                RETURN COALESCE(NEW, OLD);
            END;
            $$ LANGUAGE plpgsql;
            """,
            reverse_sql="""
            DROP FUNCTION IF EXISTS update_genre_summary();
            """
        ),

        # Tạo trigger cho MovieGenre table
        migrations.RunSQL(
            """
            CREATE TRIGGER trigger_update_genre_summary_moviegenre
            AFTER INSERT OR UPDATE OR DELETE ON movies_movie_genres
            FOR EACH ROW
            EXECUTE FUNCTION update_genre_summary();
            """,
            reverse_sql="""
            DROP TRIGGER IF EXISTS trigger_update_genre_summary_moviegenre ON movies_movie_genres;
            """
        ),

        # Tạo trigger cho Movie table (khi poster_url hoặc release_date thay đổi)
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION update_genre_summary_on_movie_change()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Cập nhật summary cho tất cả genres của movie này
                INSERT INTO metadata_genre_summary (genre_id, language, movie_count, latest_movie_data, last_updated)
                SELECT
                    g.id,
                    g.language,
                    COUNT(mg.movie_id) as movie_count,
                    (
                        SELECT json_build_object(
                            'id', m.id,
                            'title', m.title,
                            'poster_url', m.poster_url,
                            'release_date', m.release_date
                        )
                        FROM movies_movie m
                        INNER JOIN movies_movie_genres mg2 ON m.id = mg2.movie_id
                        WHERE mg2.genre_id = g.id
                        AND m.poster_url IS NOT NULL
                        AND m.poster_url != ''
                        ORDER BY m.release_date DESC
                        LIMIT 1
                    ) as latest_movie_data,
                    NOW()
                FROM metadata_genre g
                INNER JOIN movies_movie_genres mg ON g.id = mg.genre_id
                WHERE mg.movie_id = COALESCE(NEW.id, OLD.id)
                GROUP BY g.id, g.language
                ON CONFLICT (genre_id, language)
                DO UPDATE SET
                    movie_count = EXCLUDED.movie_count,
                    latest_movie_data = EXCLUDED.latest_movie_data,
                    last_updated = NOW();

                RETURN COALESCE(NEW, OLD);
            END;
            $$ LANGUAGE plpgsql;
            """,
            reverse_sql="""
            DROP FUNCTION IF EXISTS update_genre_summary_on_movie_change();
            """
        ),

        # Tạo trigger cho Movie table
        migrations.RunSQL(
            """
            CREATE TRIGGER trigger_update_genre_summary_movie
            AFTER UPDATE OF poster_url, release_date ON movies_movie
            FOR EACH ROW
            EXECUTE FUNCTION update_genre_summary_on_movie_change();
            """,
            reverse_sql="""
            DROP TRIGGER IF EXISTS trigger_update_genre_summary_movie ON movies_movie;
            """
        ),

        # Khởi tạo dữ liệu summary ban đầu
        migrations.RunSQL(
            """
            INSERT INTO metadata_genre_summary (genre_id, language, movie_count, latest_movie_data, last_updated)
            SELECT
                g.id,
                g.language,
                COUNT(mg.movie_id) as movie_count,
                (
                    SELECT json_build_object(
                        'id', m.id,
                        'title', m.title,
                        'poster_url', m.poster_url,
                        'release_date', m.release_date
                    )
                    FROM movies_movie m
                    INNER JOIN movies_movie_genres mg2 ON m.id = mg2.movie_id
                    WHERE mg2.genre_id = g.id
                    AND m.poster_url IS NOT NULL
                    AND m.poster_url != ''
                    ORDER BY m.release_date DESC
                    LIMIT 1
                ) as latest_movie_data,
                NOW()
            FROM metadata_genre g
            LEFT JOIN movies_movie_genres mg ON g.id = mg.genre_id
            GROUP BY g.id, g.language
            HAVING COUNT(mg.movie_id) > 0
            ON CONFLICT (genre_id, language)
            DO UPDATE SET
                movie_count = EXCLUDED.movie_count,
                latest_movie_data = EXCLUDED.latest_movie_data,
                last_updated = NOW();
            """,
            reverse_sql=""
        ),
    ]
