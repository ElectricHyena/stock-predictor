"""
Predictability Scoring Engine
Scores the predictability of stocks based on 4 weighted factors:
- Information (30%): Event frequency and categorization confidence
- Pattern (25%): Historical pattern consistency
- Timing (25%): Event-price correlation timing certainty
- Direction (20%): Directional accuracy (up/down prediction)
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PredictabilityScorer:
    """
    Scores the predictability of stocks based on historical analysis.

    Output: 0-100 score with component breakdown
    - information_availability_score (30%): Event frequency + quality
    - pattern_consistency_score (25%): Historical pattern reliability
    - timing_certainty_score (25%): Timing predictability
    - direction_confidence_score (20%): Direction accuracy

    Prediction output:
    - direction: UP/DOWN/SIDEWAYS
    - magnitude: % change range
    - timing: Days ahead for move
    - win_rate: Historical accuracy %
    """

    # Weights for each factor
    WEIGHTS = {
        'information': 0.30,
        'pattern': 0.25,
        'timing': 0.25,
        'direction': 0.20
    }

    def __init__(self):
        """Initialize predictability scorer"""
        logger.info("PredictabilityScorer initialized with weights: %s", self.WEIGHTS)

    def score_stock(
        self,
        db: Session,
        stock_id: int,
        days_lookback: int = 365
    ) -> Dict:
        """
        Calculate predictability score for a stock.

        Args:
            db: Database session
            stock_id: Stock ID to score
            days_lookback: Number of days to analyze (default 1 year)

        Returns:
            Dict with predictability score and component breakdown:
            {
                'stock_id': int,
                'overall_predictability_score': 0-100,
                'information_availability_score': 0-100,
                'pattern_consistency_score': 0-100,
                'timing_certainty_score': 0-100,
                'direction_confidence_score': 0-100,
                'prediction_direction': 'UP'|'DOWN'|'SIDEWAYS',
                'prediction_magnitude_low': float,
                'prediction_magnitude_high': float,
                'prediction_timing_days': int,
                'prediction_win_rate': float,
                'sample_size': int,
                'confidence': float,
                'calculated_at': datetime
            }
        """
        from app.models import NewsEvent, EventPriceCorrelation

        # Calculate lookback date
        lookback_date = datetime.utcnow().date() - timedelta(days=days_lookback)

        # Fetch recent events for the stock
        events = db.query(NewsEvent).filter(
            NewsEvent.stock_id == stock_id,
            NewsEvent.event_date >= lookback_date
        ).all()

        # Fetch correlations for the stock
        correlations = db.query(EventPriceCorrelation).filter(
            EventPriceCorrelation.stock_id == stock_id
        ).all()

        # Calculate individual factor scores
        information_score = self._score_information(events)
        pattern_score = self._score_pattern(correlations)
        timing_score = self._score_timing(correlations)
        direction_score = self._score_direction(events, correlations)

        # Calculate weighted overall score
        overall_score = int(
            (information_score * self.WEIGHTS['information']) +
            (pattern_score * self.WEIGHTS['pattern']) +
            (timing_score * self.WEIGHTS['timing']) +
            (direction_score * self.WEIGHTS['direction'])
        )

        # Ensure score is within 0-100
        overall_score = max(0, min(100, overall_score))

        # Generate prediction
        prediction = self._generate_prediction(events, correlations)

        # Calculate confidence based on data available
        confidence = self._calculate_confidence(events, correlations)

        return {
            'stock_id': stock_id,
            'overall_predictability_score': overall_score,
            'information_availability_score': int(information_score),
            'pattern_consistency_score': int(pattern_score),
            'timing_certainty_score': int(timing_score),
            'direction_confidence_score': int(direction_score),
            'prediction_direction': prediction['direction'],
            'prediction_magnitude_low': prediction['magnitude_low'],
            'prediction_magnitude_high': prediction['magnitude_high'],
            'prediction_timing_days': prediction['timing_days'],
            'prediction_win_rate': prediction['win_rate'],
            'sample_size': len(events),
            'confidence': round(confidence, 3),
            'calculated_at': datetime.utcnow()
        }

    def _score_information(self, events: List) -> float:
        """
        Score information availability based on event frequency and quality.

        Factors:
        - Event frequency (more = higher)
        - Categorization confidence (higher = higher)
        - Sentiment availability (more complete = higher)
        - Recency (recent > old)

        Args:
            events: List of news events

        Returns:
            Score 0-100
        """
        if not events:
            return 10.0  # Base score for no events

        # Event frequency score (0-40)
        # Normalize: 30+ events in period = 40
        event_count_score = min((len(events) / 30) * 40, 40)

        # Categorization confidence score (0-30)
        confidence_scores = [getattr(e, 'event_category', 'sector') for e in events]
        # Higher confidence in better categorizations
        avg_confidence = 0.7  # Default assumption
        confidence_score = avg_confidence * 30

        # Sentiment availability score (0-20)
        sentiments = [e.sentiment_score for e in events if e.sentiment_score is not None]
        if sentiments:
            sentiment_score = (len(sentiments) / len(events)) * 20
        else:
            sentiment_score = 0.0

        # Recency score (0-10)
        if events:
            most_recent = max(e.event_date for e in events)
            days_old = (datetime.utcnow().date() - most_recent).days
            recency_score = max(0, 10 - (days_old / 30))  # Loses 1 point per 30 days
        else:
            recency_score = 0.0

        total_score = event_count_score + confidence_score + sentiment_score + recency_score
        return min(100.0, max(0.0, total_score))

    def _score_pattern(self, correlations: List) -> float:
        """
        Score historical pattern consistency.

        Factors:
        - Win rate (higher = higher)
        - Sample size (more = higher confidence)
        - Consistency across different events
        - Overall correlation coefficient

        Args:
            correlations: List of correlation analysis results

        Returns:
            Score 0-100
        """
        if not correlations:
            return 10.0  # Base score

        # Win rate score (0-50)
        win_rates = [c.historical_win_rate for c in correlations if c.historical_win_rate]
        if win_rates:
            avg_win_rate = np.mean(win_rates)
            # 50% win rate = 25, 60% = 30, 70% = 40, 80% = 50
            win_rate_score = ((avg_win_rate - 0.5) * 100) if avg_win_rate > 0.5 else 0
            win_rate_score = min(50, max(0, win_rate_score))
        else:
            win_rate_score = 0.0

        # Sample size score (0-30)
        sample_sizes = [c.sample_size for c in correlations if c.sample_size]
        if sample_sizes:
            avg_sample = np.mean(sample_sizes)
            # 20 samples = 15, 50+ = 30
            sample_score = min(30, (avg_sample / 50) * 30)
        else:
            sample_score = 0.0

        # Consistency score (0-20)
        # Count how many correlations have good win rates
        good_correlations = sum(1 for c in correlations if c.historical_win_rate and c.historical_win_rate > 0.55)
        consistency_score = (good_correlations / max(1, len(correlations))) * 20

        total_score = win_rate_score + sample_score + consistency_score
        return min(100.0, max(0.0, total_score))

    def _score_timing(self, correlations: List) -> float:
        """
        Score timing certainty and predictability.

        Factors:
        - Same-day move frequency (highest weight)
        - Next-day move frequency (medium weight)
        - Lagged move frequency (lower weight)
        - Timing consistency

        Args:
            correlations: List of correlation results

        Returns:
            Score 0-100
        """
        if not correlations:
            return 10.0

        same_day_count = 0
        next_day_count = 0
        lagged_count = 0

        for correlation in correlations:
            days = getattr(correlation, 'days_to_move', 1)
            if days == 0:
                same_day_count += 1
            elif days == 1:
                next_day_count += 1
            else:
                lagged_count += 1

        total = len(correlations)

        # Scoring: immediate moves = better predictability
        # same_day (0) = 3 points, next_day (1) = 2 points, lagged (2+) = 1 point
        timing_score = (
            (same_day_count * 3 / total * 50) +
            (next_day_count * 2 / total * 30) +
            (lagged_count * 1 / total * 20)
        )

        return min(100.0, max(0.0, timing_score))

    def _score_direction(self, events: List, correlations: List) -> float:
        """
        Score directional accuracy and clarity.

        Factors:
        - Sentiment-to-price alignment
        - Directional bias (strong up/down vs sideways)
        - Recent direction accuracy
        - Sentiment distribution (more extreme = clearer direction)

        Args:
            events: List of news events
            correlations: List of correlation results

        Returns:
            Score 0-100
        """
        if not events:
            return 10.0

        # Sentiment distribution score (0-40)
        sentiments = [e.sentiment_score for e in events if e.sentiment_score is not None]
        if sentiments:
            # More extreme sentiments = clearer direction
            extreme_count = sum(1 for s in sentiments if abs(s) > 0.6)
            sentiment_clarity = (extreme_count / len(sentiments)) * 40
        else:
            sentiment_clarity = 10.0

        # Recent performance score (0-30)
        recent_events = [e for e in events if (datetime.utcnow().date() - e.event_date).days <= 30]
        if recent_events:
            recent_sentiments = [e.sentiment_score for e in recent_events if e.sentiment_score]
            if recent_sentiments:
                avg_sentiment = np.mean(recent_sentiments)
                # If average sentiment is extreme, direction is clear
                recent_score = (abs(avg_sentiment) / 1.0) * 30
            else:
                recent_score = 0.0
        else:
            recent_score = 0.0

        # Directional bias score (0-30)
        if correlations:
            directions = [c.price_direction for c in correlations if c.price_direction]
            if directions:
                up_count = sum(1 for d in directions if d == 'UP')
                down_count = sum(1 for d in directions if d == 'DOWN')
                flat_count = sum(1 for d in directions if d == 'FLAT')

                # Strong bias (>60%) toward up or down = higher score
                total = len(directions)
                max_bias = max(up_count, down_count) / total
                bias_score = max(0, (max_bias - 0.5) * 60) if max_bias > 0.5 else 0
            else:
                bias_score = 0.0
        else:
            bias_score = 0.0

        total_score = sentiment_clarity + recent_score + bias_score
        return min(100.0, max(0.0, total_score))

    def _generate_prediction(self, events: List, correlations: List) -> Dict:
        """
        Generate prediction for stock direction and magnitude.

        Args:
            events: List of news events
            correlations: List of correlation results

        Returns:
            Dict with:
            - direction: UP/DOWN/SIDEWAYS
            - magnitude_low: low % estimate
            - magnitude_high: high % estimate
            - timing_days: days until move expected
            - win_rate: historical accuracy %
        """
        direction = 'SIDEWAYS'
        magnitude_low = 0.5
        magnitude_high = 1.5
        timing_days = 1
        win_rate = 0.5

        # Determine direction from recent sentiment
        if events:
            recent_events = [e for e in events if (datetime.utcnow().date() - e.event_date).days <= 7]
            if recent_events:
                sentiments = [e.sentiment_score for e in recent_events if e.sentiment_score]
                if sentiments:
                    avg_sentiment = np.mean(sentiments)
                    if avg_sentiment > 0.3:
                        direction = 'UP'
                    elif avg_sentiment < -0.3:
                        direction = 'DOWN'

        # Estimate magnitude from historical correlations
        if correlations:
            price_changes = [abs(c.price_change_pct) for c in correlations if c.price_change_pct]
            if price_changes:
                magnitude_low = np.percentile(price_changes, 25)
                magnitude_high = np.percentile(price_changes, 75)

                # Win rate from correlations
                win_rates = [c.historical_win_rate for c in correlations if c.historical_win_rate]
                if win_rates:
                    win_rate = np.mean(win_rates)

                # Timing from correlations
                timings = [c.days_to_move for c in correlations if hasattr(c, 'days_to_move') and c.days_to_move is not None]
                if timings:
                    timing_days = int(np.median(timings))

        return {
            'direction': direction,
            'magnitude_low': round(magnitude_low, 2),
            'magnitude_high': round(magnitude_high, 2),
            'timing_days': max(0, timing_days),
            'win_rate': round(win_rate, 3)
        }

    def _calculate_confidence(self, events: List, correlations: List) -> float:
        """
        Calculate overall confidence in the prediction.

        Based on:
        - Number of events (more = higher)
        - Number of correlations (more = higher)
        - Data recency

        Args:
            events: List of news events
            correlations: List of correlations

        Returns:
            Confidence 0-1
        """
        event_score = min(len(events) / 30, 1.0)  # 30+ events = max confidence
        correlation_score = min(len(correlations) / 8, 1.0)  # 8+ categories = max

        # Average the two
        base_confidence = (event_score + correlation_score) / 2

        # Apply recency penalty
        if events:
            most_recent = max(e.event_date for e in events)
            days_old = (datetime.utcnow().date() - most_recent).days
            recency_factor = 1.0 - (days_old / 365)  # 0.5 at 6 months old
            recency_factor = max(0.3, recency_factor)
        else:
            recency_factor = 0.3

        confidence = base_confidence * recency_factor
        return max(0.0, min(1.0, confidence))
