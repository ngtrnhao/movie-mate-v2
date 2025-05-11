import { useQuery } from '@tanstack/react-query';

const TMDB_BASE_URL = 'https://api.themoviedb.org/3';
const options = {
  method: 'GET',
  headers: {
    accept: 'application/json',
    Authorization:
      'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0YzMzOGUzYTMzNGI4ZjgxN2M0NWNlOGIwY2JhNmRmMSIsIm5iZiI6MTc0MDYwODk5Mi40MTkwMDAxLCJzdWIiOiI2N2JmOTVlMGJjNjkzNWEwMDFhMjM2MTgiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.iOVSJPSuTWhbnD5AAQBCnQ5TYXVLCwVOgPMytmB4rHs',
  },
};

const fetchCategories = async () => {
  const res = await fetch(`${TMDB_BASE_URL}/genre/movie/list?language=en-US`, options);
  if (!res.ok) throw new Error('Failed to fetch categories');
  const data = await res.json();
  // data.genres: [{id, name}]
  // Lấy số lượng phim cho từng thể loại (có thể cần API khác, tạm để count = 0)
  return data.genres.map((genre) => ({ ...genre, count: 0 }));
};

export const useCategories = () => {
  return useQuery({
    queryKey: ['categories'],
    queryFn: fetchCategories,
    staleTime: 5 * 60 * 1000,
  });
};
