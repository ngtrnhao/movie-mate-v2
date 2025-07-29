import React, { useState, useEffect } from 'react';
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
  Chip,
} from '@mui/material';
import {
  Close as CloseIcon,
  LocationOn as LocationIcon,
  Person as PersonIcon,
  Work as WorkIcon,
  DateRange as DateIcon,
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

const steps = [
  { id: 'personal', label: 'Personal Info', icon: <PersonIcon /> },
  { id: 'demographic', label: 'Demographics', icon: <WorkIcon /> },
  { id: 'location', label: 'Location', icon: <LocationIcon /> },
];

const ProfileCompletionModal = ({ open, onClose, onComplete }) => {
  const dispatch = useDispatch();
  const { user } = useSelector(state => state.auth);

  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingLocation, setLoadingLocation] = useState(false);
  const [choices, setChoices] = useState({});
  const [completionStatus, setCompletionStatus] = useState(null);

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
  useEffect(() => {
    if (open && user) {
      loadInitialData();
    }
  }, [open, user]);

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

  const loadInitialData = async () => {
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
        setCompletionStatus(statusData.data);

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
      toast.error('Failed to load profile data');
    }
  };

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
          newErrors.first_name = 'First name is required';
        }
        if (!formData.last_name.trim()) {
          newErrors.last_name = 'Last name is required';
        }
        if (!formData.birth_date) {
          newErrors.birth_date = 'Birth date is required';
        } else {
          // Validate age (13-120)
          const birthDate = new Date(formData.birth_date);
          const today = new Date();
          const age = today.getFullYear() - birthDate.getFullYear();
          if (age < 13) {
            newErrors.birth_date = 'You must be at least 13 years old';
          } else if (age > 120) {
            newErrors.birth_date = 'Please enter a valid birth date';
          }
        }
        break;

      case 1: // Demographics
        if (!formData.gender) {
          newErrors.gender = 'Gender is required';
        }
        if (!formData.occupation) {
          newErrors.occupation = 'Occupation is required';
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
        toast.success('Location detected successfully!');
      }
    } catch (error) {
      console.error('Error detecting location:', error);
      toast.error('Could not detect location automatically');
    } finally {
      setLoadingLocation(false);
    }
  };

  const validateCompleteProfile = () => {
    const newErrors = {};

    // Validate ALL required demographic fields for complete profile
    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required for complete profile';
    }
    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required for complete profile';
    }
    if (!formData.birth_date) {
      newErrors.birth_date = 'Birth date is required for personalized recommendations';
    } else {
      // Validate age (13-120)
      const birthDate = new Date(formData.birth_date);
      const today = new Date();
      const age = today.getFullYear() - birthDate.getFullYear();
      if (age < 13) {
        newErrors.birth_date = 'You must be at least 13 years old';
      } else if (age > 120) {
        newErrors.birth_date = 'Please enter a valid birth date';
      }
    }
    if (!formData.gender) {
      newErrors.gender = 'Gender is required for demographic recommendations';
    }
    if (!formData.occupation) {
      newErrors.occupation = 'Occupation is required for recommendation algorithms';
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
      toast.error('Please complete all required fields for personalized recommendations');
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

        toast.success('Profile completed successfully!');

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
        toast.error(error.message || 'Failed to update profile');
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
                label="First Name"
                value={formData.first_name}
                onChange={e => handleInputChange('first_name', e.target.value)}
                error={!!errors.first_name}
                helperText={errors.first_name}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Last Name"
                value={formData.last_name}
                onChange={e => handleInputChange('last_name', e.target.value)}
                error={!!errors.last_name}
                helperText={errors.last_name}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Birth Date"
                type="date"
                value={formData.birth_date}
                onChange={e => handleInputChange('birth_date', e.target.value)}
                error={!!errors.birth_date}
                helperText={
                  errors.birth_date ||
                  'Used to calculate your age and provide better recommendations'
                }
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Bio"
                multiline
                rows={3}
                value={formData.bio}
                onChange={e => handleInputChange('bio', e.target.value)}
                placeholder="Tell us a bit about yourself..."
                helperText="Optional - This helps other users learn about you"
              />
            </Grid>
          </Grid>
        );

      case 1:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth error={!!errors.gender} required>
                <InputLabel id="gender-label">Gender</InputLabel>
                <Select
                  labelId="gender-label"
                  value={formData.gender}
                  onChange={e => handleInputChange('gender', e.target.value)}
                  label="Gender"
                  sx={{ minHeight: '56px' }}
                >
                  {choices.gender_choices?.map(choice => (
                    <MenuItem key={choice.value} value={choice.value}>
                      {choice.label}
                    </MenuItem>
                  ))}
                </Select>
                {errors.gender && (
                  <Typography variant="caption" color="error" sx={{ mt: 1, ml: 2 }}>
                    {errors.gender}
                  </Typography>
                )}
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, ml: 2 }}>
                  Available choices: {choices.gender_choices?.length || 0}
                </Typography>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth error={!!errors.occupation} required>
                <InputLabel id="occupation-label">Occupation</InputLabel>
                <Select
                  labelId="occupation-label"
                  value={formData.occupation}
                  onChange={e => handleInputChange('occupation', e.target.value)}
                  label="Occupation"
                  sx={{ minHeight: '56px' }}
                >
                  {choices.occupation_choices?.map(choice => (
                    <MenuItem key={choice.value} value={choice.value}>
                      {choice.label}
                    </MenuItem>
                  ))}
                </Select>
                {errors.occupation && (
                  <Typography variant="caption" color="error" sx={{ mt: 1, ml: 2 }}>
                    {errors.occupation}
                  </Typography>
                )}
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, ml: 2 }}>
                  Available choices: {choices.occupation_choices?.length || 0}
                </Typography>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Why we ask:</strong> This information helps us provide personalized movie
                  recommendations based on preferences similar to users with your demographic
                  profile.
                </Typography>
              </Alert>
            </Grid>
          </Grid>
        );

      case 2:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <TextField
                  fullWidth
                  label="Location"
                  value={formData.location}
                  onChange={e => handleInputChange('location', e.target.value)}
                  placeholder="e.g., New York, NY, USA"
                  helperText="Optional - Helps provide region-specific recommendations"
                />
                <Button
                  variant="outlined"
                  onClick={handleAutoDetectLocation}
                  disabled={loadingLocation}
                  startIcon={loadingLocation ? <CircularProgress size={16} /> : <LocationIcon />}
                  sx={{ minWidth: 140 }}
                >
                  {loadingLocation ? 'Detecting...' : 'Auto Detect'}
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Zip Code"
                value={formData.zip_code}
                onChange={e => handleInputChange('zip_code', e.target.value)}
                placeholder="e.g., 10001"
                helperText="Optional"
              />
            </Grid>
            <Grid item xs={12}>
              <Alert severity="info">
                <Typography variant="body2">
                  📍 <strong>Optional Location Info</strong> - This helps provide region-specific
                  movie recommendations and local cinema information.
                </Typography>
              </Alert>
            </Grid>
            <Grid item xs={12}>
              <Alert severity="warning">
                <Typography variant="body2">
                  🎯 <strong>Ready to Complete!</strong> Click "Complete Profile" to generate your
                  personalized movie recommendations. This will create your demographic profile and
                  recommendations based on your preferences.
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
        sx: { borderRadius: 2 },
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h6" component="div">
              Complete Your Profile
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Help us provide better movie recommendations
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                {getCompletionPercentage()}% complete
              </Typography>
              <LinearProgress
                variant="determinate"
                value={getCompletionPercentage()}
                sx={{ width: 100, height: 6, borderRadius: 3 }}
              />
            </Box>
            <IconButton onClick={onClose} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ mt: 2 }}>
          <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
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
        <Button onClick={onClose} disabled={loading}>
          Skip for now
        </Button>

        <Box sx={{ flex: 1 }} />

        {activeStep > 0 && (
          <Button onClick={handleBack} disabled={loading}>
            Back
          </Button>
        )}

        {activeStep < steps.length - 1 ? (
          <Button variant="contained" onClick={handleNext} disabled={loading}>
            Next
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : null}
          >
            {loading ? 'Saving...' : 'Complete Profile'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ProfileCompletionModal;
