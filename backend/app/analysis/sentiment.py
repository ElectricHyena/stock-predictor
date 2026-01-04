"""
Sentiment Analysis Engine
Analyzes sentiment of news articles and headlines using lexicon-based approach.
Outputs: sentiment_score (-1.0 to +1.0), sentiment_category (POSITIVE/NEGATIVE/NEUTRAL)
"""

import logging
import re
from typing import Dict, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class SentimentCategory(str, Enum):
    """Sentiment categories"""
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class SentimentAnalyzer:
    """
    Analyzes sentiment of news articles using lexicon-based approach.

    Sentiment Score: -1.0 (very negative) to +1.0 (very positive)
    Sentiment Category:
    - POSITIVE: score > 0.2
    - NEUTRAL: -0.2 <= score <= 0.2
    - NEGATIVE: score < -0.2
    """

    # Sentiment threshold for category classification
    NEUTRAL_THRESHOLD = 0.2

    # Sentiment word lists with weights
    POSITIVE_WORDS = {
        'gain': 1.0, 'surge': 1.0, 'profit': 1.0, 'strong': 0.8, 'bullish': 1.0,
        'positive': 0.8, 'growth': 0.9, 'win': 0.9, 'excellent': 1.0, 'beat': 0.9,
        'recovery': 0.8, 'upbeat': 1.0, 'outperform': 0.9, 'upgrade': 0.9, 'rally': 1.0,
        'soar': 1.0, 'jump': 0.8, 'spike': 0.8, 'strength': 0.8, 'robust': 0.8,
        'accelerate': 0.8, 'momentum': 0.8, 'opportunity': 0.7, 'success': 0.9, 'successful': 0.9,
        'best': 0.8, 'better': 0.7, 'improve': 0.8, 'improvement': 0.8, 'boost': 0.8,
        'strong buy': 1.0, 'buy': 0.8, 'outperform': 0.9, 'optimistic': 0.8, 'optimism': 0.8,
        'rebound': 0.8, 'expansion': 0.8, 'lead': 0.7, 'leader': 0.7, 'leading': 0.7,
        'innovative': 0.8, 'innovation': 0.8, 'advanced': 0.7, 'improve': 0.8,
        'exceed': 0.8, 'exceeded': 0.8, 'outperforms': 0.9, 'boom': 0.9, 'breakthrough': 0.9,
    }

    NEGATIVE_WORDS = {
        'loss': 1.0, 'drop': 0.9, 'decline': 0.9, 'weak': 0.8, 'bearish': 1.0,
        'negative': 0.8, 'falling': 0.9, 'miss': 0.9, 'poor': 0.8, 'warning': 0.9,
        'risk': 0.7, 'challenges': 0.7, 'challenge': 0.7, 'difficult': 0.7, 'downturn': 0.9,
        'bearish': 1.0, 'short sell': 1.0, 'sell': 0.8, 'underperform': 0.9,
        'downgrade': 0.9, 'fail': 0.9, 'failure': 0.9, 'slump': 0.9, 'plunge': 1.0,
        'crash': 1.0, 'collapse': 1.0, 'crumble': 1.0, 'worse': 0.8, 'worst': 0.9,
        'struggle': 0.8, 'struggling': 0.8, 'concern': 0.7, 'concerns': 0.7, 'uncertainty': 0.7,
        'bad': 0.8, 'terrible': 1.0, 'awful': 1.0, 'horrible': 1.0, 'dismal': 1.0,
        'deficit': 0.8, 'loss': 1.0, 'losses': 0.9, 'lower': 0.7, 'decrease': 0.7,
        'hurt': 0.8, 'threat': 0.8, 'threatened': 0.8, 'recession': 0.8, 'crisis': 0.9,
        'fraud': 1.0, 'scandal': 1.0, 'bankruptcy': 1.0, 'bankrupt': 1.0,
    }

    # Negation words that flip sentiment
    NEGATION_WORDS = {'not', 'no', 'neither', 'never', 'cannot', "can't", "isn't", "doesn't", "didn't", "won't", "wouldn't"}

    # Intensifiers that amplify sentiment
    INTENSIFIERS = {
        'very': 1.5, 'extremely': 1.7, 'incredibly': 1.6, 'remarkably': 1.5,
        'significantly': 1.4, 'substantially': 1.4, 'substantially': 1.4,
        'moderately': 0.8, 'somewhat': 0.7, 'slightly': 0.5, 'barely': 0.4
    }

    def __init__(self):
        """Initialize sentiment analyzer"""
        self.positive_words = set(self.POSITIVE_WORDS.keys())
        self.negative_words = set(self.NEGATIVE_WORDS.keys())
        logger.info(
            "SentimentAnalyzer initialized with %d positive and %d negative words",
            len(self.positive_words),
            len(self.negative_words)
        )

    def analyze(self, text: str, return_category: bool = True) -> Tuple[float, str]:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze (headline or full content)
            return_category: If True, also return sentiment category

        Returns:
            Tuple of (sentiment_score, sentiment_category)
            - sentiment_score: float -1.0 to +1.0
            - sentiment_category: str POSITIVE/NEUTRAL/NEGATIVE
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to sentiment analyzer")
            return 0.0, SentimentCategory.NEUTRAL.value

        # Preprocess text
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        if not words:
            return 0.0, SentimentCategory.NEUTRAL.value

        # Calculate sentiment score
        positive_score = 0.0
        negative_score = 0.0

        i = 0
        while i < len(words):
            word = words[i]
            multiplier = 1.0

            # Check for intensifiers (word before current word)
            if i > 0 and words[i - 1] in self.INTENSIFIERS:
                multiplier = self.INTENSIFIERS[words[i - 1]]

            # Check for negation (word before current word)
            negation = False
            if i > 0 and words[i - 1] in self.NEGATION_WORDS:
                negation = True

            # Score positive words
            if word in self.positive_words:
                score = self.POSITIVE_WORDS[word] * multiplier
                if negation:
                    negative_score += score  # Negate positive to negative
                else:
                    positive_score += score

            # Score negative words
            elif word in self.negative_words:
                score = self.NEGATIVE_WORDS[word] * multiplier
                if negation:
                    positive_score += score  # Negate negative to positive
                else:
                    negative_score += score

            i += 1

        # Calculate net sentiment
        total_score = positive_score + negative_score
        if total_score == 0:
            sentiment_score = 0.0
        else:
            # Normalize to -1 to +1 range
            # (positive - negative) / (positive + negative)
            sentiment_score = (positive_score - negative_score) / total_score

        # Ensure within bounds
        sentiment_score = max(-1.0, min(1.0, sentiment_score))

        # Determine category using threshold
        if sentiment_score > self.NEUTRAL_THRESHOLD:
            sentiment_category = SentimentCategory.POSITIVE.value
        elif sentiment_score < -self.NEUTRAL_THRESHOLD:
            sentiment_category = SentimentCategory.NEGATIVE.value
        else:
            sentiment_category = SentimentCategory.NEUTRAL.value

        logger.debug(
            "Sentiment analyzed: score=%.3f, category=%s, text_length=%d",
            sentiment_score,
            sentiment_category,
            len(text)
        )

        if return_category:
            return sentiment_score, sentiment_category
        else:
            return sentiment_score, ""

    def batch_analyze(self, texts: list) -> list:
        """
        Analyze sentiment of multiple texts efficiently.

        Args:
            texts: List of text strings to analyze

        Returns:
            List of (sentiment_score, sentiment_category) tuples
        """
        results = []
        for text in texts:
            score, category = self.analyze(text)
            results.append((score, category))
        return results

    def analyze_headline_and_content(
        self,
        headline: str,
        content: str = ""
    ) -> Dict:
        """
        Analyze sentiment of both headline and content, providing separate and combined scores.

        Args:
            headline: Article headline
            content: Full article content (optional)

        Returns:
            Dict with headline_score, content_score, headline_category, content_category,
            combined_score, combined_category
        """
        headline_score, headline_category = self.analyze(headline)
        content_score, content_category = self.analyze(content) if content else (0.0, SentimentCategory.NEUTRAL.value)

        # Combined score - weight headline more heavily (60%) than content (40%)
        if content:
            combined_score = (headline_score * 0.6) + (content_score * 0.4)
        else:
            combined_score = headline_score

        # Combined category using threshold
        if combined_score > self.NEUTRAL_THRESHOLD:
            combined_category = SentimentCategory.POSITIVE.value
        elif combined_score < -self.NEUTRAL_THRESHOLD:
            combined_category = SentimentCategory.NEGATIVE.value
        else:
            combined_category = SentimentCategory.NEUTRAL.value

        return {
            'headline_score': round(headline_score, 3),
            'headline_category': headline_category,
            'content_score': round(content_score, 3) if content else None,
            'content_category': content_category if content else None,
            'combined_score': round(combined_score, 3),
            'combined_category': combined_category
        }

    def get_confidence(self, sentiment_score: float) -> float:
        """
        Get confidence level based on sentiment score magnitude.

        Higher magnitude = higher confidence that it's not neutral

        Args:
            sentiment_score: Score from -1.0 to +1.0

        Returns:
            Confidence score from 0.0 to 1.0
        """
        # Confidence increases as we move away from 0 (neutral)
        # At 0: confidence = 0.3 (low)
        # At +/- 0.5: confidence = 0.7
        # At +/- 1.0: confidence = 1.0
        confidence = 0.3 + (abs(sentiment_score) * 0.7)
        return min(1.0, confidence)
