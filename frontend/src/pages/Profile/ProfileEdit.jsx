import { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Avatar,
  IconButton,
  LinearProgress,
  Alert,
  Card,
  CardContent,
  Chip,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  LocationOn as LocationIcon,
  PhotoCamera as PhotoCameraIcon,
  Person as PersonIcon,
  Work as WorkIcon,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { toast } from 'react-hot-toast';
import { updateUser } from '../../store/slices/authSlice';
import {
  updateCurrentUserProfileAPI,
  getCurrentUserProfileAPI,
  getProfileChoicesAPI,
  autoDetectLocationAPI,
  uploadAvatarAPI,
} from '../../api/profileService';

const ProfileEdit = () => {
  const dispatch = useDispatch();
  const { user: currentUser } = useSelector(state => state.auth);

  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingLocation, setLoadingLocation] = useState(false);
  const [choices, setChoices] = useState({});
  const [userData, setUserData] = useState(null);

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    birth_date: '',
    gender: '',
    occupation: '',
    location: '',
    zip_code: '',
    bio: '',
    avatar_url: '',
  });

  const [errors, setErrors] = useState({});

  // Load initial data
  useEffect(() => {
    if (currentUser?.id) {
      loadData();
    }
  }, [currentUser?.id]);

  // Update form when user data changes
  useEffect(() => {
    if (userData) {
      setFormData({
        first_name: userData.first_name || '',
        last_name: userData.last_name || '',
        birth_date: userData.birth_date || '',
        gender: userData.gender || '',
        occupation: userData.occupation || '',
        location: userData.location || '',
        zip_code: userData.zip_code || '',
        bio: userData.bio || '',
        avatar_url: userData.avatar_url || '',
      });
    }
  }, [userData]);

  const loadData = async () => {
    try {
      setLoading(true);

      // Fetch both user data and choices
      const [userDataResponse, choicesData] = await Promise.all([
        getCurrentUserProfileAPI(),
        getProfileChoicesAPI(),
      ]);

      if (userDataResponse.status === 'success') {
        setUserData(userDataResponse.data);
      }

      if (choicesData.status === 'success') {
        setChoices(choicesData.data);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load profile data');
    } finally {
      setLoading(false);
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

  const validateForm = () => {
    const newErrors = {};

    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required';
    }
    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required';
    }
    if (formData.birth_date) {
      const birthDate = new Date(formData.birth_date);
      const today = new Date();
      const age = today.getFullYear() - birthDate.getFullYear();
      if (age < 13) {
        newErrors.birth_date = 'You must be at least 13 years old';
      } else if (age > 120) {
        newErrors.birth_date = 'Please enter a valid birth date';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const result = await updateCurrentUserProfileAPI(formData);

      if (result.status === 'success') {
        // Update Redux store
        dispatch(updateUser(result.data));

        toast.success('Profile updated successfully!');
        setEditMode(false);
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

  const handleCancel = () => {
    // Reset form to original user data
    if (userData) {
      setFormData({
        first_name: userData.first_name || '',
        last_name: userData.last_name || '',
        birth_date: userData.birth_date || '',
        gender: userData.gender || '',
        occupation: userData.occupation || '',
        location: userData.location || '',
        zip_code: userData.zip_code || '',
        bio: userData.bio || '',
        avatar_url: userData.avatar_url || '',
      });
    }
    setErrors({});
    setEditMode(false);
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

  const handleAvatarUpload = async event => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    const formData = new FormData();
    formData.append('avatar', file);

    setLoading(true);
    try {
      const result = await uploadAvatarAPI(currentUser.id, formData);

      if (result.status === 'success') {
        dispatch(updateUser({ avatarUrl: result.data.avatar_url }));
        setFormData(prev => ({ ...prev, avatar_url: result.data.avatar_url }));
        toast.success('Avatar updated successfully!');
      }
    } catch (error) {
      console.error('Error uploading avatar:', error);
      toast.error('Failed to upload avatar');
    } finally {
      setLoading(false);
    }
  };

  const getCompletionPercentage = () => {
    if (!userData) return 0;
    return userData.profile_completion_percentage || 0;
  };

  const getMissingFields = () => {
    const missing = [];
    if (!formData.birth_date) missing.push('Birth Date');
    if (!formData.gender) missing.push('Gender');
    if (!formData.occupation) missing.push('Occupation');
    if (!formData.location) missing.push('Location');
    if (!formData.bio) missing.push('Bio');
    return missing;
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      {/* Profile Completion Status */}
      <Card sx={{ mb: 3, background: '#1f2937', color: '#fff', borderRadius: 3, boxShadow: 6 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <PersonIcon sx={{ color: '#ef4444' }} />
            <Typography variant="h6" sx={{ color: '#ef4444', fontWeight: 700 }}>
              Profile Completion
            </Typography>
            <Chip
              label={`${getCompletionPercentage()}%`}
              sx={{
                color: getCompletionPercentage() === 100 ? '#22c55e' : '#ef4444',
                borderColor: getCompletionPercentage() === 100 ? '#22c55e' : '#ef4444',
                background: 'transparent',
                fontWeight: 700,
              }}
              variant="outlined"
            />
          </Box>
          <LinearProgress
            variant="determinate"
            value={getCompletionPercentage()}
            sx={{
              mb: 2,
              height: 8,
              borderRadius: 4,
              background: '#374151',
              '& .MuiLinearProgress-bar': {
                backgroundColor: '#ef4444',
              },
            }}
          />
          {getMissingFields().length > 0 && (
            <Alert
              severity="info"
              sx={{
                mt: 2,
                background: 'rgba(239, 68, 68, 0.1)',
                color: '#f3f4f6',
                border: '1px solid #ef4444',
                '& .MuiAlert-icon': {
                  color: '#ef4444',
                },
              }}
            >
              <Typography variant="body2" sx={{ color: '#f3f4f6' }}>
                <strong style={{ color: '#ef4444' }}>Improve your recommendations:</strong> Complete
                these fields:{' '}
                <span style={{ color: '#fbbf24' }}>{getMissingFields().join(', ')}</span>
              </Typography>
            </Alert>
          )}
        </CardContent>
      </Card>
      {/* Main Profile Form */}
      <Paper elevation={3} sx={{ p: 4, background: '#111827', color: '#fff', borderRadius: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
          <Typography variant="h4" component="h1" sx={{ color: '#ef4444', fontWeight: 700 }}>
            Profile Settings
          </Typography>
          {!editMode ? (
            <Button
              variant="contained"
              startIcon={<EditIcon />}
              onClick={() => setEditMode(true)}
              sx={{
                background: '#ef4444',
                color: '#fff',
                fontWeight: 700,
                borderRadius: 2,
                boxShadow: 3,
                '&:hover': { background: '#dc2626' },
              }}
            >
              Edit Profile
            </Button>
          ) : (
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<CancelIcon />}
                onClick={handleCancel}
                disabled={loading}
                sx={{
                  color: '#fff',
                  borderColor: '#6b7280',
                  background: 'rgba(55,65,81,0.5)',
                  '&:hover': { background: '#374151', borderColor: '#ef4444', color: '#ef4444' },
                  borderRadius: 2,
                }}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                startIcon={loading ? <CircularProgress size={16} /> : <SaveIcon />}
                onClick={handleSave}
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
                {loading ? 'Saving...' : 'Save Changes'}
              </Button>
            </Box>
          )}
        </Box>
        <Grid container spacing={4}>
          {/* Avatar Section */}
          <Grid item xs={12} md={4}>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              <Box sx={{ position: 'relative' }}>
                <Avatar
                  src={formData.avatar_url}
                  sx={{
                    width: 150,
                    height: 150,
                    bgcolor: '#374151',
                    color: '#00000',
                    fontSize: 48,
                    border: '3px solid #ef4444',
                  }}
                >
                  {formData.first_name?.charAt(0) || formData.last_name?.charAt(0)}
                </Avatar>
                {editMode && (
                  <IconButton
                    component="label"
                    sx={{
                      position: 'absolute',
                      bottom: 0,
                      right: 0,
                      bgcolor: '#ef4444',
                      color: 'white',
                      '&:hover': { bgcolor: '#dc2626' },
                    }}
                  >
                    <PhotoCameraIcon />
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarUpload}
                      style={{ display: 'none' }}
                    />
                  </IconButton>
                )}
              </Box>
              <Typography variant="h6" textAlign="center" sx={{ color: '#fff', fontWeight: 700 }}>
                {formData.first_name} {formData.last_name}
              </Typography>
              {formData.occupation && (
                <Chip
                  icon={<WorkIcon sx={{ color: '#ef4444' }} />}
                  label={
                    choices.occupation_choices?.find(opt => opt.value === formData.occupation)
                      ?.label || formData.occupation
                  }
                  sx={{
                    color: '#ef4444',
                    borderColor: '#ef4444',
                    background: 'transparent',
                    fontWeight: 700,
                  }}
                  variant="outlined"
                />
              )}
            </Box>
          </Grid>
          {/* Form Fields */}
          <Grid item xs={12} md={8}>
            <Grid container spacing={3}>
              {/* Personal Information */}
              <Grid item xs={12}>
                <Typography
                  variant="h6"
                  sx={{
                    mb: 2,
                    color: '#ef4444',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                  }}
                >
                  <PersonIcon sx={{ color: '#ef4444' }} /> Personal Information
                </Typography>
                <Divider sx={{ mb: 3, borderColor: '#ef4444' }} />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  value={formData.first_name}
                  onChange={e => handleInputChange('first_name', e.target.value)}
                  error={!!errors.first_name}
                  helperText={errors.first_name}
                  disabled={!editMode}
                  required
                  sx={{
                    '& .MuiInputBase-root': {
                      color: '#1f2937',
                      background: '#ffffff',
                      '&:hover .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                      },
                      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                        borderWidth: '2px',
                      },
                    },
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#6b7280',
                      borderWidth: '1px',
                    },
                    '& .MuiInputLabel-root': {
                      color: '#f3f4f6',
                      fontWeight: 600,
                      fontSize: '1rem',
                      textShadow: '0 1px 2px rgba(0,0,0,0.5)',
                      '&.Mui-focused': {
                        color: '#ef4444',
                        fontWeight: 700,
                        textShadow: '0 1px 2px rgba(0,0,0,0.7)',
                      },
                    },
                    '& .MuiFormHelperText-root': {
                      color: '#d1d5db',
                      fontSize: '0.875rem',
                      '&.Mui-error': {
                        color: '#f87171',
                        fontWeight: 500,
                      },
                    },
                    '& .MuiInputBase-input::placeholder': {
                      color: '#4b5563',
                      opacity: 1,
                      fontWeight: 400,
                    },
                  }}
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
                  disabled={!editMode}
                  required
                  sx={{
                    '& .MuiInputBase-root': {
                      color: '#1f2937',
                      background: '#ffffff',
                      '&:hover .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                      },
                      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                        borderWidth: '2px',
                      },
                    },
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#6b7280',
                      borderWidth: '1px',
                    },
                    '& .MuiInputLabel-root': {
                      color: '#f3f4f6',
                      fontWeight: 600,
                      fontSize: '1rem',
                      textShadow: '0 1px 2px rgba(0,0,0,0.5)',
                      '&.Mui-focused': {
                        color: '#ef4444',
                        fontWeight: 700,
                        textShadow: '0 1px 2px rgba(0,0,0,0.7)',
                      },
                    },
                    '& .MuiFormHelperText-root': {
                      color: '#d1d5db',
                      fontSize: '0.875rem',
                      '&.Mui-error': {
                        color: '#f87171',
                        fontWeight: 500,
                      },
                    },
                    '& .MuiInputBase-input::placeholder': {
                      color: '#4b5563',
                      opacity: 1,
                      fontWeight: 400,
                    },
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Birth Date"
                  type="date"
                  value={formData.birth_date}
                  onChange={e => handleInputChange('birth_date', e.target.value)}
                  error={!!errors.birth_date}
                  helperText={
                    errors.birth_date || 'Used for age calculation and better recommendations'
                  }
                  InputLabelProps={{ shrink: true }}
                  disabled={!editMode}
                  sx={{
                    '& .MuiInputBase-root': {
                      color: '#1f2937',
                      background: '#ffffff',
                      '&:hover .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                      },
                      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                        borderWidth: '2px',
                      },
                    },
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#6b7280',
                      borderWidth: '1px',
                    },
                    '& .MuiInputLabel-root': {
                      color: '#f3f4f6',
                      fontWeight: 600,
                      fontSize: '1rem',
                      textShadow: '0 1px 2px rgba(0,0,0,0.5)',
                      '&.Mui-focused': {
                        color: '#ef4444',
                        fontWeight: 700,
                        textShadow: '0 1px 2px rgba(0,0,0,0.7)',
                      },
                    },
                    '& .MuiFormHelperText-root': {
                      color: '#d1d5db',
                      fontSize: '0.875rem',
                      '&.Mui-error': {
                        color: '#f87171',
                        fontWeight: 500,
                      },
                    },
                    '& .MuiInputBase-input::placeholder': {
                      color: '#4b5563',
                      opacity: 1,
                      fontWeight: 400,
                    },
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth disabled={!editMode}>
                  <InputLabel
                    sx={{
                      color: '#ffffff',
                      fontWeight: 600,
                      fontSize: '1rem',
                      textShadow: '0 1px 2px rgba(0,0,0,0.5)',
                    }}
                  >
                    Gender
                  </InputLabel>
                  <Select
                    value={formData.gender}
                    onChange={e => handleInputChange('gender', e.target.value)}
                    label="Gender"
                    sx={{
                      color: '#1f2937',
                      background: '#ffffff',
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#6b7280',
                        borderWidth: '1px',
                      },
                      '&:hover .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                      },
                      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                        borderWidth: '2px',
                      },
                      '& .MuiSelect-icon': {
                        color: '#6b7280',
                      },
                      '& .MuiInputLabel-root': {
                        color: '#e5e7eb',
                        fontWeight: 500,
                        fontSize: '0.95rem',
                        '&.Mui-focused': {
                          color: '#ef4444',
                          fontWeight: 600,
                        },
                      },
                    }}
                  >
                    {choices.gender_choices?.map(choice => (
                      <MenuItem key={choice.value} value={choice.value} sx={{ color: '#1f2937' }}>
                        {choice.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              {/* Demographics */}
              <Grid item xs={12}>
                <Typography
                  variant="h6"
                  sx={{
                    mb: 2,
                    mt: 2,
                    color: '#ef4444',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                  }}
                >
                  <WorkIcon sx={{ color: '#ef4444' }} /> Demographics
                </Typography>
                <Divider sx={{ mb: 3, borderColor: '#ef4444' }} />
              </Grid>
              <Grid item xs={12}>
                <FormControl fullWidth disabled={!editMode}>
                  <InputLabel
                    sx={{
                      color: '#ffffff',
                      fontWeight: 600,
                      fontSize: '1rem',
                      textShadow: '0 1px 2px rgba(0,0,0,0.5)',
                    }}
                  >
                    Occupation
                  </InputLabel>
                  <Select
                    value={formData.occupation}
                    onChange={e => handleInputChange('occupation', e.target.value)}
                    label="Occupation"
                    sx={{
                      color: '#1f2937',
                      background: '#ffffff',
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#6b7280',
                        borderWidth: '1px',
                      },
                      '&:hover .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                      },
                      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                        borderWidth: '2px',
                      },
                      '& .MuiSelect-icon': {
                        color: '#6b7280',
                      },
                      '& .MuiInputLabel-root': {
                        color: '#e5e7eb',
                        fontWeight: 500,
                        fontSize: '0.95rem',
                        '&.Mui-focused': {
                          color: '#ef4444',
                          fontWeight: 600,
                        },
                      },
                    }}
                  >
                    {choices.occupation_choices?.map(choice => (
                      <MenuItem key={choice.value} value={choice.value} sx={{ color: '#1f2937' }}>
                        {choice.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              {/* Location */}
              <Grid item xs={12}>
                <Typography
                  variant="h6"
                  sx={{
                    mb: 2,
                    mt: 2,
                    color: '#ef4444',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                  }}
                >
                  <LocationIcon sx={{ color: '#ef4444' }} /> Location
                </Typography>
                <Divider sx={{ mb: 3, borderColor: '#ef4444' }} />
              </Grid>
              <Grid item xs={12} sm={editMode ? 8 : 12}>
                <TextField
                  fullWidth
                  label="Location"
                  value={formData.location}
                  onChange={e => handleInputChange('location', e.target.value)}
                  placeholder="e.g., New York, NY, USA"
                  disabled={!editMode}
                  sx={{
                    '& .MuiInputBase-root': {
                      color: '#1f2937',
                      background: '#ffffff',
                      '&:hover .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                      },
                      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                        borderWidth: '2px',
                      },
                    },
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#6b7280',
                      borderWidth: '1px',
                    },
                    '& .MuiInputLabel-root': {
                      color: '#f3f4f6',
                      '&.Mui-focused': {
                        color: '#ef4444',
                      },
                    },
                    '& .MuiFormHelperText-root': {
                      color: '#d1d5db',
                      '&.Mui-error': {
                        color: '#f87171',
                      },
                    },
                    '& .MuiInputBase-input::placeholder': {
                      color: '#4b5563',
                      opacity: 1,
                    },
                  }}
                />
              </Grid>
              {editMode && (
                <Grid item xs={12} sm={4}>
                  <Button
                    fullWidth
                    variant="outlined"
                    onClick={handleAutoDetectLocation}
                    disabled={loadingLocation}
                    startIcon={loadingLocation ? <CircularProgress size={16} /> : <LocationIcon />}
                    sx={{
                      height: 56,
                      color: '#ef4444',
                      borderColor: '#ef4444',
                      background: 'rgba(239,68,68,0.05)',
                      fontWeight: 700,
                      '&:hover': { background: '#ef4444', color: '#fff', borderColor: '#ef4444' },
                    }}
                  >
                    {loadingLocation ? 'Detecting...' : 'Auto Detect'}
                  </Button>
                </Grid>
              )}
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Zip Code"
                  value={formData.zip_code}
                  onChange={e => handleInputChange('zip_code', e.target.value)}
                  placeholder="e.g., 10001"
                  disabled={!editMode}
                  sx={{
                    '& .MuiInputBase-root': {
                      color: '#1f2937',
                      background: '#ffffff',
                      '&:hover .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                      },
                      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                        borderWidth: '2px',
                      },
                    },
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#6b7280',
                      borderWidth: '1px',
                    },
                    '& .MuiInputLabel-root': {
                      color: '#f3f4f6',
                      '&.Mui-focused': {
                        color: '#ef4444',
                      },
                    },
                    '& .MuiFormHelperText-root': {
                      color: '#d1d5db',
                      '&.Mui-error': {
                        color: '#f87171',
                      },
                    },
                    '& .MuiInputBase-input::placeholder': {
                      color: '#4b5563',
                      opacity: 1,
                    },
                  }}
                />
              </Grid>
              {/* Bio */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Bio"
                  multiline
                  rows={4}
                  value={formData.bio}
                  onChange={e => handleInputChange('bio', e.target.value)}
                  placeholder="Tell us a bit about yourself..."
                  disabled={!editMode}
                  sx={{
                    '& .MuiInputBase-root': {
                      color: '#1f2937',
                      background: '#ffffff',
                      '&:hover .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                      },
                      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ef4444',
                        borderWidth: '2px',
                      },
                    },
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#6b7280',
                      borderWidth: '1px',
                    },
                    '& .MuiInputLabel-root': {
                      color: '#f3f4f6',
                      '&.Mui-focused': {
                        color: '#ef4444',
                      },
                    },
                    '& .MuiFormHelperText-root': {
                      color: '#d1d5db',
                      '&.Mui-error': {
                        color: '#f87171',
                      },
                    },
                    '& .MuiInputBase-input::placeholder': {
                      color: '#4b5563',
                      opacity: 1,
                    },
                  }}
                />
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default ProfileEdit;
