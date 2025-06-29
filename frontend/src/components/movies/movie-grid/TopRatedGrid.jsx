import { useState } from 'react';
import { useTranslation } from 'react-i18next';

// Mock movies reused from movie-carousel
const mockMovies = [
  {
    id: 1,
    title: 'The Shawshank Redemption',
    poster_path: 'https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg',
    vote_average: 9.3,
    year: 1994,
    runtime: 142,
    overview:
      'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.',
  },
  {
    id: 3,
    title: 'The Dark Knight',
    poster_path: 'https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
    vote_average: 9.0,
    year: 2008,
    runtime: 152,
    overview: 'Batman raises the stakes in his war on crime.',
  },
  {
    id: 4,
    title: 'Pulp Fiction',
    poster_path: 'https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg',
    vote_average: 8.9,
    year: 1994,
    runtime: 154,
    overview:
      'The lives of two mob hitmen, a boxer, and others intertwine in four tales of violence and redemption.',
  },
  {
    id: 11,
    title: 'The Lord of the Rings: The Return of the King',
    poster_path: 'https://image.tmdb.org/t/p/w500/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg',
    vote_average: 8.9,
    year: 2003,
    runtime: 201,
    overview: 'Gandalf and Aragorn lead the World of Men against Sauron.',
  },
  {
    id: 6,
    title: 'Inception',
    poster_path: 'https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
    vote_average: 8.8,
    year: 2010,
    runtime: 148,
    overview: 'A thief who steals corporate secrets through dream-sharing technology.',
  },
];

const TABS = [
  { value: 'all', label: 'All Time' },
  { value: 'week', label: 'This Week' },
  { value: 'month', label: 'This Month' },
];

export default function TopRatedGrid() {
  const { t } = useTranslation('movies');
  const [activeTab, setActiveTab] = useState('all');
  const topRatedMovies = [...mockMovies]
    .sort((a, b) => b.vote_average - a.vote_average)
    .slice(0, 5);

  return (
    <section className="w-full pb-6">
      <div className="ml-14">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">Top Rated</h2>
            <p className="text-sm text-gray-400">Highest rated movies by our users</p>
          </div>
        </div>
        <div className="mb-6 flex justify-end">
          <div className="inline-flex rounded-md bg-gray-800 p-1">
            {TABS.map(tab => (
              <button
                key={tab.value}
                className={`rounded-md px-4 py-1 text-sm font-medium transition-colors duration-150 ${activeTab === tab.value ? 'bg-white text-gray-900' : 'text-gray-300 hover:bg-gray-700'}`}
                onClick={() => setActiveTab(tab.value)}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
        {activeTab === 'all' && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {topRatedMovies.map((movie, index) => (
              <div
                key={movie.id}
                className={index === 0 ? 'md:col-span-2 lg:col-span-1 lg:row-span-2' : ''}
              >
                <div
                  className={`group relative overflow-hidden rounded-xl ${index === 0 ? 'aspect-[2/3] min-h-[400px]' : 'aspect-video min-h-[180px]'}`}
                >
                  <a href={'/movies/' + movie.id} className="block">
                    <img
                      src={movie.poster_path}
                      alt={movie.title}
                      className="absolute inset-0 size-full object-cover transition-transform duration-300 group-hover:scale-105"
                      style={{ position: 'absolute' }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
                  </a>
                  <div className="absolute inset-x-0 bottom-0 p-4">
                    <div className="mb-1 flex items-center gap-2">
                      <div className="flex items-center rounded-md bg-yellow-500/90 px-2 py-1 text-xs font-bold text-black">
                        <svg className="mr-1 size-3" fill="black" viewBox="0 0 24 24">
                          <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                        </svg>
                        {movie.vote_average.toFixed(1)}
                      </div>
                      <div className="rounded-md bg-red-600/90 px-2 py-1 text-xs font-bold text-white">
                        #{index + 1}
                      </div>
                    </div>
                    <a href={'/movies/' + movie.id} className="block">
                      <h3 className="line-clamp-2 text-lg font-bold text-white">{movie.title}</h3>
                    </a>
                    <div className="mt-1 flex items-center gap-2 text-xs text-white/80">
                      <span>{movie.year}</span>
                      <span>•</span>
                      <span>{movie.runtime} min</span>
                    </div>
                    {index === 0 && (
                      <>
                        <p className="mt-2 line-clamp-3 text-sm text-white/70">{movie.overview}</p>
                        <button className="mt-3 flex items-center gap-1 rounded bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow transition hover:bg-red-700">
                          <svg
                            className="size-4"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M5 3v18l15-9-15-9z"
                            />
                          </svg>
                          <span>{t('details.watchTrailer')}</span>
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        {activeTab !== 'all' && (
          <div className="flex min-h-[200px] items-center justify-center rounded-lg border border-dashed border-gray-600 p-8 text-center">
            <div>
              <p className="text-lg font-medium text-white">{t('details.comingSoon')}</p>
              <p className="text-sm text-gray-400">
                {activeTab === 'week' ? t('details.weeklyRatings') : t('details.monthlyRatings')}
              </p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
