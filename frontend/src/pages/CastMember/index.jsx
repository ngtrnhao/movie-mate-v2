import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import {
  ArrowLeft,
  Calendar,
  MapPin,
  Star,
  Film,
  Award,
  User,
  Heart,
  Eye,
  Play,
} from 'lucide-react';
import { getProfileUrl } from '../../utils/imageUtils';
import { useCastMember } from '../../hooks/useCastMember';
import MovieCard from '../../components/movies/cast/MovieCard';

const CastMemberDetail = () => {
  const { castId } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation('movies');
  const { castMember, loading, error } = useCastMember(castId);

  const getGenderText = gender => {
    if (gender === 1) return 'Female';
    if (gender === 2) return 'Male';
    return 'Unknown';
  };

  const getDisplayName = castMember => {
    return castMember?.name || t('details.unknownActor');
  };

  const getDisplayBiography = biography => {
    if (!biography || biography.trim() === '') {
      return t('details.noBiography');
    }
    return biography;
  };

  const getDisplayPlaceOfBirth = placeOfBirth => {
    return placeOfBirth || t('details.unknown');
  };

  const getDisplayProfessions = professions => {
    if (!professions || !Array.isArray(professions) || professions.length === 0) {
      return ['Actor']; // Default profession
    }
    return professions;
  };

  const getDisplayKnownFor = (knownFor, knownForMovies) => {
    if (!knownForMovies || !Array.isArray(knownForMovies) || knownForMovies.length === 0) {
      if (!knownFor || !Array.isArray(knownFor) || knownFor.length === 0) {
        return [t('details.noKnownWorksAvailable')];
      }
      return knownFor;
    }
    return knownForMovies;
  };

  const getDisplayRelatedMovies = relatedMovies => {
    if (!relatedMovies || !Array.isArray(relatedMovies) || relatedMovies.length === 0) {
      return [];
    }
    return relatedMovies;
  };

  const getAge = (birthYear, deathYear) => {
    if (!birthYear) return null;
    const currentYear = new Date().getFullYear();
    const endYear = deathYear || currentYear;
    return endYear - birthYear;
  };

  const getRoleDisplay = role => {
    const roleMap = {
      ACTOR: 'Actor',
      DIRECTOR: 'Director',
      WRITER: 'Writer',
      PRODUCER: 'Producer',
      CINEMATOGRAPHER: 'Cinematographer',
      EDITOR: 'Editor',
      COMPOSER: 'Composer',
    };
    return roleMap[role] || role;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900">
        <div className="container mx-auto px-4 py-8">
          <div className="animate-pulse">
            <div className="mb-8 flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-gray-700"></div>
              <div className="h-8 w-48 rounded bg-gray-700"></div>
            </div>
            <div className="grid gap-8 lg:grid-cols-3">
              <div className="lg:col-span-1">
                <div className="aspect-[2/3] w-full rounded-lg bg-gray-700"></div>
              </div>
              <div className="lg:col-span-2 space-y-4">
                <div className="h-8 w-3/4 rounded bg-gray-700"></div>
                <div className="h-4 w-full rounded bg-gray-700"></div>
                <div className="h-4 w-2/3 rounded bg-gray-700"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-white">
            <h1 className="mb-4 text-2xl font-bold">Error</h1>
            <p className="text-gray-400">{error}</p>
            <button
              onClick={() => navigate(-1)}
              className="mt-4 rounded-lg bg-red-600 px-6 py-2 text-white hover:bg-red-700"
            >
              Go Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!castMember) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="container mx-auto px-4 py-28">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 flex items-center gap-4"
        >
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 rounded-lg bg-gray-800 px-4 py-2 text-white transition-colors hover:bg-gray-700"
          >
            <ArrowLeft size={20} />
            {t('details.back')}
          </button>
          <h1 className="text-2xl font-bold text-white lg:text-3xl">
            {getDisplayName(castMember)}
          </h1>
        </motion.div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Profile Section */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-1"
          >
            <div className="sticky top-8">
              {/* Profile Image */}
              <div className="mb-6 overflow-hidden rounded-lg bg-gray-800 shadow-xl">
                <img
                  src={getProfileUrl(castMember, 'w500')}
                  alt={getDisplayName(castMember)}
                  className="aspect-[2/3] w-full object-cover"
                  onError={e => {
                    e.target.src = '/images/avatar_default.jpg';
                  }}
                />
              </div>

              {/* Basic Info */}
              <div className="space-y-4 rounded-lg bg-gray-800 p-6">
                <div className="flex items-center gap-2">
                  <User size={20} className="text-gray-400" />
                  <span className="text-white">{getRoleDisplay(castMember.role)}</span>
                </div>

                {castMember.birth_year && (
                  <div className="flex items-center gap-2">
                    <Calendar size={20} className="text-gray-400" />
                    <span className="text-white">
                      {castMember.birth_year}
                      {castMember.death_year && ` - ${castMember.death_year}`}
                      {getAge(castMember.birth_year, castMember.death_year) &&
                        ` (${getAge(castMember.birth_year, castMember.death_year)} ${t('details.years')})`}
                    </span>
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <MapPin size={20} className="text-gray-400" />
                  <span className="text-white">
                    {getDisplayPlaceOfBirth(castMember.place_of_birth)}
                  </span>
                </div>

                {castMember.gender && (
                  <div className="flex items-center gap-2">
                    <Heart size={20} className="text-gray-400" />
                    <span className="text-white">{getGenderText(castMember.gender)}</span>
                  </div>
                )}

                {castMember.popularity && (
                  <div className="flex items-center gap-2">
                    <Star size={20} className="text-yellow-400" />
                    <span className="text-white">
                      {t('details.popularity')}: {castMember.popularity.toFixed(1)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </motion.div>

          {/* Content Section */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-2 space-y-8"
          >
            {/* Biography */}
            <div className="rounded-lg bg-gray-800 p-6">
              <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-white">
                <User size={24} />
                {t('details.biography')}
              </h2>
              <p className="leading-relaxed text-gray-300">
                {getDisplayBiography(castMember.biography)}
              </p>
            </div>

            {/* Current Movie */}
            <div className="rounded-lg bg-gray-800 p-6">
              <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-white">
                <Film size={24} />
                {t('details.currentMovie')}
              </h2>
              {castMember.current_movie ? (
                <div className="flex gap-4">
                  <img
                    src={castMember.current_movie.poster_url || 'https://placehold.co/600x400'}
                    alt={castMember.current_movie.title || t('details.unknownMovie')}
                    className="h-32 w-24 rounded-lg object-cover"
                    onError={e => {
                      e.target.src = 'https://placehold.co/600x400';
                    }}
                  />
                  <div className="flex-1">
                    <h3 className="mb-2 text-lg font-semibold text-white">
                      {castMember.current_movie.title || t('details.unknownMovie')}
                    </h3>
                    {castMember.current_movie.release_date && (
                      <p className="text-gray-400">
                        {new Date(castMember.current_movie.release_date).getFullYear()}
                      </p>
                    )}
                    {castMember.main_character && (
                      <p className="mt-2 text-sm text-gray-300">
                        {t('details.as')}{' '}
                        <span className="text-yellow-400">{castMember.main_character}</span>
                      </p>
                    )}
                    <button
                      onClick={() => navigate(`/movies/${castMember.current_movie.id}`)}
                      className="mt-3 flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
                    >
                      <Eye size={16} />
                      {t('details.viewMovie')}
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-gray-400">{t('details.noCurrentMovie')}</p>
              )}
            </div>

            {/* Related Movies */}
            <div className="rounded-lg bg-gray-800 p-6">
              <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-white">
                <Film size={24} />
                {t('details.filmography')}
              </h2>
              {getDisplayRelatedMovies(castMember.related_movies).length > 0 ? (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {getDisplayRelatedMovies(castMember.related_movies).map(movie => (
                    <MovieCard key={movie.id} movie={movie} showCharacter={true} />
                  ))}
                </div>
              ) : (
                <p className="text-gray-400">{t('details.noFilmography')}</p>
              )}
            </div>

            {/* Known For */}
            <div className="rounded-lg bg-gray-800 p-6">
              <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-white">
                <Award size={24} />
                {t('details.knownForMovies')}
              </h2>
              {getDisplayKnownFor(castMember.known_for_titles, castMember.known_for_movies).length >
              0 ? (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {getDisplayKnownFor(castMember.known_for_titles, castMember.known_for_movies)
                    .slice(0, 6)
                    .map((item, index) => (
                      <MovieCard key={item.id || index} movie={item} showCharacter={false} />
                    ))}
                </div>
              ) : (
                <p className="text-gray-400">{t('details.noKnownWorks')}</p>
              )}
            </div>

            {/* Primary Profession */}
            <div className="rounded-lg bg-gray-800 p-6">
              <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-white">
                <Award size={24} />
                {t('details.professions')}
              </h2>
              {getDisplayProfessions(castMember.primary_profession).length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {getDisplayProfessions(castMember.primary_profession).map((profession, index) => (
                    <span
                      key={index}
                      className="rounded-full bg-red-600 px-3 py-1 text-sm text-white"
                    >
                      {profession}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400">{t('details.noProfessions')}</p>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default CastMemberDetail;
