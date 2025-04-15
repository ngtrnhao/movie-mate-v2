
CREATE DATABASE movie_recommendation_db
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    CONNECTION LIMIT = -1;


CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Bảng Genre (Thể loại phim)
CREATE TABLE metadata_genre (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT genre_name_slug_unique UNIQUE (name, slug)
);

CREATE INDEX idx_genre_name_trgm ON metadata_genre USING gin (name gin_trgm_ops);

-- Bảng Person (Diễn viên/Đạo diễn)
CREATE TABLE metadata_person (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    biography TEXT,
    date_of_birth DATE,
    date_of_death DATE,
    place_of_birth VARCHAR(255),
    photo_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_person_name_trgm ON metadata_person USING gin (name gin_trgm_ops);

-- Bảng Movie (Phim)
CREATE TABLE movies_movie (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    original_title VARCHAR(255),
    overview TEXT,
    release_date DATE,
    poster_url VARCHAR(255),
    backdrop_url VARCHAR(255),
    imdb_rating DECIMAL(3,1),
    tmdb_id VARCHAR(20) UNIQUE,
    runtime INTEGER,
    status VARCHAR(50) CHECK (status IN ('RUMORED', 'PLANNED', 'IN_PRODUCTION', 'POST_PRODUCTION', 'RELEASED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_movie_title_trgm ON movies_movie USING gin (title gin_trgm_ops);
CREATE INDEX idx_movie_release_date ON movies_movie (release_date);
CREATE INDEX idx_movie_imdb_rating ON movies_movie (imdb_rating);
CREATE INDEX idx_movie_tmdb_id ON movies_movie (tmdb_id);
CREATE INDEX idx_movie_status ON movies_movie (status);

-- Bảng Movie Metadata
CREATE TABLE movies_moviemetadata (
    id BIGSERIAL PRIMARY KEY,
    movie_id BIGINT NOT NULL REFERENCES movies_movie(id) ON DELETE CASCADE,
    budget BIGINT,
    revenue BIGINT,
    tagline TEXT,
    homepage VARCHAR(255),
    keywords JSONB,
    production_companies JSONB,
    production_countries JSONB,
    spoken_languages JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_movie_metadata UNIQUE (movie_id)
);

-- Bảng liên kết Movie-Genre
CREATE TABLE movies_movie_genres (
    id BIGSERIAL PRIMARY KEY,
    movie_id BIGINT NOT NULL REFERENCES movies_movie(id) ON DELETE CASCADE,
    genre_id BIGINT NOT NULL REFERENCES metadata_genre(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_movie_genre UNIQUE (movie_id, genre_id)
);

-- Bảng MovieCrew (Đội ngũ làm phim)
CREATE TABLE metadata_moviecrew (
    id BIGSERIAL PRIMARY KEY,
    movie_id BIGINT NOT NULL REFERENCES movies_movie(id) ON DELETE CASCADE,
    person_id BIGINT NOT NULL REFERENCES metadata_person(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('ACTOR', 'DIRECTOR', 'WRITER', 'PRODUCER')),
    character_name VARCHAR(255),
    order_credit INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_movie_person_role UNIQUE (movie_id, person_id, role)
);

CREATE INDEX idx_movie_role ON metadata_moviecrew (movie_id, role);

-- Bảng Movie Trailer
CREATE TABLE movies_trailer (
    id BIGSERIAL PRIMARY KEY,
    movie_id BIGINT NOT NULL REFERENCES movies_movie(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    youtube_key VARCHAR(50) NOT NULL,
    type VARCHAR(20) CHECK (type IN ('TRAILER', 'TEASER', 'CLIP')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trailer_movie ON movies_trailer (movie_id);

-- Bảng Movie Image
CREATE TABLE movies_movieimage (
    id BIGSERIAL PRIMARY KEY,
    movie_id BIGINT NOT NULL REFERENCES movies_movie(id) ON DELETE CASCADE,
    image_url VARCHAR(255) NOT NULL,
    type VARCHAR(20) CHECK (type IN ('POSTER', 'BACKDROP', 'SCREENSHOT')),
    width INTEGER,
    height INTEGER,
    aspect_ratio DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_image_movie ON movies_movieimage (movie_id);

-- Bảng Users (Người dùng)
CREATE TABLE users_users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(254) UNIQUE,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(30),
    last_name VARCHAR(150),
    avatar_url VARCHAR(255),
    bio TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    date_joined TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    age INTEGER,
    gender VARCHAR(10) CHECK (gender IN ('M', 'F', 'O')),
    location VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_username_trgm ON users_users USING gin (username gin_trgm_ops);
CREATE INDEX idx_user_email ON users_users (email);

-- Bảng liên kết Users-Genre (Thể loại yêu thích)
CREATE TABLE users_users_favorite_genres (
    id BIGSERIAL PRIMARY KEY,
    users_id BIGINT NOT NULL REFERENCES users_users(id) ON DELETE CASCADE,
    genre_id BIGINT NOT NULL REFERENCES metadata_genre(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_genre UNIQUE (users_id, genre_id)
);

-- Bảng Rating (Đánh giá)
CREATE TABLE users_rating (
    id BIGSERIAL PRIMARY KEY,
    users_id BIGINT NOT NULL REFERENCES users_users(id) ON DELETE CASCADE,
    movie_id BIGINT NOT NULL REFERENCES movies_movie(id) ON DELETE CASCADE,
    rating DECIMAL(3,1) NOT NULL CHECK (rating >= 0 AND rating <= 10),
    review_title VARCHAR(255),
    review_text TEXT,
    likes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_movie_rating UNIQUE (users_id, movie_id)
);

CREATE INDEX idx_rating_user ON users_rating (users_id);
CREATE INDEX idx_rating_movie ON users_rating (movie_id);
CREATE INDEX idx_rating_created ON users_rating (created_at);

-- Bảng Comment (Bình luận)
CREATE TABLE users_comment (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users_users(id) ON DELETE CASCADE,
    movie_id BIGINT NOT NULL REFERENCES movies_movie(id) ON DELETE CASCADE,
    parent_id BIGINT REFERENCES users_comment(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    likes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comment_movie ON users_comment (movie_id);
CREATE INDEX idx_comment_user ON users_comment (user_id);
CREATE INDEX idx_comment_parent ON users_comment (parent_id);

-- Bảng Comment Like
CREATE TABLE users_commentlike (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users_users(id) ON DELETE CASCADE,
    comment_id BIGINT NOT NULL REFERENCES users_comment(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_comment_like UNIQUE (user_id, comment_id)
);

-- Bảng Watchlist
CREATE TABLE users_watchlist (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users_users(id) ON DELETE CASCADE,
    movie_id BIGINT NOT NULL REFERENCES movies_movie(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PLANNED', 'WATCHING', 'WATCHED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_movie_watchlist UNIQUE (user_id, movie_id)
);

CREATE INDEX idx_watchlist_user ON users_watchlist (user_id);
CREATE INDEX idx_watchlist_status ON users_watchlist (status);

-- Bảng Search History
CREATE TABLE users_searchhistory (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users_users(id) ON DELETE CASCADE,
    search_query VARCHAR(255) NOT NULL,
    search_results_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_search_history ON users_searchhistory (user_id, created_at);

-- Bảng User Activity Log
CREATE TABLE users_useractivitylog (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users_users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    activity_data JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_activity ON users_useractivitylog (user_id, activity_type);
CREATE INDEX idx_activity_time ON users_useractivitylog (created_at);

-- Bảng Movie News
CREATE TABLE movies_movienews (
    id BIGSERIAL PRIMARY KEY,
    movie_id BIGINT NOT NULL REFERENCES movies_movie(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source_url VARCHAR(255),
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_news_movie ON movies_movienews (movie_id);
CREATE INDEX idx_news_published ON movies_movienews (published_at);

-- Materialized View cho thống kê phim
CREATE MATERIALIZED VIEW movie_statistics AS
SELECT 
    m.id as movie_id,
    COUNT(DISTINCT r.id) as total_ratings,
    AVG(r.rating) as average_rating,
    COUNT(DISTINCT c.id) as total_comments,
    COUNT(DISTINCT w.id) as total_watchlist,
    COUNT(DISTINCT CASE WHEN r.rating >= 8 THEN r.id END) as positive_ratings,
    COUNT(DISTINCT CASE WHEN r.rating <= 4 THEN r.id END) as negative_ratings
FROM movies_movie m
LEFT JOIN users_rating r ON m.id = r.movie_id
LEFT JOIN users_comment c ON m.id = c.movie_id
LEFT JOIN users_watchlist w ON m.id = w.movie_id
GROUP BY m.id;

CREATE UNIQUE INDEX idx_movie_statistics ON movie_statistics (movie_id);

-- Function để refresh materialized view
CREATE OR REPLACE FUNCTION refresh_movie_statistics()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY movie_statistics;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger để tự động refresh materialized view
CREATE TRIGGER refresh_movie_statistics_trigger
AFTER INSERT OR UPDATE OR DELETE ON users_rating
    OR INSERT OR UPDATE OR DELETE ON users_comment
    OR INSERT OR UPDATE OR DELETE ON users_watchlist
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_movie_statistics();