"""
Event-Price Correlation Engine
Analyzes historical correlations between news events and price movements.
Calculates win rates, correlation coefficients, and timing patterns.
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """
    Analyzes historical correlations between news events and stock price movements.

    Analyzes events across multiple time windows:
    - same-day: 9:30-16:00 ET (market hours)
    - next-day: 0-24 hours after event
    - lagged: 2-5 days after event

    For each analysis, calculates:
    - Correlation coefficient (-1 to +1)
    - Win rate (% of times price moved as expected)
    - Sample size (minimum 20 occurrences)
    - Confidence (based on sample size and consistency)
    """

    # Default time windows for analysis (in hours from event)
    WINDOWS = {
        'same_day': (0, 8),      # Market hours (approximation)
        'next_day': (8, 32),     # Next 24 hours
        'lagged_2_5': (32, 120)  # 2-5 days
    }

    # Minimum sample size for statistical significance
    MIN_SAMPLE_SIZE = 20

    def __init__(self):
        """Initialize correlation analyzer"""
        logger.info("CorrelationAnalyzer initialized")

    def find_correlations(
        self,
        db: Session,
        stock_id: int,
        event_category: Optional[str] = None,
        min_sample_size: int = MIN_SAMPLE_SIZE
    ) -> Dict:
        """
        Analyze event-price correlations for a stock.

        Args:
            db: Database session
            stock_id: Stock ID to analyze
            event_category: Specific category to analyze (optional, all if None)
            min_sample_size: Minimum occurrences required for analysis

        Returns:
            Dict with correlation analysis results:
            {
                'stock_id': int,
                'event_category': str,
                'same_day': {...},
                'next_day': {...},
                'lagged_2_5': {...},
                'overall_win_rate': float,
                'sample_size': int,
                'confidence': float,
                'calculated_at': datetime
            }
        """
        from app.models import NewsEvent, StockPrice

        # Query events for this stock and category
        query = db.query(NewsEvent).filter(NewsEvent.stock_id == stock_id)

        if event_category:
            query = query.filter(NewsEvent.event_category == event_category)

        events = query.order_by(NewsEvent.event_date).all()

        if not events:
            logger.warning(f"No events found for stock_id={stock_id}, category={event_category}")
            return {
                'stock_id': stock_id,
                'event_category': event_category,
                'sample_size': 0,
                'confidence': 0.0,
                'calculated_at': datetime.utcnow()
            }

        # Fetch price data for the stock
        prices = db.query(StockPrice).filter(
            StockPrice.stock_id == stock_id
        ).order_by(StockPrice.date).all()

        if not prices:
            logger.warning(f"No price data found for stock_id={stock_id}")
            return {
                'stock_id': stock_id,
                'event_category': event_category,
                'sample_size': 0,
                'confidence': 0.0,
                'calculated_at': datetime.utcnow()
            }

        # Create price lookup (date -> StockPrice)
        price_map = {p.date: p for p in prices}

        # Analyze each time window
        window_results = {}
        valid_events = 0

        for window_name, (start_hours, end_hours) in self.WINDOWS.items():
            results = self._analyze_window(
                events=events,
                price_map=price_map,
                start_hours=start_hours,
                end_hours=end_hours
            )
            window_results[window_name] = results
            if results['sample_size'] > 0:
                valid_events += results['sample_size']

        # Calculate overall metrics
        overall_win_rate = self._calculate_overall_win_rate(window_results)
        confidence = self._calculate_confidence(valid_events, min_sample_size)

        return {
            'stock_id': stock_id,
            'event_category': event_category,
            'same_day': window_results.get('same_day', {}),
            'next_day': window_results.get('next_day', {}),
            'lagged_2_5': window_results.get('lagged_2_5', {}),
            'overall_win_rate': round(overall_win_rate, 3),
            'sample_size': valid_events,
            'confidence': round(confidence, 3),
            'calculated_at': datetime.utcnow()
        }

    def _analyze_window(
        self,
        events: List,
        price_map: Dict,
        start_hours: int,
        end_hours: int
    ) -> Dict:
        """
        Analyze a specific time window for event-price correlation.

        Args:
            events: List of news events
            price_map: Dict mapping dates to StockPrice objects
            start_hours: Start of window (hours from event)
            end_hours: End of window (hours from event)

        Returns:
            Dict with window analysis results
        """
        correlations = []
        win_count = 0
        total_count = 0

        for event in events:
            event_date = event.event_date

            # Get price on event date
            if event_date not in price_map:
                continue

            event_price = price_map[event_date]
            if not event_price.close_price:
                continue

            # Look for price move in window
            window_start_date = event_date + timedelta(hours=start_hours)
            window_end_date = event_date + timedelta(hours=end_hours)

            # Find first price within window
            window_price = None
            days_to_move = 0

            for day_offset in range(0, 10):  # Look ahead up to 10 days
                check_date = event_date + timedelta(days=day_offset)
                if check_date in price_map:
                    check_price = price_map[check_date]
                    if check_price.close_price and check_date >= window_start_date.date():
                        if check_date <= window_end_date.date():
                            window_price = check_price
                            days_to_move = day_offset
                            break

            if not window_price:
                continue

            # Calculate price change
            price_change = window_price.close_price - event_price.close_price
            price_change_pct = (price_change / event_price.close_price) * 100 if event_price.close_price else 0

            # Determine direction
            if price_change_pct > 0.5:  # Threshold of 0.5%
                direction = 'UP'
            elif price_change_pct < -0.5:
                direction = 'DOWN'
            else:
                direction = 'FLAT'

            # Analyze sentiment direction match
            sentiment_score = event.sentiment_score if event.sentiment_score else 0.0
            sentiment_direction = 'UP' if sentiment_score > 0.3 else ('DOWN' if sentiment_score < -0.3 else 'FLAT')

            # Win if sentiment matches price direction
            is_win = sentiment_direction == direction
            if is_win:
                win_count += 1

            total_count += 1

            correlations.append({
                'date': event_date,
                'price_change_pct': round(price_change_pct, 3),
                'direction': direction,
                'days_to_move': days_to_move,
                'win': is_win
            })

        # Calculate statistics
        if total_count == 0:
            return {
                'sample_size': 0,
                'win_rate': 0.0,
                'avg_price_change_pct': 0.0,
                'correlation_coefficient': 0.0,
                'consistency': 0.0
            }

        win_rate = win_count / total_count
        avg_price_change = np.mean([c['price_change_pct'] for c in correlations])
        consistency = self._calculate_consistency(correlations)

        # Calculate Pearson correlation coefficient
        correlation_coef = self._calculate_correlation_coefficient(correlations)

        return {
            'sample_size': total_count,
            'win_rate': round(win_rate, 3),
            'avg_price_change_pct': round(avg_price_change, 3),
            'correlation_coefficient': round(correlation_coef, 3),
            'consistency': round(consistency, 3)
        }

    def _calculate_correlation_coefficient(self, correlations: List[Dict]) -> float:
        """
        Calculate Pearson correlation coefficient between event sentiment and price movement.

        Args:
            correlations: List of correlation data dicts

        Returns:
            Correlation coefficient (-1 to +1)
        """
        if len(correlations) < 2:
            return 0.0

        # Convert direction to numeric: UP=1, FLAT=0, DOWN=-1
        directions = [1 if c['direction'] == 'UP' else (-1 if c['direction'] == 'DOWN' else 0)
                      for c in correlations]
        price_changes = [c['price_change_pct'] for c in correlations]

        try:
            correlation = np.corrcoef(directions, price_changes)[0, 1]
            return float(correlation) if not np.isnan(correlation) else 0.0
        except Exception as e:
            logger.warning(f"Error calculating correlation coefficient: {e}")
            return 0.0

    def _calculate_consistency(self, correlations: List[Dict]) -> float:
        """
        Calculate consistency of correlations (how often pattern repeats).

        Args:
            correlations: List of correlation data dicts

        Returns:
            Consistency score (0-1)
        """
        if len(correlations) < 2:
            return 0.0

        # Consistency = standard deviation of wins/losses
        # Lower SD = higher consistency
        wins = [1 if c['win'] else 0 for c in correlations]

        if len(wins) < 2:
            return 0.0

        # Calculate rolling consistency
        window_size = min(5, len(wins))
        rolling_wins = []

        for i in range(len(wins) - window_size + 1):
            window_win_rate = sum(wins[i:i+window_size]) / window_size
            rolling_wins.append(window_win_rate)

        if not rolling_wins:
            return 0.0

        # Consistency = 1 - (std_dev of rolling win rates)
        # Perfect consistency = 1.0, random = 0.5
        std_dev = np.std(rolling_wins)
        consistency = max(0.0, 1.0 - std_dev)

        return consistency

    def _calculate_overall_win_rate(self, window_results: Dict) -> float:
        """
        Calculate overall win rate across all windows.

        Args:
            window_results: Dict of window analysis results

        Returns:
            Overall win rate (0-1)
        """
        total_wins = 0
        total_count = 0

        for window_data in window_results.values():
            if isinstance(window_data, dict) and 'sample_size' in window_data:
                win_rate = window_data.get('win_rate', 0.0)
                sample_size = window_data.get('sample_size', 0)
                if sample_size > 0:
                    total_wins += int(win_rate * sample_size)
                    total_count += sample_size

        if total_count == 0:
            return 0.0

        return total_wins / total_count

    def _calculate_confidence(self, sample_size: int, min_sample: int) -> float:
        """
        Calculate confidence based on sample size.

        Args:
            sample_size: Number of samples in analysis
            min_sample: Minimum required for full confidence

        Returns:
            Confidence score (0-1)
        """
        if sample_size == 0:
            return 0.0

        # Confidence increases with sample size, plateaus at min_sample
        confidence = min(sample_size / min_sample, 1.0)
        return confidence

    def batch_analyze_categories(
        self,
        db: Session,
        stock_id: int,
        categories: List[str]
    ) -> Dict[str, Dict]:
        """
        Analyze correlations for multiple event categories.

        Args:
            db: Database session
            stock_id: Stock ID
            categories: List of event categories to analyze

        Returns:
            Dict mapping category -> correlation results
        """
        results = {}

        for category in categories:
            result = self.find_correlations(db, stock_id, event_category=category)
            results[category] = result

        return results
