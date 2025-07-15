import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Grid,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Divider,
  Switch,
  FormControlLabel,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  Analytics as AnalyticsIcon,
  AutoFix as AutoFixIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
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
    { value: 'basic', label: '📝 Basic Info (Titles, Overviews)' },
    { value: 'visual', label: '🖼️ Visual Assets (Posters, Backdrops)' },
    { value: 'metadata', label: '🎭 Metadata (Cast, Genres, Trailers)' },
    { value: 'ratings', label: '⭐ Ratings (TMDB, IMDB)' },
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
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {isSuccess ? '✅ Enrichment Results' : '❌ Enrichment Failed'}
          </Typography>

          {/* Single Movie Results */}
          {enrichmentResults.enrichment_result && (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Movie: {enrichmentResults.movie_title} (ID: {enrichmentResults.movie_id})
              </Typography>

              {result.quality_before && result.quality_after && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2">Quality Improvement:</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Chip
                        label={`Before: ${result.quality_before.quality_score || 0}/10`}
                        color="warning"
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Chip
                        label={`After: ${result.quality_after.quality_score || 0}/10`}
                        color="success"
                        size="small"
                      />
                    </Grid>
                  </Grid>
                </Box>
              )}

              {result.improvements && result.improvements.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2">Improvements Made:</Typography>
                  {result.improvements.map((improvement, index) => (
                    <Chip
                      key={index}
                      label={improvement}
                      color="success"
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))}
                </Box>
              )}

              <Typography variant="body2" color="text.secondary">
                Processing time: {result.processing_time || 0}s
              </Typography>
            </Box>
          )}

          {/* Batch Results */}
          {enrichmentResults.batch_result && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={3}>
                  <Typography variant="h4" color="primary">
                    {result.total_movies || 0}
                  </Typography>
                  <Typography variant="body2">Total Movies</Typography>
                </Grid>
                <Grid item xs={3}>
                  <Typography variant="h4" color="success.main">
                    {result.processed_successfully || 0}
                  </Typography>
                  <Typography variant="body2">Successful</Typography>
                </Grid>
                <Grid item xs={3}>
                  <Typography variant="h4" color="error.main">
                    {result.errors || 0}
                  </Typography>
                  <Typography variant="body2">Errors</Typography>
                </Grid>
                <Grid item xs={3}>
                  <Typography variant="h4" color="info.main">
                    {result.success_rate || 0}%
                  </Typography>
                  <Typography variant="body2">Success Rate</Typography>
                </Grid>
              </Grid>

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Processing time: {result.processing_time || 0}s
              </Typography>
            </Box>
          )}

          {/* Quality-based Results */}
          {enrichmentResults.processed !== undefined && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <Typography variant="h4" color="primary">
                    {enrichmentResults.processed || 0}
                  </Typography>
                  <Typography variant="body2">Movies Processed</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="h4" color="success.main">
                    {enrichmentResults.successful || 0}
                  </Typography>
                  <Typography variant="body2">Successfully Enriched</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="h4" color="error.main">
                    {enrichmentResults.failed || 0}
                  </Typography>
                  <Typography variant="body2">Failed</Typography>
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  // === RENDER ENRICHMENT STATUS DIALOG ===
  const renderStatusDialog = () => (
    <Dialog
      open={statusDialogOpen}
      onClose={() => setStatusDialogOpen(false)}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        📊 Movie Enrichment Status
        {enrichmentStatus?.movie_id && ` - ID: ${enrichmentStatus.movie_id}`}
      </DialogTitle>
      <DialogContent>
        {enrichmentStatus && (
          <Box>
            <Typography variant="h6" gutterBottom>
              {enrichmentStatus.movie_title}
            </Typography>

            {/* Data Completeness */}
            <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
              📊 Data Completeness
            </Typography>

            {Object.entries(enrichmentStatus.enrichment_status?.data_completeness || {}).map(
              ([category, data]) => (
                <Accordion key={category}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2">
                      {category.replace('_', ' ').toUpperCase()}
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={1}>
                      {Object.entries(data).map(([field, value]) => (
                        <Grid item xs={6} key={field}>
                          <Box display="flex" alignItems="center">
                            {value ? (
                              <CheckCircleIcon color="success" />
                            ) : (
                              <ErrorIcon color="error" />
                            )}
                            <Typography variant="body2" sx={{ ml: 1 }}>
                              {field.replace('_', ' ')}
                            </Typography>
                          </Box>
                        </Grid>
                      ))}
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              )
            )}

            {/* Enrichment Opportunities */}
            {enrichmentStatus.enrichment_status?.enrichment_opportunities?.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  💡 Enrichment Opportunities
                </Typography>
                {enrichmentStatus.enrichment_status.enrichment_opportunities.map(
                  (opportunity, index) => (
                    <Chip
                      key={index}
                      label={opportunity}
                      color="info"
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  )
                )}
              </Box>
            )}

            {/* Quality Metrics */}
            {enrichmentStatus.enrichment_status?.quality_metrics && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  📈 Quality Metrics
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2">
                      Quality Score:{' '}
                      {enrichmentStatus.enrichment_status.quality_metrics.quality_score || 'N/A'}/10
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2">
                      Completeness:{' '}
                      {enrichmentStatus.enrichment_status.quality_metrics.content_completeness || 0}
                      %
                    </Typography>
                  </Grid>
                </Grid>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setStatusDialogOpen(false)}>Close</Button>
        <Button onClick={handleEnrichSingleMovie} variant="contained" disabled={loading}>
          Enrich Now
        </Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        🎬 Movie Enrichment Panel
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Comprehensive movie data enrichment using unified TMDB/IMDB services
      </Typography>

      {/* Success/Error Messages */}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Configuration Panel */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            ⚙️ Enrichment Configuration
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Enrichment Type</InputLabel>
                <Select
                  value={enrichmentType}
                  onChange={e => setEnrichmentType(e.target.value)}
                  label="Enrichment Type"
                >
                  <MenuItem value="comprehensive">🔥 Comprehensive (All Data)</MenuItem>
                  <MenuItem value="quality_based">🎯 Quality-Based (Issues Only)</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Focus Areas</InputLabel>
                <Select
                  multiple
                  value={selectedFocusAreas}
                  onChange={e => setSelectedFocusAreas(e.target.value)}
                  label="Focus Areas"
                  renderValue={selected => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map(value => (
                        <Chip
                          key={value}
                          label={focusAreaOptions.find(opt => opt.value === value)?.label || value}
                          size="small"
                        />
                      ))}
                    </Box>
                  )}
                >
                  {focusAreaOptions.map(option => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={forceRefresh}
                    onChange={e => setForceRefresh(e.target.checked)}
                  />
                }
                label="🔄 Force Refresh Existing Data"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Individual Movie Enrichment */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">🎬 Individual Movie Enrichment</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Movie ID"
                type="number"
                value={selectedMovieId}
                onChange={e => setSelectedMovieId(e.target.value)}
                placeholder="Enter movie ID"
              />
            </Grid>
            <Grid item xs={12} md={8}>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  onClick={handleEnrichSingleMovie}
                  disabled={loading || !selectedMovieId}
                  startIcon={loading ? <CircularProgress size={20} /> : <AutoFixIcon />}
                >
                  {loading ? 'Enriching...' : 'Enrich Movie'}
                </Button>

                <Button
                  variant="outlined"
                  onClick={handleGetEnrichmentStatus}
                  disabled={loading || !selectedMovieId}
                  startIcon={<AnalyticsIcon />}
                >
                  Check Status
                </Button>
              </Box>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Batch Movie Enrichment */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">🚀 Batch Movie Enrichment</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Movie IDs (comma-separated)"
                value={batchMovieIds}
                onChange={e => setBatchMovieIds(e.target.value)}
                placeholder="1, 2, 3, 4, 5..."
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Max Concurrent"
                type="number"
                value={maxConcurrent}
                onChange={e => setMaxConcurrent(parseInt(e.target.value) || 5)}
                inputProps={{ min: 1, max: 10 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Button
                variant="contained"
                onClick={handleBatchEnrichMovies}
                disabled={batchLoading || !batchMovieIds.trim()}
                startIcon={batchLoading ? <CircularProgress size={20} /> : <PlayArrowIcon />}
                fullWidth
              >
                {batchLoading ? 'Processing Batch...' : 'Start Batch Enrichment'}
              </Button>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Quality-Based Enrichment */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">🎯 Quality-Based Enrichment</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Max Quality Score"
                type="number"
                value={qualityOptions.qualityScoreMax}
                onChange={e =>
                  setQualityOptions(prev => ({
                    ...prev,
                    qualityScoreMax: parseFloat(e.target.value) || 7.0,
                  }))
                }
                inputProps={{ min: 0, max: 10, step: 0.1 }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Limit"
                type="number"
                value={qualityOptions.limit}
                onChange={e =>
                  setQualityOptions(prev => ({
                    ...prev,
                    limit: parseInt(e.target.value) || 50,
                  }))
                }
                inputProps={{ min: 1, max: 100 }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <Button
                variant="contained"
                onClick={handleEnrichQualityIssues}
                disabled={qualityLoading}
                startIcon={qualityLoading ? <CircularProgress size={20} /> : <AutoFixIcon />}
                color="warning"
                fullWidth
              >
                {qualityLoading ? 'Processing...' : 'Enrich Quality Issues'}
              </Button>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Results Display */}
      {renderEnrichmentResults()}

      {/* Status Dialog */}
      {renderStatusDialog()}
    </Box>
  );
};

export default MovieEnrichmentPanel;
