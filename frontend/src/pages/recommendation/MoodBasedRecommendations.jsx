import { useState } from 'react';
import { mockMovies } from '../../mocks/movies';
import { useNavigate } from 'react-router-dom';

const moods = [
  {
    id: 'uplifting',
    name: 'Uplifting',
    icon: '🌟',
    description: 'Feel-good movies to brighten your day',
  },
  {
    id: 'intense',
    name: 'Intense',
    icon: '🔥',
    description: 'Gripping, edge-of-your-seat experiences',
  },
  {
    id: 'thoughtful',
    name: 'Thoughtful',
    icon: '🤔',
    description: 'Thought-provoking films that make you reflect',
  },
  {
    id: 'relaxing',
    name: 'Relaxing',
    icon: '😌',
    description: 'Calm, easy-watching for when you need to unwind',
  },
  {
    id: 'adventurous',
    name: 'Adventurous',
    icon: '🌍',
    description: 'Exciting journeys and explorations',
  },
  {
    id: 'romantic',
    name: 'Romantic',
    icon: '❤️',
    description: 'Love stories and heartwarming connections',
  },
];

const moodToGenres = {
  uplifting: ['Comedy', 'Animation', 'Fantasy'],
  intense: ['Thriller', 'Horror', 'Crime'],
  thoughtful: ['Drama', 'Documentary'],
  relaxing: ['Comedy', 'Romance'],
  adventurous: ['Adventure', 'Action', 'Sci-Fi'],
  romantic: ['Romance', 'Drama'],
};

const MoodBasedRecommendations = () => {
  const [selectedMood, setSelectedMood] = useState('uplifting');
  const navigate = useNavigate();

  const getMoodRecommendations = (mood) => {
    const genres = moodToGenres[mood] || [];
    return mockMovies
      .filter((movie) => movie.genres.some((genre) => genres.includes(genre)))
      .sort(() => Math.random() - 0.5)
      .slice(0, 6);
  };

  const selectedMoodObj = moods.find((m) => m.id === selectedMood);

  return (
    <section className="w-full py-8 md:col-span-2">
      <div className="rounded-lg border border-gray-800 bg-gray-900 p-6 shadow-lg">
        <h2 className="mb-1 flex items-center gap-2 text-2xl font-semibold text-white">
          <span className="text-3xl text-yellow-500">{selectedMoodObj.icon}</span>
          Mood Based Recommendations
        </h2>
        <p className="mb-6 text-sm text-gray-400">
          Discover movies that match your current mood and emotional state.
        </p>

        {/* Mood Selector */}
        <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-6">
          {moods.map((mood) => (
            <button
              key={mood.id}
              onClick={() => setSelectedMood(mood.id)}
              className={`flex flex-col items-center rounded-lg border p-4 transition-all ${
                selectedMood === mood.id
                  ? 'border-yellow-500 bg-yellow-500/10'
                  : 'border-gray-700 bg-gray-800 hover:border-yellow-500/50'
              }`}
            >
              <span className="mb-2 text-3xl">{mood.icon}</span>
              <span className="text-sm text-white">{mood.name}</span>
            </button>
          ))}
        </div>

        {/* Mood Description */}
        <div className="mb-4 text-center">
          <p className="text-gray-400">{selectedMoodObj.description}</p>
        </div>

        {/* Movie Recommendations */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-3">
          {getMoodRecommendations(selectedMood).map((movie) => (
            <div
              key={movie.id}
              className="group cursor-pointer overflow-hidden rounded-lg bg-gray-800"
            >
              <img
                src={movie.poster_path}
                alt={movie.title}
                className="aspect-[2/3] w-full object-cover transition-transform duration-300 group-hover:scale-105"
              />
              <div className="p-2">
                <h4 className="text-sm font-medium text-white">{movie.title}</h4>
                <div className="mt-1 flex items-center gap-2">
                  <span className="text-xs text-yellow-500">★ {movie.vote_average}</span>
                  <span className="text-xs text-gray-400">
                    {new Date(movie.release_date).getFullYear()}
                  </span>
                </div>
                <div className="mt-1 flex flex-wrap gap-1">
                  {movie.genres.map((genre) => (
                    <span
                      key={genre}
                      className="rounded bg-gray-700 px-2 py-0.5 text-xs text-gray-300"
                    >
                      {genre}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-center">
          <button
            onClick={() => navigate('/recommendation')}
            className="rounded border border-gray-300 bg-yellow-600 px-6 py-2 font-semibold text-white transition hover:bg-yellow-700"
          >
            View More {selectedMoodObj.name} Movies
          </button>
        </div>
      </div>
    </section>
  );
};

export default MoodBasedRecommendations;
