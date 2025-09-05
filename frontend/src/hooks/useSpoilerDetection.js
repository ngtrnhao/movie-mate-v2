import { useState, useCallback, useRef } from 'react';
import { detectSpoilers } from '../api/movieService';

export const useSpoilerDetection = (language = 'en', movieTitle = '') => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [detectionResult, setDetectionResult] = useState(null);
  const [error, setError] = useState(null);
  const debounceTimeoutRef = useRef(null);

  // Simplified analysis - background processing only
  const analyzeContentRealTime = useCallback(
    async content => {
      if (!content || content.trim().length < 10) {
        setDetectionResult(null);
        return;
      }

      setIsAnalyzing(true);
      setError(null);

      try {
        // Final comprehensive analysis
        const result = await detectSpoilers(content, language, movieTitle);
        setDetectionResult(result);
      } catch (err) {
        console.error('Spoiler detection error:', err);
        setError('Không thể phân tích nội dung. Vui lòng thử lại.');
        setDetectionResult(null);
      } finally {
        setIsAnalyzing(false);
      }
    },
    [language, movieTitle]
  );

  const analyzeContentDebounced = useCallback(
    content => {
      // Clear existing timeout
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }

      // Set new timeout for debounced analysis
      debounceTimeoutRef.current = setTimeout(() => {
        analyzeContentRealTime(content);
      }, 500); // Reduced delay for better responsiveness
    },
    [analyzeContentRealTime]
  );

  const clearAnalysis = useCallback(() => {
    setDetectionResult(null);
    setError(null);
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }
  }, []);

  const getRecommendationColor = useCallback(confidence => {
    if (confidence > 0.8) return 'red';
    if (confidence > 0.6) return 'orange';
    if (confidence > 0.4) return 'yellow';
    return 'green';
  }, []);

  const getRecommendationIcon = useCallback(confidence => {
    if (confidence > 0.8) return '🚨';
    if (confidence > 0.6) return '⚠️';
    if (confidence > 0.4) return '⚡';
    return '✅';
  }, []);

  const getRecommendationMessage = useCallback(result => {
    if (!result) return '';

    const { confidence, recommendation } = result;

    if (confidence > 0.8) {
      return 'Nội dung này có khả năng cao chứa spoiler. Bạn nên đánh dấu là spoiler.';
    } else if (confidence > 0.6) {
      return 'Nội dung này có thể chứa spoiler. Bạn có muốn đánh dấu là spoiler không?';
    } else if (confidence > 0.4) {
      return 'Nội dung này có một số dấu hiệu spoiler. Hãy kiểm tra lại.';
    } else {
      return 'Nội dung này không có dấu hiệu spoiler rõ ràng.';
    }
  }, []);

  // Get current result
  const getCurrentResult = () => {
    return detectionResult;
  };

  // Intelligent review classification logic
  const getReviewClassification = useCallback(result => {
    if (!result) return { action: 'auto_approve', reason: 'no_spoiler_detected' };

    const {
      confidence = 0,
      is_spoiler = false,
      detected_patterns = [],
      spoiler_indicators = [],
    } = result;

    // High confidence spoiler detection (90%+)
    if (confidence > 0.9) {
      return {
        action: 'auto_approve',
        reason: 'high_confidence_spoiler',
        autoMarkAsSpoiler: true,
        message: 'Review được tự động đánh dấu là spoiler và phê duyệt',
      };
    }

    // Medium-high confidence (60-80%) - needs user confirmation
    if (confidence > 0.6) {
      return {
        action: 'user_confirmation',
        reason: 'medium_high_confidence',
        suggestedAction: 'mark_as_spoiler',
        message: 'Review có khả năng cao chứa spoiler. Cần xác nhận từ người dùng.',
      };
    }

    // Medium confidence (40-60%) - send to moderation (background)
    if (confidence > 0.4) {
      return {
        action: 'moderation_required',
        reason: 'medium_confidence_uncertain',
        priority: 'medium',
        message: 'Review sẽ được kiểm tra bởi Moderator',
      };
    }

    // Low confidence (0-30%) - auto approve
    return {
      action: 'auto_approve',
      reason: 'low_confidence_no_spoiler',
      message: 'Review được tự động phê duyệt',
    };
  }, []);

  // Advanced classification based on content patterns
  const getAdvancedClassification = useCallback(
    (result, content) => {
      if (!result) return getReviewClassification(result);

      const { confidence = 0, detected_patterns = [], spoiler_indicators = [] } = result;
      const normalizedContent = (content || '').toLowerCase();

      // Check for explicit spoiler warnings
      const explicitWarnings = [
        'spoiler alert',
        'cảnh báo spoiler',
        'spoiler warning',
        'chứa spoiler',
        'có spoiler',
        'spoiler ahead',
      ];

      const hasExplicitWarning = explicitWarnings.some(warning =>
        normalizedContent.includes(warning)
      );

      // Check for major plot reveals
      const majorPlotReveals = [
        'kết thúc',
        'ending',
        'cuối phim',
        'end of movie',
        'chết',
        'dies',
        'death',
        'hy sinh',
        'sacrifice',
        'twist',
        'plot twist',
        'bất ngờ',
        'surprise',
      ];

      const hasMajorReveal = majorPlotReveals.some(reveal => normalizedContent.includes(reveal));

      // Check for character development spoilers
      const characterSpoilers = [
        'hóa ra',
        'turns out',
        'sự thật là',
        'truth is',
        'thân phận',
        'identity',
        'danh tính',
        'real identity',
      ];

      const hasCharacterSpoiler = characterSpoilers.some(spoiler =>
        normalizedContent.includes(spoiler)
      );

      // Classification logic
      if (hasExplicitWarning) {
        return {
          action: 'auto_approve',
          reason: 'explicit_spoiler_warning',
          autoMarkAsSpoiler: true,
          message: 'Review có cảnh báo spoiler rõ ràng - tự động đánh dấu',
        };
      }

      if (hasMajorReveal && confidence > 0.6) {
        return {
          action: 'moderation_required',
          reason: 'major_plot_reveal',
          priority: 'high',
          message: 'Review tiết lộ cốt truyện chính - sẽ được kiểm tra',
        };
      }

      if (hasCharacterSpoiler && confidence > 0.5) {
        return {
          action: 'user_confirmation',
          reason: 'character_development_spoiler',
          suggestedAction: 'mark_as_spoiler',
          message: 'Review tiết lộ phát triển nhân vật - cần xác nhận',
        };
      }

      // Check for review context indicators
      const reviewContext = [
        'review',
        'đánh giá',
        'opinion',
        'nhận xét',
        'cinematography',
        'quay phim',
        'acting',
        'diễn xuất',
      ];

      const hasReviewContext = reviewContext.some(context => normalizedContent.includes(context));

      // If content has review context and low spoiler indicators, auto approve
      if (hasReviewContext && confidence < 0.4) {
        return {
          action: 'auto_approve',
          reason: 'review_context_low_spoiler',
          message: 'Review có ngữ cảnh đánh giá và ít dấu hiệu spoiler',
        };
      }

      // Default to basic classification
      return getReviewClassification(result);
    },
    [getReviewClassification]
  );

  // Get moderation priority
  const getModerationPriority = useCallback((classification, currentResult) => {
    if (classification.action !== 'moderation_required') return null;

    const { reason } = classification;
    const confidence = currentResult?.confidence || 0;

    if (reason === 'major_plot_reveal' || confidence > 0.8) {
      return 'high';
    }

    if (reason === 'medium_confidence_uncertain' || confidence > 0.6) {
      return 'medium';
    }

    return 'low';
  }, []);

  return {
    // State
    isAnalyzing,
    detectionResult,
    error,

    // Actions
    analyzeContent: analyzeContentRealTime,
    analyzeContentDebounced,
    clearAnalysis,

    // Utilities
    getRecommendationColor,
    getRecommendationIcon,
    getRecommendationMessage,
    getCurrentResult,
    getReviewClassification,
    getAdvancedClassification,
    getModerationPriority,

    // Computed values
    isSpoiler: getCurrentResult()?.is_spoiler || false,
    confidence: getCurrentResult()?.confidence || 0,
    shouldShowWarning: getCurrentResult()?.confidence > 0.4,
    shouldAutoMark: getCurrentResult()?.confidence > 0.8,
  };
};
