"""
Analysis Service - High-level orchestration of all analysis engines
Chains together: categorizer -> sentiment -> correlator -> scorer
Provides centralized API for running complete analysis pipeline
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.analysis import (
    EventCategorizer,
    SentimentAnalyzer,
    CorrelationAnalyzer,
    PredictabilityScorer
)
from app.models import NewsEvent, EventPriceCorrelation, PredictabilityScore, Stock
from app.cache import cache, cache_key_predictability, cache_key_prediction

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    High-level service for running complete analysis pipeline.

    Pipeline:
    1. EventCategorizer: Categorize news into event types
    2. SentimentAnalyzer: Analyze sentiment of news
    3. CorrelationAnalyzer: Find event-price correlations
    4. PredictabilityScorer: Score stock predictability

    All results are stored in the database.
    """

    def __init__(self):
        """Initialize all analysis engines"""
        self.categorizer = EventCategorizer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.predictor = PredictabilityScorer()

        logger.info("AnalysisService initialized with all analysis engines")

    def _invalidate_predictability_cache(self, db: Session, stock_id: int) -> None:
        """
        Invalidate predictability and prediction caches for a stock.

        Args:
            db: Database session
            stock_id: Stock ID
        """
        try:
            stock = db.query(Stock).filter(Stock.id == stock_id).first()
            if stock:
                # Invalidate both predictability and prediction caches
                cache.delete(cache_key_predictability(stock.ticker))
                cache.delete(cache_key_prediction(stock.ticker))
                logger.debug(f"Invalidated predictability cache for {stock.ticker}")
        except Exception as e:
            logger.error(f"Error invalidating cache for stock_id={stock_id}: {e}")

    def analyze_stock(
        self,
        db: Session,
        stock_id: int,
        update_events: bool = True,
        update_correlations: bool = True,
        update_predictability: bool = True
    ) -> Dict:
        """
        Run complete analysis pipeline for a stock.

        Pipeline:
        1. Categorize and analyze sentiment of all news events
        2. Calculate event-price correlations
        3. Generate predictability score

        Args:
            db: Database session
            stock_id: Stock ID to analyze
            update_events: If True, update existing news events with analysis
            update_correlations: If True, calculate event-price correlations
            update_predictability: If True, generate predictability score

        Returns:
            Dict with pipeline results:
            {
                'stock_id': int,
                'events_analyzed': int,
                'events': [...],
                'correlations': {...},
                'predictability': {...},
                'completed_at': datetime,
                'status': 'SUCCESS' | 'PARTIAL' | 'FAILED'
            }
        """
        logger.info(f"Starting analysis pipeline for stock_id={stock_id}")
        results = {
            'stock_id': stock_id,
            'events_analyzed': 0,
            'events': [],
            'correlations': {},
            'predictability': None,
            'completed_at': None,
            'status': 'SUCCESS'
        }

        try:
            # Step 1: Analyze existing news events
            if update_events:
                events_result = self._analyze_events(db, stock_id)
                results['events'] = events_result['events']
                results['events_analyzed'] = events_result['count']
                logger.info(f"Analyzed {events_result['count']} events for stock_id={stock_id}")

            # Step 2: Calculate event-price correlations
            if update_correlations:
                try:
                    correlations = self._calculate_correlations(db, stock_id)
                    results['correlations'] = correlations
                    logger.info(f"Calculated correlations for stock_id={stock_id}")
                except Exception as e:
                    logger.error(f"Error calculating correlations: {e}", exc_info=True)
                    results['status'] = 'PARTIAL'

            # Step 3: Generate predictability score
            if update_predictability:
                try:
                    predictability = self._calculate_predictability(db, stock_id)
                    results['predictability'] = predictability
                    logger.info(f"Generated predictability score for stock_id={stock_id}")
                except Exception as e:
                    logger.error(f"Error calculating predictability: {e}", exc_info=True)
                    results['status'] = 'PARTIAL'

            results['completed_at'] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Fatal error in analysis pipeline: {e}", exc_info=True)
            results['status'] = 'FAILED'
            results['error'] = str(e)

        return results

    def _analyze_events(self, db: Session, stock_id: int) -> Dict:
        """
        Categorize and analyze sentiment of all news events for a stock.

        Args:
            db: Database session
            stock_id: Stock ID

        Returns:
            Dict with analyzed events
        """
        events = db.query(NewsEvent).filter(
            NewsEvent.stock_id == stock_id
        ).order_by(NewsEvent.event_date.desc()).all()

        analyzed_events = []

        for event in events:
            try:
                # Categorize event
                category, confidence, secondary = self.categorizer.categorize_event(
                    headline=event.headline,
                    content=event.content or ""
                )

                # Analyze sentiment
                sentiment_score, sentiment_category = self.sentiment_analyzer.analyze(
                    f"{event.headline} {event.content or ''}"
                )

                # Update event in database
                event.event_category = category
                event.sentiment_score = sentiment_score
                event.sentiment_category = sentiment_category

                db.add(event)

                analyzed_events.append({
                    'event_id': event.id,
                    'headline': event.headline[:100],
                    'category': category,
                    'category_confidence': confidence,
                    'sentiment_score': round(sentiment_score, 3),
                    'sentiment_category': sentiment_category
                })

            except Exception as e:
                logger.error(f"Error analyzing event {event.id}: {e}")
                continue

        # Commit all event updates
        try:
            db.commit()
            logger.info(f"Committed {len(analyzed_events)} event analyses")
        except Exception as e:
            logger.error(f"Error committing event updates: {e}")
            db.rollback()

        return {
            'count': len(analyzed_events),
            'events': analyzed_events
        }

    def _calculate_correlations(self, db: Session, stock_id: int) -> Dict:
        """
        Calculate event-price correlations for a stock.

        Args:
            db: Database session
            stock_id: Stock ID

        Returns:
            Dict with correlation analysis results
        """
        # Get all unique event categories
        categories = db.query(NewsEvent.event_category).filter(
            NewsEvent.stock_id == stock_id
        ).distinct().all()

        category_list = [c[0] for c in categories if c[0]]

        if not category_list:
            logger.warning(f"No event categories found for stock_id={stock_id}")
            return {}

        # Analyze each category
        correlations = self.correlation_analyzer.batch_analyze_categories(
            db, stock_id, category_list
        )

        # Store in database
        for category, correlation_data in correlations.items():
            try:
                # Check if record exists
                existing = db.query(EventPriceCorrelation).filter(
                    EventPriceCorrelation.stock_id == stock_id,
                    EventPriceCorrelation.event_category == category
                ).first()

                if existing:
                    # Update existing
                    existing.historical_win_rate = correlation_data.get('overall_win_rate')
                    existing.sample_size = correlation_data.get('sample_size')
                    existing.confidence_score = correlation_data.get('confidence')
                    existing.updated_at = datetime.utcnow()
                    db.add(existing)
                else:
                    # Create new
                    corr = EventPriceCorrelation(
                        stock_id=stock_id,
                        event_category=category,
                        event_date=datetime.utcnow().date(),
                        historical_win_rate=correlation_data.get('overall_win_rate'),
                        sample_size=correlation_data.get('sample_size'),
                        confidence_score=correlation_data.get('confidence')
                    )
                    db.add(corr)

            except Exception as e:
                logger.error(f"Error storing correlation for {category}: {e}")
                continue

        try:
            db.commit()
            logger.info(f"Stored correlations for {len(correlations)} categories")
        except Exception as e:
            logger.error(f"Error committing correlations: {e}")
            db.rollback()

        return correlations

    def _calculate_predictability(self, db: Session, stock_id: int) -> Dict:
        """
        Calculate predictability score for a stock.

        Args:
            db: Database session
            stock_id: Stock ID

        Returns:
            Dict with predictability score
        """
        # Calculate score
        score_data = self.predictor.score_stock(db, stock_id)

        # Store in database
        try:
            # Check if record exists for today
            today = datetime.utcnow().date()
            existing = db.query(PredictabilityScore).filter(
                PredictabilityScore.stock_id == stock_id,
                PredictabilityScore.calculated_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).first()

            if existing:
                # Update existing
                existing.information_availability_score = score_data['information_availability_score']
                existing.pattern_consistency_score = score_data['pattern_consistency_score']
                existing.timing_certainty_score = score_data['timing_certainty_score']
                existing.direction_confidence_score = score_data['direction_confidence_score']
                existing.overall_predictability_score = score_data['overall_predictability_score']
                existing.prediction_direction = score_data['prediction_direction']
                existing.prediction_magnitude_low = score_data['prediction_magnitude_low']
                existing.prediction_magnitude_high = score_data['prediction_magnitude_high']
                existing.calculated_at = datetime.utcnow()
                db.add(existing)
            else:
                # Create new
                score = PredictabilityScore(
                    stock_id=stock_id,
                    information_availability_score=score_data['information_availability_score'],
                    pattern_consistency_score=score_data['pattern_consistency_score'],
                    timing_certainty_score=score_data['timing_certainty_score'],
                    direction_confidence_score=score_data['direction_confidence_score'],
                    overall_predictability_score=score_data['overall_predictability_score'],
                    prediction_direction=score_data['prediction_direction'],
                    prediction_magnitude_low=score_data['prediction_magnitude_low'],
                    prediction_magnitude_high=score_data['prediction_magnitude_high'],
                    calculated_at=datetime.utcnow(),
                    is_current=True
                )
                db.add(score)

            db.commit()
            logger.info(f"Stored predictability score for stock_id={stock_id}: {score_data['overall_predictability_score']}")

            # Invalidate cache after successful update
            self._invalidate_predictability_cache(db, stock_id)

        except Exception as e:
            logger.error(f"Error storing predictability score: {e}")
            db.rollback()

        return score_data

    def batch_analyze_stocks(
        self,
        db: Session,
        stock_ids: List[int]
    ) -> Dict[int, Dict]:
        """
        Analyze multiple stocks.

        Args:
            db: Database session
            stock_ids: List of stock IDs to analyze

        Returns:
            Dict mapping stock_id -> analysis results
        """
        results = {}

        for stock_id in stock_ids:
            try:
                result = self.analyze_stock(db, stock_id)
                results[stock_id] = result
            except Exception as e:
                logger.error(f"Error analyzing stock {stock_id}: {e}")
                results[stock_id] = {
                    'stock_id': stock_id,
                    'status': 'FAILED',
                    'error': str(e)
                }

        return results

    def recalculate_correlations(self, db: Session, stock_id: int) -> Dict:
        """
        Recalculate correlations for a specific stock (used for weekly updates).

        Args:
            db: Database session
            stock_id: Stock ID

        Returns:
            Dict with recalculation results
        """
        logger.info(f"Recalculating correlations for stock_id={stock_id}")
        return self._calculate_correlations(db, stock_id)

    def recalculate_predictability(self, db: Session, stock_id: int) -> Dict:
        """
        Recalculate predictability score for a specific stock (used for daily updates).

        Args:
            db: Database session
            stock_id: Stock ID

        Returns:
            Dict with recalculation results
        """
        logger.info(f"Recalculating predictability for stock_id={stock_id}")
        return self._calculate_predictability(db, stock_id)
