from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0010_fix_genre_summary_ambiguous_column'),
    ]

    operations = [
        # Sửa trigger để đảm bảo movie_count được tính đúng
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION update_genre_summary()
            RETURNS TRIGGER AS $$
            DECLARE
                target_genre_id INTEGER;
                current_count INTEGER;
                latest_movie_json JSON;
            BEGIN
                -- Xác định genre_id dựa trên operation
                IF TG_OP = 'DELETE' THEN
                    target_genre_id := OLD.genre_id;
                ELSE
                    target_genre_id := NEW.genre_id;
                END IF;

                -- Tính movie count trực tiếp
                SELECT COUNT(*) INTO current_count
                FROM movies_movie_genres
                WHERE genre_id = target_genre_id;

                -- Tìm latest movie có poster
                SELECT json_build_object(
                    'id', m.id,
                    'title', m.title,
                    'poster_url', m.poster_url,
                    'release_date', m.release_date
                ) INTO latest_movie_json
                FROM movies_movie m
                INNER JOIN movies_movie_genres mg ON m.id = mg.movie_id
                WHERE mg.genre_id = target_genre_id
                AND m.poster_url IS NOT NULL
                AND m.poster_url != ''
                ORDER BY COALESCE(m.release_date, '1900-01-01'::date) DESC, m.id DESC
                LIMIT 1;

                -- Update hoặc insert summary
                INSERT INTO metadata_genre_summary (genre_id, language, movie_count, latest_movie_data, last_updated)
                SELECT
                    target_genre_id,
                    g.language,
                    current_count,
                    latest_movie_json,
                    NOW()
                FROM metadata_genre g
                WHERE g.id = target_genre_id
                ON CONFLICT (genre_id, language)
                DO UPDATE SET
                    movie_count = current_count,
                    latest_movie_data = latest_movie_json,
                    last_updated = NOW();

                RETURN COALESCE(NEW, OLD);
            END;
            $$ LANGUAGE plpgsql;
            """,
            reverse_sql="""
            -- Revert to previous version
            CREATE OR REPLACE FUNCTION update_genre_summary()
            RETURNS TRIGGER AS $$
            DECLARE
                target_genre_id INTEGER;
            BEGIN
                -- Xác định genre_id dựa trên operation
                IF TG_OP = 'DELETE' THEN
                    target_genre_id := OLD.genre_id;
                ELSE
                    target_genre_id := NEW.genre_id;
                END IF;

                -- Cập nhật summary cho genre với logic đơn giản hơn
                INSERT INTO metadata_genre_summary (genre_id, language, movie_count, latest_movie_data, last_updated)
                SELECT
                    g.id,
                    g.language,
                    COUNT(mg.movie_id) as movie_count,
                    (
                        -- Chọn movie mới nhất có poster
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
                WHERE g.id = target_genre_id
                GROUP BY g.id, g.language
                ON CONFLICT (genre_id, language)
                DO UPDATE SET
                    movie_count = EXCLUDED.movie_count,
                    latest_movie_data = EXCLUDED.latest_movie_data,
                    last_updated = NOW();

                RETURN COALESCE(NEW, OLD);
            END;
            $$ LANGUAGE plpgsql;
            """
        ),

        # Refresh tất cả data sau khi fix function
        migrations.RunSQL(
            """
            -- Refresh all genre summaries with correct counts
            INSERT INTO metadata_genre_summary (genre_id, language, movie_count, latest_movie_data, last_updated)
            SELECT
                g.id,
                g.language,
                (SELECT COUNT(*) FROM movies_movie_genres mg WHERE mg.genre_id = g.id) as movie_count,
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
                    ORDER BY COALESCE(m.release_date, '1900-01-01'::date) DESC, m.id DESC
                    LIMIT 1
                ) as latest_movie_data,
                NOW()
            FROM metadata_genre g
            WHERE EXISTS (SELECT 1 FROM movies_movie_genres mg WHERE mg.genre_id = g.id)
            ON CONFLICT (genre_id, language)
            DO UPDATE SET
                movie_count = EXCLUDED.movie_count,
                latest_movie_data = EXCLUDED.latest_movie_data,
                last_updated = NOW();
            """,
            reverse_sql=""
        ),
    ]