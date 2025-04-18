import { useState, useEffect, useCallback } from 'react';
import MovieMateLogo from '../../components/header/Logo';

const LandingPage = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  const TMDB_BASE_URL = 'https://api.themoviedb.org/3';
  const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/original';

  const options = {
    method: 'GET',
    headers: {
      accept: 'application/json',
      Authorization:
        'BearereyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0YzMzOGUzYTMzNGI4ZjgxN2M0NWNlOGIwY2JhNmRmMSIsIm5iZiI6MTc0MDYwODk5Mi40MTkwMDAxLCJzdWIiOiI2N2JmOTVlMGJjNjkzNWEwMDFhMjM2MTgiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.iOVSJPSuTWhbnD5AAQBCnQ5TYXVLCwVOgPMytmB4rHs',
    },
  };
  const fetchMovies = useCallback(async () => {
    try {
      const [enResponse, viResponse] = await Promise.all([
        fetch(`${TMDB_BASE_URL}/trending/movie/week?language=en-US`, options),
        fetch(`${TMDB_BASE_URL}/trending/movie/week?language=vi-VN`, options),
      ]);
      if (!enResponse.ok || !viResponse.ok) {
        throw new Error('Failed to fetch movies');
      }
      const [enData, viData] = await Promise.all([enResponse.json(), viResponse.json()]);

      const movieWithDetails = await Promise.all(
        enData.results.slice(0, 3).map(async (enMovie, index) => {
          const viMovie = viData.results[index];

          const [enDetails, viDetails] = await Promise.all([
            fetch(
              `${TMDB_BASE_URL}/movie/${enMovie.id}?language=en-US&append_to_response=videos`,
              options
            ).then((res) => res.json()),
            fetch(
              `${TMDB_BASE_URL}/movie/${viMovie.id}?language=vi-VN&append_to_response=videos`,
              options
            ).then((res) => res.json()),
          ]);
          return {
            id: enMovie.id,
            titile: {
              en: enDetails.title,
              vi: viDetails.title,
            },
            year: new Date(enMovie.release_date).getFullYear(),
            rating: enMovie.vote_average.toFixed(1),
            description: {
              en: enMovie.overview,
              vi: viMovie.overview,
            },
            imageUrl: `${TMDB_IMAGE_BASE_URL}${enMovie.backdrop_path}`,
            trailerUrl: enDetails.videos?.results?.[0]?.key
              ? `https://www.youtube.com/watch?v=${enDetails.videos.results[0].key}`
              : null,
          };
        })
      );
      return movieWithDetails;
    } catch (error) {
      console.error('Error fetching movies:', error);
      return [];
    }
  });
  const toggleLangeuage = () => {
    setLanguage((prev) => (prev === 'en-US' ? 'vi-VN' : 'en-US'));
  };
  useEffect(() => {
    fetchMovies();
  }, [fetchMovies]);

  return (
    <div className="bg-background relative min-h-screen">
      <header className="absolute inset-0 z-10">
        <div className="mx-auto max-w-[1400px] px-4">
          <div className="flex h-20 items-center justify-between">
            <MovieMateLogo />
          </div>
        </div>
      </header>
    </div>
  );
};

export default LandingPage;
