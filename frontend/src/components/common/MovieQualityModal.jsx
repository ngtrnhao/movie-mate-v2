import { useState, useEffect } from 'react';
import { Dialog, Transition, Tab } from '@headlessui/react';
import { Fragment } from 'react';
import {
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  StarIcon,
  ChartBarIcon,
  DocumentCheckIcon,
  ClockIcon,
  UserIcon,
  PhotoIcon,
  FilmIcon,
  SpeakerWaveIcon,
  GlobeAltIcon,
  TagIcon,
  PencilIcon,
  ArrowRightIcon,
  BugAntIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

const MovieQualityModal = ({
  isOpen,
  onClose,
  movie,
  onQualityUpdate,
  onIssueResolve,
  userRole = 'admin',
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [qualityNotes, setQualityNotes] = useState('');
  const [selectedIssues, setSelectedIssues] = useState([]);

  // Get quality metrics with fallback and backend data mapping
  const qualityMetrics = movie?.quality_metrics || {};

  // Convert backend quality issues from string array to object format
  const processQualityIssues = issues => {
    if (!Array.isArray(issues)) return [];

    return issues.map((issue, index) => ({
      category: 'Quality Issue',
      description: issue,
      priority: index === 0 ? 'high' : index === 1 ? 'medium' : 'low',
      suggested_fix: `Address: ${issue}`,
    }));
  };

  // Convert backend quality suggestions from string array to object format
  const processQualitySuggestions = suggestions => {
    if (!Array.isArray(suggestions)) return [];

    return suggestions.map((suggestion, index) => ({
      category: 'Improvement',
      description: suggestion,
      priority: index <= 1 ? 'medium' : 'low',
      expected_impact: index <= 1 ? 'High impact on quality score' : 'Moderate improvement',
    }));
  };

  // Map backend scores to component breakdown format
  const mapBackendScoresToBreakdown = metrics => {
    const backendScores = {
      basic_info_score: parseFloat(metrics.basic_info_score) || 0,
      visual_assets_score: parseFloat(metrics.visual_assets_score) || 0,
      metadata_richness_score: parseFloat(metrics.metadata_richness_score) || 0,
      rating_validity_score: parseFloat(metrics.rating_validity_score) || 0,
    };

    // Map backend scores to component keys
    return {
      poster_quality: backendScores.visual_assets_score,
      metadata_completeness: backendScores.metadata_richness_score,
      content_accuracy: backendScores.rating_validity_score,
      technical_quality: backendScores.basic_info_score,
      user_engagement: backendScores.rating_validity_score,
      content_freshness: backendScores.basic_info_score,
    };
  };

  // Process all quality data
  const processedQualityMetrics = {
    ...qualityMetrics,
    quality_score: parseFloat(qualityMetrics.quality_score) || 0,
    content_completeness: parseFloat(qualityMetrics.content_completeness) || 0,
    quality_issues: processQualityIssues(qualityMetrics.quality_issues),
    quality_suggestions: processQualitySuggestions(qualityMetrics.quality_suggestions),
    overall_quality_rating: qualityMetrics.overall_quality_rating || 'Not Rated',
    completion_status: qualityMetrics.completion_status || 'Unknown',
    last_quality_check: qualityMetrics.last_quality_check || new Date().toISOString(),
    assessed_by: qualityMetrics.auto_calculated ? 'System Auto-Assessment' : 'Manual Assessment',
    assessment_notes:
      qualityMetrics.assessment_notes ||
      `Quality assessment for ${movie?.title || 'this movie'}. Overall quality rating: ${qualityMetrics.overall_quality_rating || 'Not Rated'}.`,
  };

  const qualityBreakdown = mapBackendScoresToBreakdown(qualityMetrics);

  useEffect(() => {
    if (isOpen && movie) {
      console.log('MovieQualityModal opened for:', movie.title);
      console.log('Quality metrics:', processedQualityMetrics);
      console.log('Quality breakdown:', qualityBreakdown);
      setQualityNotes(processedQualityMetrics.assessment_notes || '');
      setSelectedIssues([]);
      setEditMode(false);
    }
  }, [isOpen, movie, processedQualityMetrics.assessment_notes]);

  const getQualityColor = score => {
    const numScore = parseFloat(score) || 0;
    if (numScore >= 8) return 'text-green-600 bg-green-100';
    if (numScore >= 6) return 'text-blue-600 bg-blue-100';
    if (numScore >= 4) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getCompletionColor = percentage => {
    const pct = parseFloat(percentage) || 0;
    if (pct >= 90) return 'text-green-600 bg-green-100';
    if (pct >= 70) return 'text-blue-600 bg-blue-100';
    if (pct >= 50) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getRatingBadgeColor = rating => {
    switch (rating) {
      case 'Excellent':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'Good':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'Fair':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'Poor':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPriorityColor = priority => {
    switch (priority) {
      case 'critical':
        return 'text-red-600 bg-red-100 border-red-200';
      case 'high':
        return 'text-orange-600 bg-orange-100 border-orange-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'low':
        return 'text-blue-600 bg-blue-100 border-blue-200';
      default:
        return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const handleSaveQuality = async () => {
    setLoading(true);
    try {
      const qualityData = {
        assessment_notes: qualityNotes,
        resolved_issues: selectedIssues,
        assessed_by: userRole,
        assessment_date: new Date().toISOString(),
      };

      await onQualityUpdate(movie.id, qualityData);
      setEditMode(false);
    } catch (error) {
      console.error('Error updating quality:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResolveIssue = async issueIndex => {
    try {
      await onIssueResolve(movie.id, issueIndex);
    } catch (error) {
      console.error('Error resolving issue:', error);
    }
  };

  const toggleIssueSelection = issueIndex => {
    setSelectedIssues(prev =>
      prev.includes(issueIndex) ? prev.filter(i => i !== issueIndex) : [...prev, issueIndex]
    );
  };

  const qualityBreakdownItems = [
    {
      key: 'poster_quality',
      label: 'Poster Quality',
      icon: PhotoIcon,
      description: 'Image resolution, aspect ratio, content relevance',
    },
    {
      key: 'metadata_completeness',
      label: 'Metadata Completeness',
      icon: DocumentCheckIcon,
      description: 'Title, description, genre, cast, crew information',
    },
    {
      key: 'content_accuracy',
      label: 'Content Accuracy',
      icon: CheckCircleIcon,
      description: 'Correct information, verified details',
    },
    {
      key: 'technical_quality',
      label: 'Technical Quality',
      icon: ChartBarIcon,
      description: 'Video quality, audio, subtitles, encoding',
    },
    {
      key: 'user_engagement',
      label: 'User Engagement',
      icon: UserIcon,
      description: 'User ratings, reviews, watch completion',
    },
    {
      key: 'content_freshness',
      label: 'Content Freshness',
      icon: ClockIcon,
      description: 'Release date relevance, trending status',
    },
  ];

  const tabs = [
    { name: 'Overview', icon: ChartBarIcon },
    { name: 'Quality Breakdown', icon: StarIcon },
    { name: 'Issues & Suggestions', icon: BugAntIcon },
    { name: 'Assessment', icon: DocumentCheckIcon },
  ];

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Quality Score & Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Quality Score</h3>
            {processedQualityMetrics.quality_score && (
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getQualityColor(processedQualityMetrics.quality_score)}`}
              >
                {parseFloat(processedQualityMetrics.quality_score).toFixed(1)}/10
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {processedQualityMetrics.quality_score ? (
              <>
                <div className="flex space-x-1">
                  {[...Array(5)].map((_, i) => (
                    <StarIconSolid
                      key={i}
                      className={`h-5 w-5 ${
                        i < Math.round(parseFloat(processedQualityMetrics.quality_score || 0) / 2)
                          ? 'text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    />
                  ))}
                </div>
                <span className="text-2xl font-bold text-gray-900">
                  {parseFloat(processedQualityMetrics.quality_score).toFixed(1)}
                </span>
              </>
            ) : (
              <span className="text-gray-500 italic">Not assessed</span>
            )}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Completeness</h3>
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getCompletionColor(processedQualityMetrics.content_completeness)}`}
            >
              {parseFloat(processedQualityMetrics.content_completeness).toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-300 ${
                parseFloat(processedQualityMetrics.content_completeness) >= 70
                  ? 'bg-green-500'
                  : parseFloat(processedQualityMetrics.content_completeness) >= 50
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
              }`}
              style={{ width: `${parseFloat(processedQualityMetrics.content_completeness || 0)}%` }}
            />
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Overall Rating</h3>
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getRatingBadgeColor(processedQualityMetrics.overall_quality_rating)}`}
            >
              {processedQualityMetrics.overall_quality_rating}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            {processedQualityMetrics.minimum_quality_met ? (
              <CheckCircleIcon className="h-6 w-6 text-green-500" />
            ) : (
              <ExclamationTriangleIcon className="h-6 w-6 text-red-500" />
            )}
            <span
              className={`text-sm font-medium ${processedQualityMetrics.minimum_quality_met ? 'text-green-700' : 'text-red-700'}`}
            >
              {processedQualityMetrics.minimum_quality_met ? 'Meets Standards' : 'Below Standards'}
            </span>
          </div>
        </div>
      </div>

      {/* Status Summary */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quality Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Status</h4>
            <p className="text-sm text-gray-600">
              Completion Status:{' '}
              <span className="font-medium">{processedQualityMetrics.completion_status}</span>
            </p>
            {processedQualityMetrics.last_quality_check && (
              <p className="text-sm text-gray-600">
                Last Check:{' '}
                <span className="font-medium">
                  {new Date(processedQualityMetrics.last_quality_check).toLocaleDateString()}
                </span>
              </p>
            )}
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Issues Summary</h4>
            <p className="text-sm text-gray-600">
              Active Issues:{' '}
              <span className="font-medium text-red-600">
                {processedQualityMetrics.quality_issues?.length || 0}
              </span>
            </p>
            <p className="text-sm text-gray-600">
              Suggestions:{' '}
              <span className="font-medium text-blue-600">
                {processedQualityMetrics.quality_suggestions?.length || 0}
              </span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderQualityBreakdownTab = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {qualityBreakdownItems.map(item => {
          const Icon = item.icon;
          const score = qualityBreakdown[item.key] || 0;
          const percentage = (score / 10) * 100;

          return (
            <div key={item.key} className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <Icon className="h-6 w-6 text-gray-400" />
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">{item.label}</h3>
                    <p className="text-xs text-gray-500">{item.description}</p>
                  </div>
                </div>
                <span
                  className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getQualityColor(score)}`}
                >
                  {parseFloat(score).toFixed(1)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    score >= 8
                      ? 'bg-green-500'
                      : score >= 6
                        ? 'bg-blue-500'
                        : score >= 4
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                  }`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderIssuesTab = () => (
    <div className="space-y-6">
      {/* Quality Issues */}
      <div>
        <div className="flex items-center space-x-2 mb-4">
          <BugAntIcon className="h-5 w-5 text-red-500" />
          <h3 className="text-lg font-medium text-gray-900">Quality Issues</h3>
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
            {processedQualityMetrics.quality_issues?.length || 0}
          </span>
        </div>

        {processedQualityMetrics.quality_issues?.length > 0 ? (
          <div className="space-y-3">
            {processedQualityMetrics.quality_issues.map((issue, index) => (
              <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium border ${getPriorityColor(issue.priority)}`}
                      >
                        {issue.priority}
                      </span>
                      <span className="text-sm font-medium text-gray-900">{issue.category}</span>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{issue.description}</p>
                    {issue.suggested_fix && (
                      <p className="text-sm text-blue-600">
                        <span className="font-medium">Suggested fix:</span> {issue.suggested_fix}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    {editMode && (
                      <input
                        type="checkbox"
                        checked={selectedIssues.includes(index)}
                        onChange={() => toggleIssueSelection(index)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    )}
                    <button
                      onClick={() => handleResolveIssue(index)}
                      className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-green-700 bg-green-100 hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                    >
                      Resolve
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <CheckCircleIcon className="h-12 w-12 mx-auto mb-2 text-green-400" />
            <p>No quality issues found</p>
          </div>
        )}
      </div>

      {/* Quality Suggestions */}
      <div>
        <div className="flex items-center space-x-2 mb-4">
          <LightBulbIcon className="h-5 w-5 text-yellow-500" />
          <h3 className="text-lg font-medium text-gray-900">Improvement Suggestions</h3>
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            {processedQualityMetrics.quality_suggestions?.length || 0}
          </span>
        </div>

        {processedQualityMetrics.quality_suggestions?.length > 0 ? (
          <div className="space-y-3">
            {processedQualityMetrics.quality_suggestions.map((suggestion, index) => (
              <div key={index} className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-sm font-medium text-gray-900">
                        {suggestion.category}
                      </span>
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium border ${getPriorityColor(suggestion.priority)}`}
                      >
                        {suggestion.priority}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{suggestion.description}</p>
                    {suggestion.expected_impact && (
                      <p className="text-sm text-green-600">
                        <span className="font-medium">Expected impact:</span>{' '}
                        {suggestion.expected_impact}
                      </p>
                    )}
                  </div>
                  <ArrowRightIcon className="h-4 w-4 text-gray-400 mt-1" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <LightBulbIcon className="h-12 w-12 mx-auto mb-2 text-yellow-400" />
            <p>No improvement suggestions available</p>
          </div>
        )}
      </div>
    </div>
  );

  const renderAssessmentTab = () => (
    <div className="space-y-6">
      {/* Assessment Information */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quality Assessment</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Assessed By</label>
            <p className="text-sm text-gray-900">
              {processedQualityMetrics.assessed_by || 'Not assessed yet'}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Last Assessment Date
            </label>
            <p className="text-sm text-gray-900">
              {processedQualityMetrics.last_quality_check
                ? new Date(processedQualityMetrics.last_quality_check).toLocaleString()
                : 'Not assessed yet'}
            </p>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Assessment Notes</label>
          {editMode ? (
            <textarea
              value={qualityNotes}
              onChange={e => setQualityNotes(e.target.value)}
              rows={6}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              placeholder="Enter quality assessment notes, observations, and recommendations..."
            />
          ) : (
            <div className="min-h-[120px] p-3 border border-gray-300 rounded-md bg-gray-50 text-sm text-gray-700">
              {processedQualityMetrics.assessment_notes || 'No assessment notes available'}
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3">
        {editMode ? (
          <>
            <button
              onClick={() => setEditMode(false)}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveQuality}
              disabled={loading}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Save Assessment'}
            </button>
          </>
        ) : (
          <button
            onClick={() => setEditMode(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <PencilIcon className="h-4 w-4 mr-2" />
            Edit Assessment
          </button>
        )}
      </div>
    </div>
  );

  return (
    <Transition.Root show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white px-4 pt-5 pb-4 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-6xl sm:p-6">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-gray-200 pb-4 mb-6">
                  <div className="flex items-center space-x-3">
                    <ChartBarIcon className="h-6 w-6 text-blue-500" />
                    <div>
                      <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-gray-900">
                        Quality Management - {movie?.title}
                      </Dialog.Title>
                      <p className="text-sm text-gray-500">
                        Comprehensive quality assessment and issue resolution
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    onClick={onClose}
                  >
                    <span className="sr-only">Close</span>
                    <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                  </button>
                </div>

                {/* Tabs */}
                <Tab.Group selectedIndex={activeTab} onChange={setActiveTab}>
                  <Tab.List className="flex space-x-1 rounded-xl bg-gray-100 p-1 mb-6">
                    {tabs.map((tab, index) => {
                      const Icon = tab.icon;
                      return (
                        <Tab
                          key={tab.name}
                          className={({ selected }) =>
                            `w-full rounded-lg py-2.5 text-sm font-medium leading-5 ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2 ${
                              selected
                                ? 'bg-white text-blue-700 shadow'
                                : 'text-gray-600 hover:bg-white/50 hover:text-gray-900'
                            }`
                          }
                        >
                          <div className="flex items-center justify-center space-x-2">
                            <Icon className="h-4 w-4" />
                            <span>{tab.name}</span>
                          </div>
                        </Tab>
                      );
                    })}
                  </Tab.List>

                  <Tab.Panels>
                    <Tab.Panel>{renderOverviewTab()}</Tab.Panel>
                    <Tab.Panel>{renderQualityBreakdownTab()}</Tab.Panel>
                    <Tab.Panel>{renderIssuesTab()}</Tab.Panel>
                    <Tab.Panel>{renderAssessmentTab()}</Tab.Panel>
                  </Tab.Panels>
                </Tab.Group>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
};

export default MovieQualityModal;
