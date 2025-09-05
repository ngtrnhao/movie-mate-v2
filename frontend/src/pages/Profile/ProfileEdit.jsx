import { useState, useEffect, useCallback } from 'react';
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
import { useTranslation } from '../../i18n/hooks/useTranslation';

const ProfileEdit = () => {
  const dispatch = useDispatch();
  const { user: currentUser } = useSelector(state => state.auth);
  const { t } = useTranslation('profile');

  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingLocation, setLoadingLocation] = useState(false);
  const [error, setError] = useState(null);
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

  // Common input field classes for dark theme
  const inputClasses = {
    base: 'w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-colors',
    disabled:
      'w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-md text-white placeholder-gray-400 opacity-90 cursor-not-allowed',
    label: 'block text-sm font-medium text-gray-300 mb-1',
    labelDisabled: 'block text-sm font-medium text-gray-400 mb-1 opacity-90',
    error: 'text-red-400 text-xs mt-1',
    helper: 'text-gray-400 text-xs mt-1',
  };

  // Safety check for translation function
  const safeT = (key, defaultValue = '') => {
    try {
      return t(key) || defaultValue;
    } catch (error) {
      console.warn(`Translation key not found: ${key}`, error);
      return defaultValue;
    }
  };

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

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
      setError(t('toasts.load_failed'));
      toast.error(t('toasts.load_failed'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  // Load initial data
  useEffect(() => {
    if (currentUser?.id) {
      loadData();
    }
  }, [currentUser?.id, loadData]);

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
      newErrors.first_name = t('errors.first_name_required_basic');
    }
    if (!formData.last_name.trim()) {
      newErrors.last_name = t('errors.last_name_required_basic');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      const response = await updateCurrentUserProfileAPI(formData);

      if (response.status === 'success') {
        // Update Redux store
        dispatch(updateUser(response.data));
        toast.success(t('toasts.update_success'));
        setEditMode(false);
        setErrors({});
      } else {
        toast.error(response.message || t('toasts.update_failed'));
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error(t('toasts.update_failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    // Reset form to original data
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

  const handleAvatarUpload = async event => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('avatar', file);

      const response = await uploadAvatarAPI(formData);
      if (response.status === 'success') {
        setFormData(prev => ({
          ...prev,
          avatar_url: response.data.avatar_url,
        }));
        toast.success(t('toasts.avatar_upload_success'));
      }
    } catch (error) {
      console.error('Error uploading avatar:', error);
      toast.error(t('toasts.avatar_upload_failed'));
    }
  };

  const handleAutoDetectLocation = async () => {
    try {
      setLoadingLocation(true);
      const response = await autoDetectLocationAPI();
      if (response.status === 'success') {
        setFormData(prev => ({
          ...prev,
          location: response.data.location || '',
          zip_code: response.data.zip_code || '',
        }));
        toast.success(t('toasts.location_detected'));
      }
    } catch (error) {
      console.error('Error detecting location:', error);
      toast.error(t('toasts.location_detection_failed'));
    } finally {
      setLoadingLocation(false);
    }
  };

  // Calculate completion percentage
  const completionPercentage = useCallback(() => {
    if (!userData) return 0;

    const fields = [
      'first_name',
      'last_name',
      'birth_date',
      'gender',
      'occupation',
      'location',
      'zip_code',
      'bio',
    ];

    const filledFields = fields.filter(
      field => userData[field] && userData[field].toString().trim()
    );
    return Math.round((filledFields.length / fields.length) * 100);
  }, [userData]);

  if (loading && !userData) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Profile Completion Status */}
        <div className="mb-6 bg-slate-800 rounded-lg shadow-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <svg className="w-6 h-6 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                clipRule="evenodd"
              />
            </svg>
            <h3 className="text-xl font-bold text-red-500">{t('page.completion.title')}</h3>
          </div>
          <div
            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-bold ${
              completionPercentage() === 100
                ? 'bg-green-500 text-white'
                : 'bg-yellow-500 text-white'
            }`}
          >
            {completionPercentage()}% {t('page.completion.complete')}
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div className="bg-red-500 h-2 rounded-full animate-pulse"></div>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="mb-6 bg-red-900 border border-red-500 rounded-lg p-4">
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {/* Main Profile Form */}
        <div className="bg-slate-900 rounded-lg shadow-lg p-8">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold text-red-500">{t('page.title')}</h1>
            {!editMode ? (
              <button
                onClick={() => setEditMode(true)}
                className="flex items-center gap-2 px-6 py-3 bg-red-500 text-white font-bold rounded-lg hover:bg-red-600 transition-colors shadow-lg"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
                {safeT('page.buttons.edit', 'Edit Profile')}
              </button>
            ) : (
              <div className="flex gap-3">
                <button
                  onClick={handleCancel}
                  disabled={loading}
                  className="px-6 py-3 border border-gray-600 text-white font-bold rounded-lg hover:bg-gray-700 hover:border-red-500 hover:text-red-500 transition-colors disabled:opacity-50"
                >
                  {safeT('page.buttons.cancel', 'Cancel')}
                </button>
                <button
                  onClick={handleSave}
                  disabled={loading}
                  className="flex items-center gap-2 px-6 py-3 bg-red-500 text-white font-bold rounded-lg hover:bg-red-600 transition-colors shadow-lg disabled:opacity-50"
                >
                  {loading ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                  {loading
                    ? safeT('page.buttons.saving', 'Saving...')
                    : safeT('page.buttons.save', 'Save Changes')}
                </button>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Avatar Section */}
            <div className="lg:col-span-1">
              <div className="flex flex-col items-center gap-4">
                <div className="relative">
                  <div className="w-32 h-32 bg-gray-700 rounded-full border-4 border-red-500 flex items-center justify-center text-4xl font-bold text-white">
                    {formData.avatar_url ? (
                      <img
                        src={formData.avatar_url}
                        alt="Avatar"
                        className="w-full h-full rounded-full object-cover"
                      />
                    ) : (
                      formData.first_name?.charAt(0) || formData.last_name?.charAt(0) || '?'
                    )}
                  </div>
                  {editMode && (
                    <label className="absolute bottom-0 right-0 bg-red-500 text-white p-2 rounded-full cursor-pointer hover:bg-red-600 transition-colors">
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                      </svg>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleAvatarUpload}
                        className="hidden"
                      />
                    </label>
                  )}
                </div>
                <h2 className="text-xl font-bold text-white text-center">
                  {formData.first_name} {formData.last_name}
                </h2>
                {formData.occupation && (
                  <div className="flex items-center gap-2 px-3 py-1 border border-red-500 text-red-500 rounded-full text-sm font-bold">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z"
                        clipRule="evenodd"
                      />
                      <path d="M2 13.692V16a2 2 0 002 2h12a2 2 0 002-2v-2.308A24.974 24.974 0 0110 15c-2.796 0-5.487-.46-8-1.308z" />
                    </svg>
                    {choices.occupation_choices?.find(opt => opt.value === formData.occupation)
                      ?.label || formData.occupation}
                  </div>
                )}
              </div>
            </div>

            {/* Form Fields */}
            <div className="lg:col-span-2">
              <div className="space-y-6">
                {/* Personal Information */}
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <svg className="w-6 h-6 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <h3 className="text-xl font-bold text-red-500">
                      {t('page.sections.personal')}
                    </h3>
                  </div>
                  <div className="border-b border-red-500 mb-6"></div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className={editMode ? inputClasses.label : inputClasses.labelDisabled}>
                        {t('page.labels.first_name')} *
                      </label>
                      <input
                        type="text"
                        value={formData.first_name}
                        onChange={e => handleInputChange('first_name', e.target.value)}
                        disabled={!editMode}
                        required
                        className={editMode ? inputClasses.base : inputClasses.disabled}
                        placeholder={t('page.placeholders.first_name')}
                      />
                      {errors.first_name && (
                        <p className={inputClasses.error}>{errors.first_name}</p>
                      )}
                    </div>

                    <div>
                      <label className={editMode ? inputClasses.label : inputClasses.labelDisabled}>
                        {t('page.labels.last_name')} *
                      </label>
                      <input
                        type="text"
                        value={formData.last_name}
                        onChange={e => handleInputChange('last_name', e.target.value)}
                        disabled={!editMode}
                        required
                        className={editMode ? inputClasses.base : inputClasses.disabled}
                        placeholder={t('page.placeholders.last_name')}
                      />
                      {errors.last_name && <p className={inputClasses.error}>{errors.last_name}</p>}
                    </div>

                    <div>
                      <label className={editMode ? inputClasses.label : inputClasses.labelDisabled}>
                        {t('page.labels.birth_date')}
                      </label>
                      <input
                        type="date"
                        value={formData.birth_date}
                        onChange={e => handleInputChange('birth_date', e.target.value)}
                        disabled={!editMode}
                        className={editMode ? inputClasses.base : inputClasses.disabled}
                      />
                      <p className={inputClasses.helper}>{t('page.helper.birthdate_purpose')}</p>
                    </div>

                    <div>
                      <label className={editMode ? inputClasses.label : inputClasses.labelDisabled}>
                        {t('page.labels.gender')}
                      </label>
                      <select
                        value={formData.gender}
                        onChange={e => handleInputChange('gender', e.target.value)}
                        disabled={!editMode}
                        className={editMode ? inputClasses.base : inputClasses.disabled}
                      >
                        <option value="">{t('page.placeholders.gender')}</option>
                        {choices.gender_choices?.map(choice => (
                          <option key={choice.value} value={choice.value}>
                            {t(`options.gender.${choice.value}`, { defaultValue: choice.label })}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                {/* Demographics */}
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <svg className="w-6 h-6 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z"
                        clipRule="evenodd"
                      />
                      <path d="M2 13.692V16a2 2 0 002 2h12a2 2 0 002-2v-2.308A24.974 24.974 0 0110 15c-2.796 0-5.487-.46-8-1.308z" />
                    </svg>
                    <h3 className="text-xl font-bold text-red-500">
                      {t('page.sections.demographics')}
                    </h3>
                  </div>
                  <div className="border-b border-red-500 mb-6"></div>

                  <div className="space-y-4">
                    <div>
                      <label className={editMode ? inputClasses.label : inputClasses.labelDisabled}>
                        {t('page.labels.occupation')}
                      </label>
                      <select
                        value={formData.occupation}
                        onChange={e => handleInputChange('occupation', e.target.value)}
                        disabled={!editMode}
                        className={editMode ? inputClasses.base : inputClasses.disabled}
                      >
                        <option value="">{t('page.placeholders.occupation')}</option>
                        {choices.occupation_choices?.map(choice => (
                          <option key={choice.value} value={choice.value}>
                            {t(`options.occupation.${choice.value}`, {
                              defaultValue: choice.label,
                            })}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Location */}
                    <div>
                      <div className="flex items-center gap-2 mb-4">
                        <svg
                          className="w-6 h-6 text-red-500"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                            clipRule="evenodd"
                          />
                        </svg>
                        <h3 className="text-xl font-bold text-red-500">
                          {t('page.sections.location')}
                        </h3>
                      </div>
                      <div className="border-b border-red-500 mb-6"></div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="md:col-span-2">
                          <label
                            className={editMode ? inputClasses.label : inputClasses.labelDisabled}
                          >
                            {t('page.labels.location')}
                          </label>
                          <input
                            type="text"
                            value={formData.location}
                            onChange={e => handleInputChange('location', e.target.value)}
                            disabled={!editMode}
                            className={editMode ? inputClasses.base : inputClasses.disabled}
                            placeholder={t('page.placeholders.location')}
                          />
                        </div>
                        {editMode && (
                          <div className="flex items-end">
                            <button
                              onClick={handleAutoDetectLocation}
                              disabled={loadingLocation}
                              className="w-full px-4 py-2 border border-red-500 text-red-500 font-bold rounded-md hover:bg-red-500 hover:text-white transition-colors disabled:opacity-50"
                            >
                              {loadingLocation ? (
                                <div className="flex items-center justify-center">
                                  <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
                                </div>
                              ) : (
                                <span>{t('page.buttons.auto_detect') || 'Auto Detect'}</span>
                              )}
                            </button>
                          </div>
                        )}
                      </div>

                      <div className="mt-4">
                        <label
                          className={editMode ? inputClasses.label : inputClasses.labelDisabled}
                        >
                          {t('page.labels.zip_code')}
                        </label>
                        <input
                          type="text"
                          value={formData.zip_code}
                          onChange={e => handleInputChange('zip_code', e.target.value)}
                          disabled={!editMode}
                          className={editMode ? inputClasses.base : inputClasses.disabled}
                          placeholder={t('page.placeholders.zip_code')}
                        />
                      </div>
                    </div>

                    {/* Bio */}
                    <div>
                      <label className={editMode ? inputClasses.label : inputClasses.labelDisabled}>
                        {t('page.labels.bio')}
                      </label>
                      <textarea
                        value={formData.bio}
                        onChange={e => handleInputChange('bio', e.target.value)}
                        disabled={!editMode}
                        rows={4}
                        className={editMode ? inputClasses.base : inputClasses.disabled}
                        placeholder={t('page.placeholders.bio')}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileEdit;
