import { useState, useCallback, useEffect } from 'react';
import {
  enrichMovie,
  batchEnrichMovies,
  getMovieEnrichmentStatus,
  enrichMoviesWithQualityIssues,
} from '../../../api/adminMovieService';

const MovieEnrichmentPanel = () => {
  // State management
  const [selectedMovieId, setSelectedMovieId] = useState('');
  const [batchMovieIds, setBatchMovieIds] = useState('');
  const [enrichmentResults, setEnrichmentResults] = useState(null);
  const [enrichmentStatus, setEnrichmentStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [batchLoading, setBatchLoading] = useState(false);
  const [qualityLoading, setQualityLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Configuration state
  const [forceRefresh, setForceRefresh] = useState(false);
  const [selectedFocusAreas, setSelectedFocusAreas] = useState([]);
  const [enrichmentType, setEnrichmentType] = useState('comprehensive');
  const [maxConcurrent, setMaxConcurrent] = useState(5);
  const [qualityOptions, setQualityOptions] = useState({
    qualityScoreMax: 7.0,
    hasQualityIssues: true,
    limit: 50,
  });

  // Dialog state
  const [statusDialogOpen, setStatusDialogOpen] = useState(false);

  // Focus areas options
  const focusAreaOptions = [
    { value: 'basic', label: '📝 Basic Info (Titles, Overviews)', color: 'blue' },
    { value: 'visual', label: '🖼️ Visual Assets (Posters, Backdrops)', color: 'purple' },
    { value: 'metadata', label: '🎭 Metadata (Cast, Genres, Trailers)', color: 'green' },
    { value: 'ratings', label: '⭐ Ratings (TMDB, IMDB)', color: 'yellow' },
  ];

  // Clear messages after delay
  useEffect(() => {
    if (success || error) {
      const timer = setTimeout(() => {
        setSuccess(null);
        setError(null);
      }, 10000);
      return () => clearTimeout(timer);
    }
  }, [success, error]);

  // Helper functions
  const showSuccess = message => {
    setSuccess(message);
    setError(null);
  };

  const showError = message => {
    setError(message);
    setSuccess(null);
  };

  const resetResults = () => {
    setEnrichmentResults(null);
    setEnrichmentStatus(null);
    setError(null);
    setSuccess(null);
  };

  // === INDIVIDUAL MOVIE ENRICHMENT ===
  const handleEnrichSingleMovie = useCallback(async () => {
    if (!selectedMovieId) {
      showError('Please enter a movie ID');
      return;
    }

    setLoading(true);
    resetResults();

    try {
      const result = await enrichMovie(parseInt(selectedMovieId), {
        forceRefresh,
        focusAreas: selectedFocusAreas.length > 0 ? selectedFocusAreas : null,
        enrichType: enrichmentType,
      });

      setEnrichmentResults(result);
      showSuccess(`Movie ${selectedMovieId} enriched successfully!`);

      // Auto-refresh status if movie exists
      setTimeout(() => {
        handleGetEnrichmentStatus();
      }, 1000);
    } catch (error) {
      console.error('Error enriching movie:', error);
      showError(error.error || 'Failed to enrich movie');
    } finally {
      setLoading(false);
    }
  }, [selectedMovieId, forceRefresh, selectedFocusAreas, enrichmentType]);

  // === BATCH MOVIE ENRICHMENT ===
  const handleBatchEnrichMovies = useCallback(async () => {
    if (!batchMovieIds.trim()) {
      showError('Please enter movie IDs separated by commas');
      return;
    }

    // Parse movie IDs
    const movieIdArray = batchMovieIds
      .split(',')
      .map(id => parseInt(id.trim()))
      .filter(id => !isNaN(id));

    if (movieIdArray.length === 0) {
      showError('Please enter valid movie IDs');
      return;
    }

    if (movieIdArray.length > 100) {
      showError('Maximum 100 movies per batch');
      return;
    }

    setBatchLoading(true);
    resetResults();

    try {
      const result = await batchEnrichMovies(movieIdArray, {
        focusAreas: selectedFocusAreas.length > 0 ? selectedFocusAreas : null,
        maxConcurrent,
      });

      setEnrichmentResults(result);
      showSuccess(
        `Batch enrichment completed! ${result.batch_result?.processed_successfully || 0} movies processed successfully.`
      );
    } catch (error) {
      console.error('Error in batch enrichment:', error);
      showError(error.error || 'Failed to batch enrich movies');
    } finally {
      setBatchLoading(false);
    }
  }, [batchMovieIds, selectedFocusAreas, maxConcurrent]);

  // === QUALITY-BASED ENRICHMENT ===
  const handleEnrichQualityIssues = useCallback(async () => {
    setQualityLoading(true);
    resetResults();

    try {
      const result = await enrichMoviesWithQualityIssues(qualityOptions);

      setEnrichmentResults(result);
      showSuccess(`Quality-based enrichment completed! ${result.successful || 0} movies improved.`);
    } catch (error) {
      console.error('Error in quality-based enrichment:', error);
      showError(error.error || 'Failed to enrich movies with quality issues');
    } finally {
      setQualityLoading(false);
    }
  }, [qualityOptions]);

  // === ENRICHMENT STATUS ===
  const handleGetEnrichmentStatus = useCallback(async () => {
    if (!selectedMovieId) {
      showError('Please enter a movie ID');
      return;
    }

    setLoading(true);

    try {
      const status = await getMovieEnrichmentStatus(parseInt(selectedMovieId));
      setEnrichmentStatus(status);
      setStatusDialogOpen(true);
    } catch (error) {
      console.error('Error getting enrichment status:', error);
      showError(error.error || 'Failed to get enrichment status');
    } finally {
      setLoading(false);
    }
  }, [selectedMovieId]);

  // === RENDER RESULTS ===
  const renderEnrichmentResults = () => {
    if (!enrichmentResults) return null;

    const isSuccess = enrichmentResults.success;
    const result =
      enrichmentResults.enrichment_result || enrichmentResults.batch_result || enrichmentResults;

    return (
      <div className="mt-6 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-lg">
        <div className="border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4">
          <h3 className="flex items-center text-lg font-semibold text-gray-900">
            {isSuccess ? (
              <>
                <div className="mr-2 flex size-5 items-center justify-center rounded-full bg-green-500">
                  <svg className="size-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                Enrichment Results
              </>
            ) : (
              <>
                <div className="mr-2 flex size-5 items-center justify-center rounded-full bg-red-500">
                  <svg className="size-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                Enrichment Failed
              </>
            )}
          </h3>
        </div>

        <div className="p-6">
          {/* Single Movie Results */}
          {enrichmentResults.enrichment_result && (
            <div className="space-y-4">
              <div className="text-sm text-gray-600">
                Movie: <span className="font-medium">{enrichmentResults.movie_title}</span> (ID:{' '}
                {enrichmentResults.movie_id})
              </div>

              {result.quality_before && result.quality_after && (
                <div className="rounded-lg bg-gray-50 p-4">
                  <h4 className="mb-3 text-sm font-medium text-gray-900">Quality Improvement:</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="inline-flex items-center rounded-full bg-yellow-100 px-3 py-1 text-sm font-medium text-yellow-800">
                        Before: {result.quality_before.quality_score || 0}/10
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800">
                        After: {result.quality_after.quality_score || 0}/10
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {result.improvements && result.improvements.length > 0 && (
                <div className="rounded-lg bg-blue-50 p-4">
                  <h4 className="mb-3 text-sm font-medium text-gray-900">Improvements Made:</h4>
                  <div className="flex flex-wrap gap-2">
                    {result.improvements.map((improvement, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800"
                      >
                        {improvement}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="text-sm text-gray-500">
                Processing time: {result.processing_time || 0}s
              </div>
            </div>
          )}

          {/* Batch Results */}
          {enrichmentResults.batch_result && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{result.total_movies || 0}</div>
                  <div className="text-sm text-gray-600">Total Movies</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {result.processed_successfully || 0}
                  </div>
                  <div className="text-sm text-gray-600">Successful</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">{result.errors || 0}</div>
                  <div className="text-sm text-gray-600">Errors</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-indigo-600">
                    {result.success_rate || 0}%
                  </div>
                  <div className="text-sm text-gray-600">Success Rate</div>
                </div>
              </div>

              <div className="text-sm text-gray-500">
                Processing time: {result.processing_time || 0}s
              </div>
            </div>
          )}

          {/* Quality-based Results */}
          {enrichmentResults.processed !== undefined && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {enrichmentResults.processed || 0}
                  </div>
                  <div className="text-sm text-gray-600">Movies Processed</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {enrichmentResults.successful || 0}
                  </div>
                  <div className="text-sm text-gray-600">Successfully Enriched</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {enrichmentResults.failed || 0}
                  </div>
                  <div className="text-sm text-gray-600">Failed</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  // === RENDER ENRICHMENT STATUS DIALOG ===
  const renderStatusDialog = () => (
    <>
      {statusDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-xl bg-white shadow-2xl">
            <div className="border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4">
              <h2 className="text-xl font-semibold text-gray-900">
                📊 Movie Enrichment Status
                {enrichmentStatus?.movie_id && ` - ID: ${enrichmentStatus.movie_id}`}
              </h2>
            </div>

            <div className="p-6">
              {enrichmentStatus && (
                <div className="space-y-6">
                  <h3 className="text-lg font-medium text-gray-900">
                    {enrichmentStatus.movie_title}
                  </h3>

                  {/* Data Completeness */}
                  <div>
                    <h4 className="text-md mb-3 font-medium text-gray-900">📊 Data Completeness</h4>
                    <div className="space-y-3">
                      {Object.entries(
                        enrichmentStatus.enrichment_status?.data_completeness || {}
                      ).map(([category, data]) => (
                        <div key={category} className="rounded-lg bg-gray-50 p-4">
                          <h5 className="mb-2 text-sm font-medium text-gray-900">
                            {category.replace('_', ' ').toUpperCase()}
                          </h5>
                          <div className="grid grid-cols-2 gap-2">
                            {Object.entries(data).map(([field, value]) => (
                              <div key={field} className="flex items-center">
                                {value ? (
                                  <svg
                                    className="mr-2 size-4 text-green-500"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                  >
                                    <path
                                      fillRule="evenodd"
                                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                      clipRule="evenodd"
                                    />
                                  </svg>
                                ) : (
                                  <svg
                                    className="mr-2 size-4 text-red-500"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                  >
                                    <path
                                      fillRule="evenodd"
                                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                      clipRule="evenodd"
                                    />
                                  </svg>
                                )}
                                <span className="text-sm text-gray-700">
                                  {field.replace('_', ' ')}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Enrichment Opportunities */}
                  {enrichmentStatus.enrichment_status?.enrichment_opportunities?.length > 0 && (
                    <div className="rounded-lg bg-blue-50 p-4">
                      <h4 className="text-md mb-3 font-medium text-gray-900">
                        💡 Enrichment Opportunities
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {enrichmentStatus.enrichment_status.enrichment_opportunities.map(
                          (opportunity, index) => (
                            <span
                              key={index}
                              className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"
                            >
                              {opportunity}
                            </span>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  {/* Quality Metrics */}
                  {enrichmentStatus.enrichment_status?.quality_metrics && (
                    <div className="rounded-lg bg-green-50 p-4">
                      <h4 className="text-md mb-3 font-medium text-gray-700">📈 Quality Metrics</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-sm">
                          <span className="font-medium text-gray-700">Quality Score:</span>{' '}
                          <span className="font-medium text-gray-700">
                            {enrichmentStatus.enrichment_status.quality_metrics.quality_score ||
                              'N/A'}
                            /10
                          </span>
                        </div>
                        <div className="text-sm">
                          <span className="font-medium text-gray-700">Completeness:</span>{' '}
                          <span className="font-medium text-gray-700">
                            {enrichmentStatus.enrichment_status.quality_metrics
                              .content_completeness || 0}
                            %
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex justify-end space-x-3 border-t border-gray-200 bg-gray-50 px-6 py-4">
              <button
                onClick={() => setStatusDialogOpen(false)}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Close
              </button>
              <button
                onClick={handleEnrichSingleMovie}
                disabled={loading}
                className="rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Enrich Now
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );

  return (
    <div className="mx-auto max-w-7xl p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold text-gray-900">🎬 Movie Enrichment Panel</h1>
        <p className="text-gray-600">
          Comprehensive movie data enrichment using unified TMDB/IMDB services
        </p>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="mb-6 rounded-lg border border-green-200 bg-green-50 p-4">
          <div className="flex">
            <div className="shrink-0">
              <svg className="size-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-green-800">{success}</p>
            </div>
            <div className="ml-auto pl-3">
              <button
                onClick={() => setSuccess(null)}
                className="inline-flex text-green-400 hover:text-green-600"
              >
                <svg className="size-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
          <div className="flex">
            <div className="shrink-0">
              <svg className="size-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-red-800">{error}</p>
            </div>
            <div className="ml-auto pl-3">
              <button
                onClick={() => setError(null)}
                className="inline-flex text-red-400 hover:text-red-600"
              >
                <svg className="size-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Configuration Panel */}
      <div className="mb-6 rounded-xl border border-gray-200 bg-white shadow-lg">
        <div className="border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">⚙️ Enrichment Configuration</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Enrichment Type
              </label>
              <select
                value={enrichmentType}
                onChange={e => setEnrichmentType(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-700 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
              >
                <option value="comprehensive">🔥 Comprehensive (All Data)</option>
                <option value="quality_based">🎯 Quality-Based (Issues Only)</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Focus Areas</label>
              <div className="space-y-2">
                {focusAreaOptions.map(option => (
                  <label key={option.value} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedFocusAreas.includes(option.value)}
                      onChange={e => {
                        if (e.target.checked) {
                          setSelectedFocusAreas([...selectedFocusAreas, option.value]);
                        } else {
                          setSelectedFocusAreas(selectedFocusAreas.filter(f => f !== option.value));
                        }
                      }}
                      className="size-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">{option.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-6">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={forceRefresh}
                onChange={e => setForceRefresh(e.target.checked)}
                className="size-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">🔄 Force Refresh Existing Data</span>
            </label>
          </div>
        </div>
      </div>

      {/* Individual Movie Enrichment */}
      <div className="mb-6 rounded-xl border border-gray-200 bg-white shadow-lg">
        <div className="border-b border-gray-200 bg-gradient-to-r from-purple-50 to-pink-50 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">🎬 Individual Movie Enrichment</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 items-end gap-4 md:grid-cols-4">
            <div className="md:col-span-1">
              <label className="mb-2 block text-sm font-medium text-gray-700">Movie ID</label>
              <input
                type="number"
                value={selectedMovieId}
                onChange={e => setSelectedMovieId(e.target.value)}
                placeholder="Enter movie ID"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-700 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
              />
            </div>
            <div className="flex flex-wrap gap-3 md:col-span-3">
              <button
                onClick={handleEnrichSingleMovie}
                disabled={loading || !selectedMovieId}
                className="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <svg
                      className="-ml-1 mr-2 size-4 animate-spin text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Enriching...
                  </>
                ) : (
                  <>
                    <svg className="mr-2 size-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Enrich Movie
                  </>
                )}
              </button>

              <button
                onClick={handleGetEnrichmentStatus}
                disabled={loading || !selectedMovieId}
                className="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <svg className="mr-2 size-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                </svg>
                Check Status
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Batch Movie Enrichment */}
      <div className="mb-6 rounded-xl border border-gray-200 bg-white shadow-lg">
        <div className="border-b border-gray-200 bg-gradient-to-r from-green-50 to-emerald-50 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">🚀 Batch Movie Enrichment</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Movie IDs (comma-separated)
              </label>
              <textarea
                value={batchMovieIds}
                onChange={e => setBatchMovieIds(e.target.value)}
                placeholder="1, 2, 3, 4, 5..."
                rows={3}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-700 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
              />
            </div>
            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  Max Concurrent
                </label>
                <input
                  type="number"
                  value={maxConcurrent}
                  onChange={e => setMaxConcurrent(parseInt(e.target.value) || 5)}
                  min="1"
                  max="10"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-700 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
                />
              </div>
              <button
                onClick={handleBatchEnrichMovies}
                disabled={batchLoading || !batchMovieIds.trim()}
                className="inline-flex w-full items-center justify-center rounded-md border border-transparent bg-green-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {batchLoading ? (
                  <>
                    <svg
                      className="-ml-1 mr-2 size-4 animate-spin text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Processing Batch...
                  </>
                ) : (
                  <>
                    <svg className="mr-2 size-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Start Batch Enrichment
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Quality-Based Enrichment */}
      <div className="mb-6 rounded-xl border border-gray-200 bg-white shadow-lg">
        <div className="border-b border-gray-200 bg-gradient-to-r from-yellow-50 to-orange-50 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">🎯 Quality-Based Enrichment</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Max Quality Score
              </label>
              <input
                type="number"
                value={qualityOptions.qualityScoreMax}
                onChange={e =>
                  setQualityOptions(prev => ({
                    ...prev,
                    qualityScoreMax: parseFloat(e.target.value) || 7.0,
                  }))
                }
                min="0"
                max="10"
                step="0.1"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-700 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Limit</label>
              <input
                type="number"
                value={qualityOptions.limit}
                onChange={e =>
                  setQualityOptions(prev => ({
                    ...prev,
                    limit: parseInt(e.target.value) || 50,
                  }))
                }
                min="1"
                max="100"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-700 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={handleEnrichQualityIssues}
                disabled={qualityLoading}
                className="inline-flex w-full items-center justify-center rounded-md border border-transparent bg-yellow-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {qualityLoading ? (
                  <>
                    <svg
                      className="-ml-1 mr-2 size-4 animate-spin text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Processing...
                  </>
                ) : (
                  <>
                    <svg className="mr-2 size-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Enrich Quality Issues
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Results Display */}
      {renderEnrichmentResults()}

      {/* Status Dialog */}
      {renderStatusDialog()}
    </div>
  );
};

export default MovieEnrichmentPanel;
