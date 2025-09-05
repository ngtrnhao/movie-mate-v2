import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg, F
from django.core.cache import cache
from ..models import ModerationConfig, ModerationFeedback, MovieReview
from .spoiler_detection_service import SpoilerDetectionService

logger = logging.getLogger(__name__)


class ModerationLearningService:
    """
    Service for processing moderator feedback and improving spoiler detection accuracy
    through machine learning techniques
    """

    def __init__(self):
        self.spoiler_detector = SpoilerDetectionService()

    def process_feedback(self, feedback: ModerationFeedback) -> Dict:
        """
        Process a single piece of moderator feedback to update the learning system

        Args:
            feedback: ModerationFeedback instance with moderator's assessment

        Returns:
            Dict with processing results and learning impact
        """
        try:
            # Calculate learning impact score
            impact_score = feedback.calculate_learning_impact()

            # Mark feedback as processed (but do NOT set used_for_learning yet)
            feedback.learning_impact_score = impact_score
            feedback.save(update_fields=['learning_impact_score'])

            # Get current configuration
            config = ModerationConfig.get_active_config()
            if not config or not config.learning_enabled:
                feedback.used_for_learning = True
                feedback.save(update_fields=['used_for_learning'])
                return {
                    'success': True,
                    'message': 'Feedback recorded but learning is disabled',
                    'impact_score': impact_score
                }

            # Check if we have enough feedback to trigger learning (count ALL feedback in recent window)
            recent_feedback = self._get_recent_feedback_batch(config.min_feedback_count)
            recent_feedback_count = recent_feedback.count()

            if recent_feedback_count >= config.min_feedback_count:
                # Trigger threshold adjustment analysis
                adjustment_result = self.suggest_threshold_adjustments()

                # Auto-apply adjustments if confidence is high enough
                if (adjustment_result.get('confidence', 0) > 0.8 and config.learning_enabled):
                    self._apply_threshold_adjustments(adjustment_result['suggestions'])

                # Mark all feedback in this batch as used_for_learning (fix for Django slice update)
                ids = list(recent_feedback.values_list('id', flat=True))
                ModerationFeedback.objects.filter(id__in=ids).update(used_for_learning=True)

                return {
                    'success': True,
                    'message': 'Feedback processed and learning triggered',
                    'impact_score': impact_score,
                    'learning_triggered': True,
                    'adjustment_result': adjustment_result
                }

            # Nếu chưa đủ batch, chỉ đánh dấu feedback hiện tại là used_for_learning=False (chờ batch đủ mới set True)
            return {
                'success': True,
                'message': 'Feedback processed, waiting for more data',
                'impact_score': impact_score,
                'learning_triggered': False,
                'feedback_needed': config.min_feedback_count - recent_feedback_count
            }

        except Exception as e:
            logger.error(f"Error processing feedback {feedback.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def calculate_accuracy_metrics(self, days: int = 30) -> Dict:
        """
        Calculate comprehensive accuracy metrics for the spoiler detection system

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Dict with detailed accuracy metrics
        """
        try:
            # Get feedback data for the specified period
            metrics = ModerationFeedback.get_accuracy_metrics(days)

            # Add confidence-based breakdown
            confidence_breakdown = self._calculate_confidence_breakdown(days)
            metrics['confidence_breakdown'] = confidence_breakdown

            # Calculate trend analysis
            trend_analysis = self._calculate_accuracy_trends(days)
            metrics['trends'] = trend_analysis

            # Add performance by moderator
            moderator_performance = self._calculate_moderator_performance(days)
            metrics['moderator_performance'] = moderator_performance

            # Cache results for performance
            cache_key = f"accuracy_metrics_{days}d"
            cache.set(cache_key, metrics, timeout=3600)  # Cache for 1 hour

            return metrics

        except Exception as e:
            logger.error(f"Error calculating accuracy metrics: {str(e)}")
            return {
                'error': str(e),
                'accuracy': 0.0,
                'total_feedback': 0
            }

    def suggest_threshold_adjustments(self) -> Dict:
        """
        Analyze recent feedback to suggest optimal threshold adjustments

        Returns:
            Dict with suggested threshold adjustments and confidence level
        """
        try:
            config = ModerationConfig.get_active_config()
            if not config:
                return {'error': 'No active configuration found'}

            # Analyze feedback patterns near current thresholds
            threshold_analysis = self._analyze_threshold_performance()

            # Calculate optimal thresholds using feedback data
            suggestions = self._calculate_optimal_thresholds(threshold_analysis)

            # Calculate confidence in suggestions
            confidence = self._calculate_suggestion_confidence(threshold_analysis)

            return {
                'success': True,
                'current_thresholds': {
                    'auto_mark': config.auto_mark_threshold,
                    'flag_for_review': config.flag_for_review_threshold,
                    'suggest_warning': config.suggest_warning_threshold
                },
                'suggestions': suggestions,
                'confidence': confidence,
                'analysis': threshold_analysis,
                'recommendation': self._generate_threshold_recommendation(suggestions, confidence)
            }

        except Exception as e:
            logger.error(f"Error suggesting threshold adjustments: {str(e)}")
            return {'error': str(e)}

    def update_detection_weights(self) -> Dict:
        """
        Update detection algorithm weights based on feedback patterns

        Returns:
            Dict with update results
        """
        try:
            # Analyze which patterns are most/least effective
            pattern_analysis = self._analyze_detection_patterns()

            # Update keyword weights based on feedback
            keyword_weights = self._calculate_keyword_weights(pattern_analysis)

            # Cache updated weights
            cache.set('spoiler_detection_weights', keyword_weights, timeout=86400)  # 24 hours

            return {
                'success': True,
                'updated_weights': keyword_weights,
                'pattern_analysis': pattern_analysis
            }

        except Exception as e:
            logger.error(f"Error updating detection weights: {str(e)}")
            return {'error': str(e)}

    def get_learning_status(self) -> Dict:
        """
        Get current status of the learning system

        Returns:
            Dict with learning system status and metrics
        """
        try:
            config = ModerationConfig.get_active_config()

            # Recent feedback statistics
            recent_feedback = self._get_recent_feedback_stats()

            # Learning effectiveness metrics
            effectiveness = self._calculate_learning_effectiveness()

            return {
                'learning_enabled': config.learning_enabled if config else False,
                'recent_feedback': recent_feedback,
                'effectiveness': effectiveness,
                'last_adjustment': self._get_last_threshold_adjustment(),
                'next_learning_cycle': self._get_next_learning_cycle()
            }

        except Exception as e:
            logger.error(f"Error getting learning status: {str(e)}")
            return {'error': str(e)}

    def _get_recent_feedback_count(self, days: int = 7) -> int:
        """Get count of recent feedback for learning threshold"""
        start_date = timezone.now() - timedelta(days=days)
        return ModerationFeedback.objects.filter(
            created_at__gte=start_date,
            used_for_learning=False
        ).count()

    def _get_recent_feedback_batch(self, min_count: int, days: int = 7):
        """Get the most recent batch of feedback for learning trigger"""
        start_date = timezone.now() - timedelta(days=days)
        return ModerationFeedback.objects.filter(
            created_at__gte=start_date
        ).order_by('-created_at')[:min_count]

    def _calculate_confidence_breakdown(self, days: int) -> Dict:
        """Calculate accuracy breakdown by confidence ranges"""
        start_date = timezone.now() - timedelta(days=days)

        feedback_queryset = ModerationFeedback.objects.filter(
            created_at__gte=start_date
        )

        confidence_ranges = {
            'high': (0.8, 1.0),
            'medium-high': (0.6, 0.8),
            'medium': (0.4, 0.6),
            'low': (0.0, 0.4)
        }

        breakdown = {}
        for range_name, (min_conf, max_conf) in confidence_ranges.items():
            range_feedback = feedback_queryset.filter(
                original_confidence__gte=min_conf,
                original_confidence__lt=max_conf
            )

            total = range_feedback.count()
            correct = range_feedback.filter(is_spoiler_correct=True).count()

            breakdown[range_name] = {
                'total': total,
                'correct': correct,
                'accuracy': round(correct / total, 3) if total > 0 else 0.0
            }

        return breakdown

    def _calculate_accuracy_trends(self, days: int) -> Dict:
        """Calculate accuracy trends over time"""
        start_date = timezone.now() - timedelta(days=days)

        # Weekly accuracy calculation
        weekly_accuracy = []
        for week in range(min(days // 7, 4)):  # Max 4 weeks
            week_start = start_date + timedelta(weeks=week)
            week_end = week_start + timedelta(weeks=1)

            week_feedback = ModerationFeedback.objects.filter(
                created_at__gte=week_start,
                created_at__lt=week_end
            )

            total = week_feedback.count()
            correct = week_feedback.filter(is_spoiler_correct=True).count()
            accuracy = correct / total if total > 0 else 0.0

            weekly_accuracy.append({
                'week': week + 1,
                'accuracy': round(accuracy, 3),
                'total_feedback': total
            })

        return {
            'weekly_accuracy': weekly_accuracy,
            'trend': self._calculate_trend_direction(weekly_accuracy)
        }

    def _calculate_moderator_performance(self, days: int) -> List[Dict]:
        """Calculate performance metrics by moderator"""
        start_date = timezone.now() - timedelta(days=days)

        moderator_stats = ModerationFeedback.objects.filter(
            created_at__gte=start_date
        ).values('moderator__username').annotate(
            total_feedback=Count('id'),
            avg_time_spent=Avg('time_spent_seconds'),
            correct_decisions=Count('id', filter=Q(is_spoiler_correct=True))
        ).order_by('-total_feedback')

        performance_list = []
        for stats in moderator_stats:
            accuracy = (stats['correct_decisions'] / stats['total_feedback']
                       if stats['total_feedback'] > 0 else 0.0)

            performance_list.append({
                'moderator': stats['moderator__username'],
                'total_feedback': stats['total_feedback'],
                'accuracy': round(accuracy, 3),
                'avg_time_seconds': round(stats['avg_time_spent'] or 0, 1)
            })

        return performance_list

    def _analyze_threshold_performance(self) -> Dict:
        """Analyze how well current thresholds are performing"""
        config = ModerationConfig.get_active_config()
        if not config:
            return {}

        # Get recent feedback near threshold boundaries
        threshold_margin = 0.1  # ±0.1 around thresholds

        thresholds = {
            'auto_mark': config.auto_mark_threshold,
            'flag_for_review': config.flag_for_review_threshold,
            'suggest_warning': config.suggest_warning_threshold
        }

        analysis = {}
        for threshold_name, threshold_value in thresholds.items():
            near_threshold = ModerationFeedback.objects.filter(
                original_confidence__gte=threshold_value - threshold_margin,
                original_confidence__lte=threshold_value + threshold_margin
            )

            total = near_threshold.count()
            correct = near_threshold.filter(is_spoiler_correct=True).count()

            analysis[threshold_name] = {
                'threshold': threshold_value,
                'samples_near_threshold': total,
                'accuracy_near_threshold': correct / total if total > 0 else 0.0,
                'false_positives': near_threshold.filter(
                    feedback_type='false_positive'
                ).count(),
                'false_negatives': near_threshold.filter(
                    feedback_type='missed_spoiler'
                ).count()
            }

        return analysis

    def _calculate_optimal_thresholds(self, threshold_analysis: Dict) -> Dict:
        """Calculate optimal threshold values based on analysis"""
        config = ModerationConfig.get_active_config()
        current_thresholds = {
            'auto_mark': config.auto_mark_threshold,
            'flag_for_review': config.flag_for_review_threshold,
            'suggest_warning': config.suggest_warning_threshold
        }

        suggestions = {}

        # Simple heuristic-based adjustment
        for threshold_name, analysis in threshold_analysis.items():
            current_value = current_thresholds[threshold_name]
            accuracy = analysis['accuracy_near_threshold']
            false_positives = analysis['false_positives']
            false_negatives = analysis['false_negatives']

            # Adjust based on error types
            if false_positives > false_negatives:
                # Too many false positives, increase threshold
                suggested_value = min(current_value + 0.05, 0.95)
            elif false_negatives > false_positives:
                # Too many false negatives, decrease threshold
                suggested_value = max(current_value - 0.05, 0.05)
            else:
                # Balanced or no adjustment needed
                suggested_value = current_value

            suggestions[threshold_name] = {
                'current': current_value,
                'suggested': round(suggested_value, 2),
                'change': round(suggested_value - current_value, 2),
                'reasoning': self._generate_adjustment_reasoning(
                    false_positives, false_negatives, accuracy
                )
            }

        return suggestions

    def _calculate_suggestion_confidence(self, threshold_analysis: Dict) -> float:
        """Calculate confidence level in threshold suggestions"""
        total_samples = sum(
            analysis['samples_near_threshold']
            for analysis in threshold_analysis.values()
        )

        # Base confidence on sample size and accuracy
        if total_samples < 10:
            return 0.3  # Low confidence with few samples
        elif total_samples < 50:
            return 0.6  # Medium confidence
        else:
            return 0.9  # High confidence with many samples

    def _generate_threshold_recommendation(self, suggestions: Dict, confidence: float) -> str:
        """Generate human-readable recommendation"""
        if confidence < 0.5:
            return "Insufficient data for reliable threshold adjustments. Continue monitoring."

        significant_changes = [
            name for name, suggestion in suggestions.items()
            if abs(suggestion['change']) >= 0.05
        ]

        if not significant_changes:
            return "Current thresholds appear optimal. No significant adjustments needed."

        return f"Consider adjusting {', '.join(significant_changes)} thresholds based on recent feedback patterns."

    def _generate_adjustment_reasoning(self, false_positives: int, false_negatives: int, accuracy: float) -> str:
        """Generate reasoning for threshold adjustment"""
        if false_positives > false_negatives:
            return f"High false positive rate ({false_positives}) suggests threshold should be increased"
        elif false_negatives > false_positives:
            return f"High false negative rate ({false_negatives}) suggests threshold should be decreased"
        else:
            return f"Balanced error rates with {accuracy:.1%} accuracy - minimal adjustment needed"

    def _apply_threshold_adjustments(self, suggestions: Dict) -> None:
        """Apply suggested threshold adjustments to active configuration"""
        config = ModerationConfig.get_active_config()
        if not config:
            return

        # Apply suggested changes
        for threshold_name, suggestion in suggestions.items():
            if threshold_name == 'auto_mark':
                config.auto_mark_threshold = suggestion['suggested']
            elif threshold_name == 'flag_for_review':
                config.flag_for_review_threshold = suggestion['suggested']
            elif threshold_name == 'suggest_warning':
                config.suggest_warning_threshold = suggestion['suggested']

        config.save()
        logger.info(f"Applied automatic threshold adjustments: {suggestions}")

    def _analyze_detection_patterns(self) -> Dict:
        """Analyze which detection patterns are most effective"""
        # This analyzes the spoiler_detected_patterns field
        # to see which patterns correlate with correct/incorrect detections

        recent_feedback = ModerationFeedback.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).select_related('review')

        pattern_effectiveness = {}

        for feedback in recent_feedback:
            if feedback.review.spoiler_detected_patterns:
                patterns = feedback.review.spoiler_detected_patterns
                for pattern in patterns:
                    if pattern and pattern.strip():  # Skip empty patterns
                        if pattern not in pattern_effectiveness:
                            pattern_effectiveness[pattern] = {'correct': 0, 'total': 0}

                        pattern_effectiveness[pattern]['total'] += 1
                        if feedback.is_spoiler_correct:
                            pattern_effectiveness[pattern]['correct'] += 1

        # Calculate effectiveness rates
        for pattern, stats in pattern_effectiveness.items():
            stats['effectiveness'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0.0

        return pattern_effectiveness

    def _calculate_keyword_weights(self, pattern_analysis: Dict) -> Dict:
        """Calculate updated keyword weights based on pattern effectiveness"""
        # Simple weight adjustment based on effectiveness
        keyword_weights = {}

        for pattern, stats in pattern_analysis.items():
            effectiveness = stats['effectiveness']

            # Adjust weights: more effective patterns get higher weights
            if effectiveness > 0.8:
                weight = 1.2  # Boost effective patterns
            elif effectiveness > 0.6:
                weight = 1.0  # Keep neutral
            else:
                weight = 0.8  # Reduce ineffective patterns

            keyword_weights[pattern] = weight

        return keyword_weights

    def _get_recent_feedback_stats(self) -> Dict:
        """Get statistics about recent feedback"""
        start_date = timezone.now() - timedelta(days=7)

        recent_feedback = ModerationFeedback.objects.filter(
            created_at__gte=start_date
        )

        return {
            'total_feedback': recent_feedback.count(),
            'processed_for_learning': recent_feedback.filter(used_for_learning=True).count(),
            'pending_processing': recent_feedback.filter(used_for_learning=False).count(),
            'accuracy': recent_feedback.filter(is_spoiler_correct=True).count() / recent_feedback.count() if recent_feedback.count() > 0 else 0.0
        }

    def _calculate_learning_effectiveness(self) -> Dict:
        """Calculate how effective the learning system has been"""
        # Compare accuracy before and after learning adjustments
        config = ModerationConfig.get_active_config()

        # Get accuracy for last 30 days vs previous 30 days
        now = timezone.now()
        recent_period = now - timedelta(days=30)
        older_period = recent_period - timedelta(days=30)

        recent_accuracy = self._get_period_accuracy(recent_period, now)
        older_accuracy = self._get_period_accuracy(older_period, recent_period)

        improvement = recent_accuracy - older_accuracy

        return {
            'recent_accuracy': recent_accuracy,
            'previous_accuracy': older_accuracy,
            'improvement': round(improvement, 3),
            'trend': 'improving' if improvement > 0.02 else 'stable' if abs(improvement) <= 0.02 else 'declining'
        }

    def _get_period_accuracy(self, start_date: datetime, end_date: datetime) -> float:
        """Get accuracy for a specific time period"""
        feedback = ModerationFeedback.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date
        )

        total = feedback.count()
        correct = feedback.filter(is_spoiler_correct=True).count()

        return correct / total if total > 0 else 0.0

    def _get_last_threshold_adjustment(self) -> Optional[str]:
        """Get timestamp of last threshold adjustment"""
        # This would track when thresholds were last modified
        # For now, return the last config update
        config = ModerationConfig.get_active_config()
        return config.updated_at.isoformat() if config else None

    def _get_next_learning_cycle(self) -> Optional[str]:
        """Get when the next learning cycle will trigger"""
        config = ModerationConfig.get_active_config()
        if not config:
            return None

        recent_feedback_count = self._get_recent_feedback_count()
        feedback_needed = config.min_feedback_count - recent_feedback_count

        if feedback_needed <= 0:
            return "Ready to trigger"
        else:
            return f"Need {feedback_needed} more feedback items"

    def _calculate_trend_direction(self, weekly_accuracy: List[Dict]) -> str:
        """Calculate whether accuracy is trending up, down, or stable"""
        if len(weekly_accuracy) < 2:
            return 'insufficient_data'

        # Simple trend calculation
        first_half = weekly_accuracy[:len(weekly_accuracy)//2]
        second_half = weekly_accuracy[len(weekly_accuracy)//2:]

        first_avg = sum(w['accuracy'] for w in first_half) / len(first_half)
        second_avg = sum(w['accuracy'] for w in second_half) / len(second_half)

        difference = second_avg - first_avg

        if difference > 0.05:
            return 'improving'
        elif difference < -0.05:
            return 'declining'
        else:
            return 'stable'


# Global instance
learning_service = ModerationLearningService()
