import { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  Grid,
  IconButton,
  Alert,
  CircularProgress,
  // Chip,
} from '@mui/material';
import {
  Close as CloseIcon,
  LocationOn as LocationIcon,
  Person as PersonIcon,
  Work as WorkIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { toast } from 'react-hot-toast';
import { updateProfileCompletion, setProfileDataLoaded } from '../../store/slices/authSlice';
import {
  updateCurrentUserProfileAPI,
  getProfileChoicesAPI,
  autoDetectLocationAPI,
  getProfileCompletionStatusAPI,
} from '../../api/profileService';
import { useTranslation } from '../../i18n/hooks/useTranslation';

const ProfileCompletionModal = ({ open, onClose, onComplete }) => {
  const dispatch = useDispatch();
  const { user } = useSelector(state => state.auth);
  const { t } = useTranslation('profile');

  const steps = [
    { id: 'personal', label: t('modal.steps.personal'), icon: <PersonIcon /> },
    { id: 'demographic', label: t('modal.steps.demographic'), icon: <WorkIcon /> },
    { id: 'location', label: t('modal.steps.location'), icon: <LocationIcon /> },
  ];

  const inputSx = {
    '& .MuiInputBase-root': {
      color: '#e5e7eb',
      background: '#0f172a',
      '&:hover .MuiOutlinedInput-notchedOutline': {
        borderColor: '#ef4444',
      },
      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
        borderColor: '#ef4444',
        borderWidth: '2px',
      },
    },
    '& .MuiOutlinedInput-notchedOutline': {
      borderColor: '#334155',
      borderWidth: '1px',
    },
    '& .MuiInputLabel-root': {
      color: '#cbd5e1',
      fontWeight: 600,
      fontSize: '1rem',
      '&.Mui-focused': {
        color: '#ef4444',
      },
    },
    '& .MuiFormHelperText-root': {
      color: '#9ca3af',
      '&.Mui-error': {
        color: '#fca5a5',
      },
    },
    '& .MuiInputBase-input::placeholder': {
      color: '#9ca3af',
      opacity: 1,
    },
  };

  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingLocation, setLoadingLocation] = useState(false);
  const [choices, setChoices] = useState({});
  // const [_completionStatus, _setCompletionStatus] = useState(null);

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    birth_date: '',
    gender: '',
    occupation: '',
    location: '',
    zip_code: '',
    bio: '',
  });

  const [errors, setErrors] = useState({});

  // Load data when modal opens
  const loadInitialData = useCallback(async () => {
    try {
      console.log('Loading initial data...');

      // Load profile choices and current data
      const [choicesData, statusData] = await Promise.all([
        getProfileChoicesAPI(),
        getProfileCompletionStatusAPI(),
      ]);

      console.log('Choices data:', choicesData);
      console.log('Status data:', statusData);

      if (choicesData.status === 'success') {
        setChoices(choicesData.data);
        console.log('Choices set:', choicesData.data);
      }

      if (statusData.status === 'success') {
        // _setCompletionStatus(statusData.data);

        // Set profile data as loaded
        dispatch(setProfileDataLoaded(true));

        // Update Redux state with fresh data from API
        dispatch(
          updateProfileCompletion({
            is_profile_complete: statusData.data.is_complete,
            profile_completion_percentage: statusData.data.completion_percentage,
          })
        );

        // Check if modal should still be shown
        if (statusData.data.is_complete || statusData.data.completion_percentage >= 80) {
          console.log('Profile is complete, closing modal...');
          onClose();
        }
      }

      // Pre-fill form with existing user data
      setFormData({
        first_name: user.firstName || '',
        last_name: user.lastName || '',
        birth_date: user.birth_date || '',
        gender: user.gender || '',
        occupation: user.occupation || '',
        location: user.location || '',
        zip_code: user.zip_code || '',
        bio: user.bio || '',
      });
    } catch (error) {
      console.error('Error loading initial data:', error);
      toast.error(t('toasts.load_failed'));
    }
  }, [dispatch, onClose, t, user]);

  useEffect(() => {
    if (open && user) {
      loadInitialData();
    }
  }, [open, user, loadInitialData]);

  // Check if modal should be shown based on conditions
  useEffect(() => {
    if (open && user) {
      // Log current conditions for debugging
      console.log('Profile Completion Modal Conditions:', {
        isAuthenticated: true,
        isEmailVerified: user.is_email_verified,
        isProfileComplete: user.is_profile_complete,
        profileCompletionPercentage: user.profile_completion_percentage,
        shouldShowModal:
          user.is_email_verified &&
          !user.is_profile_complete &&
          user.profile_completion_percentage < 80,
      });
    }
  }, [open, user]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));

    // Clear field error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: null,
      }));
    }
  };

  const validateCurrentStep = () => {
    const newErrors = {};

    switch (activeStep) {
      case 0: // Personal Info
        if (!formData.first_name.trim()) {
          newErrors.first_name = t('errors.first_name_required_basic');
        }
        if (!formData.last_name.trim()) {
          newErrors.last_name = t('errors.last_name_required_basic');
        }
        if (!formData.birth_date) {
          newErrors.birth_date = t('errors.birth_date_required_basic');
        } else {
          // Validate age (13-120)
          const birthDate = new Date(formData.birth_date);
          const today = new Date();
          const age = today.getFullYear() - birthDate.getFullYear();
          if (age < 13) {
            newErrors.birth_date = t('errors.age_min_13');
          } else if (age > 120) {
            newErrors.birth_date = t('errors.age_max_120');
          }
        }
        break;

      case 1: // Demographics
        if (!formData.gender) {
          newErrors.gender = t('errors.gender_required_basic');
        }
        if (!formData.occupation) {
          newErrors.occupation = t('errors.occupation_required_basic');
        }
        break;

      case 2: // Location (optional)
        // No required fields for location step
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateCurrentStep()) {
      setActiveStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const handleAutoDetectLocation = async () => {
    setLoadingLocation(true);
    try {
      const result = await autoDetectLocationAPI();

      if (result.status === 'success') {
        setFormData(prev => ({
          ...prev,
          location: result.data.location || prev.location,
          zip_code: result.data.zip_code || prev.zip_code,
        }));
        toast.success(t('toasts.location_detect_success'));
      }
    } catch (error) {
      console.error('Error detecting location:', error);
      toast.error(t('toasts.location_detect_failed'));
    } finally {
      setLoadingLocation(false);
    }
  };

  const validateCompleteProfile = () => {
    const newErrors = {};

    // Validate ALL required demographic fields for complete profile
    if (!formData.first_name.trim()) {
      newErrors.first_name = t('errors.first_name_required');
    }
    if (!formData.last_name.trim()) {
      newErrors.last_name = t('errors.last_name_required');
    }
    if (!formData.birth_date) {
      newErrors.birth_date = t('errors.birth_date_required_recs');
    } else {
      // Validate age (13-120)
      const birthDate = new Date(formData.birth_date);
      const today = new Date();
      const age = today.getFullYear() - birthDate.getFullYear();
      if (age < 13) {
        newErrors.birth_date = t('errors.age_min_13');
      } else if (age > 120) {
        newErrors.birth_date = t('errors.age_max_120');
      }
    }
    if (!formData.gender) {
      newErrors.gender = t('errors.gender_required_recs');
    }
    if (!formData.occupation) {
      newErrors.occupation = t('errors.occupation_required_recs');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const calculateDemographicData = formData => {
    // Calculate age from birth_date
    const age = formData.birth_date
      ? new Date().getFullYear() - new Date(formData.birth_date).getFullYear()
      : null;

    // Calculate age_group (must match backend User.calculate_age_group())
    let age_group = null;
    if (age) {
      if (age < 18) age_group = 'Under 18';
      else if (age >= 18 && age <= 24) age_group = '18-24';
      else if (age >= 25 && age <= 34) age_group = '25-34';
      else if (age >= 35 && age <= 44) age_group = '35-44';
      else if (age >= 45 && age <= 49) age_group = '45-49';
      else if (age >= 50 && age <= 55) age_group = '50-55';
      else age_group = '56+';
    }

    return {
      ...formData,
      age,
      age_group,
      // Ensure all demographic fields are present
      demographic_complete: !!(age && formData.gender && formData.occupation),
    };
  };

  const handleSubmit = async () => {
    // Validate COMPLETE profile before submission
    if (!validateCompleteProfile()) {
      toast.error(t('toasts.complete_required_for_recs'));
      return;
    }

    setLoading(true);
    try {
      // Calculate enhanced demographic data
      const enhancedFormData = calculateDemographicData(formData);

      console.log('Submitting COMPLETE profile data:', enhancedFormData);

      // Update profile via API with COMPLETE demographic data
      const result = await updateCurrentUserProfileAPI(enhancedFormData);

      if (result.status === 'success') {
        // Update Redux store with new user data
        dispatch(
          updateProfileCompletion({
            is_profile_complete: result.data.is_profile_complete,
            profile_completion_percentage: result.data.profile_completion_percentage,
          })
        );

        toast.success(t('toasts.complete_success'));

        // Call completion callback
        if (onComplete) {
          onComplete(result.data);
        }

        onClose();
      }
    } catch (error) {
      console.error('Error updating profile:', error);

      if (error.errors) {
        setErrors(error.errors);
      } else {
        toast.error(error.message || t('toasts.update_failed'));
      }
    } finally {
      setLoading(false);
    }
  };

  const getStepContent = step => {
    switch (step) {
      case 0:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('modal.labels.first_name')}
                value={formData.first_name}
                onChange={e => handleInputChange('first_name', e.target.value)}
                error={!!errors.first_name}
                helperText={errors.first_name}
                required
                sx={inputSx}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('modal.labels.last_name')}
                value={formData.last_name}
                onChange={e => handleInputChange('last_name', e.target.value)}
                error={!!errors.last_name}
                helperText={errors.last_name}
                required
                sx={inputSx}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('modal.labels.birth_date')}
                type="date"
                value={formData.birth_date}
                onChange={e => handleInputChange('birth_date', e.target.value)}
                error={!!errors.birth_date}
                helperText={errors.birth_date || t('modal.helper.birthdate_purpose')}
                InputLabelProps={{ shrink: true }}
                required
                sx={inputSx}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('modal.labels.bio')}
                multiline
                rows={3}
                value={formData.bio}
                onChange={e => handleInputChange('bio', e.target.value)}
                placeholder={t('modal.placeholders.bio')}
                helperText={t('modal.helper.bio_optional')}
                sx={inputSx}
              />
            </Grid>
          </Grid>
        );

      case 1:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth error={!!errors.gender} required>
                <InputLabel
                  id="gender-label"
                  sx={{ color: '#cbd5e1', fontWeight: 600, fontSize: '1rem' }}
                >
                  {t('modal.labels.gender')}
                </InputLabel>
                <Select
                  labelId="gender-label"
                  value={formData.gender}
                  onChange={e => handleInputChange('gender', e.target.value)}
                  label={t('modal.labels.gender')}
                  sx={{
                    minHeight: '56px',
                    color: '#e5e7eb',
                    background: '#0f172a',
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#334155',
                      borderWidth: '1px',
                    },
                    '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#ef4444' },
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#ef4444',
                      borderWidth: '2px',
                    },
                  }}
                >
                  {choices.gender_choices?.map(choice => (
                    <MenuItem key={choice.value} value={choice.value}>
                      {t(`options.gender.${choice.value}`, { defaultValue: choice.label })}
                    </MenuItem>
                  ))}
                </Select>
                {errors.gender && (
                  <Typography variant="caption" color="error" sx={{ mt: 1, ml: 2 }}>
                    {errors.gender}
                  </Typography>
                )}
                <Typography
                  variant="caption"
                  sx={{ mt: 1, ml: 2, color: '#9ca3af', fontWeight: 500 }}
                >
                  {t('modal.helper.available_choices', {
                    count: choices.gender_choices?.length || 0,
                  })}
                </Typography>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth error={!!errors.occupation} required>
                <InputLabel
                  id="occupation-label"
                  sx={{ color: '#cbd5e1', fontWeight: 600, fontSize: '1rem' }}
                >
                  {t('modal.labels.occupation')}
                </InputLabel>
                <Select
                  labelId="occupation-label"
                  value={formData.occupation}
                  onChange={e => handleInputChange('occupation', e.target.value)}
                  label={t('modal.labels.occupation')}
                  sx={{
                    minHeight: '56px',
                    color: '#e5e7eb',
                    background: '#0f172a',
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#334155',
                      borderWidth: '1px',
                    },
                    '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#ef4444' },
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#ef4444',
                      borderWidth: '2px',
                    },
                  }}
                >
                  {choices.occupation_choices?.map(choice => (
                    <MenuItem key={choice.value} value={choice.value}>
                      {t(`options.occupation.${choice.value}`, { defaultValue: choice.label })}
                    </MenuItem>
                  ))}
                </Select>
                {errors.occupation && (
                  <Typography variant="caption" color="error" sx={{ mt: 1, ml: 2 }}>
                    {errors.occupation}
                  </Typography>
                )}
                <Typography
                  variant="caption"
                  sx={{ mt: 1, ml: 2, color: '#9ca3af', fontWeight: 500 }}
                >
                  {t('modal.helper.available_choices', {
                    count: choices.occupation_choices?.length || 0,
                  })}
                </Typography>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <Alert
                severity="info"
                sx={{
                  mt: 2,
                  background: 'rgba(239,68,68,0.1)',
                  border: '1px solid #ef4444',
                  color: '#f3f4f6',
                  '& .MuiAlert-icon': { color: '#ef4444' },
                }}
              >
                <Typography variant="body2">
                  <strong>{t('modal.info.why_we_ask_title')}</strong>{' '}
                  {t('modal.info.why_we_ask_text')}
                </Typography>
              </Alert>
            </Grid>
          </Grid>
        );

      case 2:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} md={7}>
              <TextField
                fullWidth
                label={t('modal.labels.location')}
                value={formData.location}
                onChange={e => handleInputChange('location', e.target.value)}
                placeholder={t('modal.placeholders.location')}
                helperText={t('modal.helper.location_optional')}
                sx={inputSx}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label={t('modal.labels.zip_code')}
                value={formData.zip_code}
                onChange={e => handleInputChange('zip_code', e.target.value)}
                placeholder={t('modal.placeholders.zip_code')}
                helperText={t('modal.helper.optional')}
                sx={inputSx}
              />
            </Grid>
            <Grid
              item
              xs={12}
              md={2}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: { xs: 'flex-start', md: 'flex-end' },
              }}
            >
              <Button
                variant="outlined"
                onClick={handleAutoDetectLocation}
                disabled={loadingLocation}
                startIcon={loadingLocation ? <CircularProgress size={16} /> : <LocationIcon />}
                sx={{
                  minWidth: 160,
                  color: loadingLocation ? '#fff' : '#ef4444',
                  borderColor: '#ef4444',
                  background: loadingLocation ? '#ef4444' : 'rgba(239,68,68,0.05)',
                  fontWeight: 700,
                  '&:hover': { background: '#ef4444', color: '#fff', borderColor: '#ef4444' },
                }}
              >
                {loadingLocation ? t('modal.buttons.detecting') : t('modal.buttons.auto_detect')}
              </Button>
            </Grid>
            <Grid item xs={12}>
              <Alert
                severity="info"
                sx={{
                  background: 'rgba(239,68,68,0.1)',
                  border: '1px solid #ef4444',
                  color: '#f3f4f6',
                  '& .MuiAlert-icon': { color: '#ef4444' },
                }}
              >
                <Typography variant="body2">
                  📍 <strong>{t('modal.info.location_info_title')}</strong> -{' '}
                  {t('modal.info.location_info_text')}
                </Typography>
              </Alert>
            </Grid>
            <Grid item xs={12}>
              <Alert
                severity="warning"
                sx={{
                  background: 'rgba(239,68,68,0.1)',
                  border: '1px solid #ef4444',
                  color: '#f3f4f6',
                  '& .MuiAlert-icon': { color: '#ef4444' },
                }}
              >
                <Typography variant="body2">
                  🎯 <strong>{t('modal.info.ready_to_complete_title')}</strong>{' '}
                  {t('modal.info.ready_to_complete_text')}
                </Typography>
              </Alert>
            </Grid>
          </Grid>
        );

      default:
        return null;
    }
  };

  const getCompletionPercentage = () => {
    // Required fields for demographic recommendations
    const requiredFields = [
      formData.first_name,
      formData.last_name,
      formData.birth_date,
      formData.gender,
      formData.occupation,
    ];

    // Optional fields that enhance recommendations
    const optionalFields = [formData.location, formData.zip_code, formData.bio];

    const completedRequired = requiredFields.filter(
      field => field && field.toString().trim() !== ''
    ).length;
    const completedOptional = optionalFields.filter(
      field => field && field.toString().trim() !== ''
    ).length;

    // Weight required fields more heavily (80% of total)
    const requiredWeight = 0.8;
    const optionalWeight = 0.2;

    const requiredScore = (completedRequired / requiredFields.length) * requiredWeight;
    const optionalScore = (completedOptional / optionalFields.length) * optionalWeight;

    return Math.round((requiredScore + optionalScore) * 100);
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          background: '#111827',
          color: '#ffffff',
          border: '1px solid #374151',
          boxShadow: 6,
        },
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h6" component="div" sx={{ color: '#ef4444', fontWeight: 700 }}>
              {t('modal.title')}
            </Typography>
            <Typography variant="body2" sx={{ color: '#e5e7eb' }}>
              {t('modal.subtitle')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" sx={{ color: '#e5e7eb' }}>
                {t('modal.helper.percent_complete', { percent: getCompletionPercentage() })}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={getCompletionPercentage()}
                sx={{
                  width: 100,
                  height: 6,
                  borderRadius: 3,
                  background: '#374151',
                  '& .MuiLinearProgress-bar': { backgroundColor: '#ef4444' },
                }}
              />
            </Box>
            <IconButton onClick={onClose} size="small" sx={{ color: '#9ca3af' }}>
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ mt: 2 }}>
          <Stepper
            activeStep={activeStep}
            alternativeLabel
            sx={{
              mb: 4,
              '& .MuiStepConnector-line': { borderColor: '#374151' },
              '& .MuiStepIcon-root': {
                color: '#6b7280',
                '&.Mui-active': { color: '#ef4444' },
                '&.Mui-completed': { color: '#22c55e' },
              },
              '& .MuiStepLabel-label': { color: '#cbd5e1', fontWeight: 700, fontSize: '1.05rem' },
              '& .MuiStepLabel-label.Mui-active': { color: '#ffffff' },
              '& .MuiStepLabel-label.Mui-completed': { color: '#e5e7eb' },
            }}
          >
            {steps.map((step, index) => (
              <Step key={step.id}>
                <StepLabel
                  icon={
                    activeStep > index ? (
                      <CheckIcon color="success" />
                    ) : activeStep === index ? (
                      step.icon
                    ) : (
                      step.icon
                    )
                  }
                >
                  {step.label}
                </StepLabel>
              </Step>
            ))}
          </Stepper>

          {getStepContent(activeStep)}
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 3, pt: 1 }}>
        <Button
          onClick={onClose}
          disabled={loading}
          sx={{
            color: '#fff',
            borderColor: '#6b7280',
            background: 'rgba(55,65,81,0.5)',
            '&:hover': { background: '#374151', borderColor: '#ef4444', color: '#ef4444' },
            borderRadius: 2,
          }}
          variant="outlined"
        >
          {t('modal.buttons.skip')}
        </Button>

        <Box sx={{ flex: 1 }} />

        {activeStep > 0 && (
          <Button
            onClick={handleBack}
            disabled={loading}
            sx={{
              color: '#fff',
              borderColor: '#6b7280',
              background: 'rgba(55,65,81,0.5)',
              '&:hover': { background: '#374151', borderColor: '#ef4444', color: '#ef4444' },
              borderRadius: 2,
            }}
            variant="outlined"
          >
            {t('modal.buttons.back')}
          </Button>
        )}

        {activeStep < steps.length - 1 ? (
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={loading}
            sx={{
              background: '#ef4444',
              color: '#fff',
              fontWeight: 700,
              borderRadius: 2,
              boxShadow: 3,
              '&:hover': { background: '#dc2626' },
            }}
          >
            {t('modal.buttons.next')}
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : null}
            sx={{
              background: '#ef4444',
              color: '#fff',
              fontWeight: 700,
              borderRadius: 2,
              boxShadow: 3,
              '&:hover': { background: '#dc2626' },
            }}
          >
            {loading ? t('modal.buttons.saving') : t('modal.buttons.complete_profile')}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ProfileCompletionModal;
