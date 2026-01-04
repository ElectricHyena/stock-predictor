"""
Event Categorization Engine
Categorizes news events into predefined categories using keyword matching.
Categories: earnings, policy, seasonal, technical, sector, merger, dividend, management
"""

import logging
from typing import Dict, Tuple, List
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class EventCategorizer:
    """
    Categorizes news events into specific categories using keyword matching.

    Categories:
    - earnings: Company financial results, EPS, revenue guidance
    - policy: Government regulations, tax changes, policy announcements
    - seasonal: Quarterly/year-end events, holiday effects
    - technical: Corporate actions (splits, buybacks, listings)
    - sector: Industry-wide trends, competitor news
    - merger: M&A activities, acquisitions, mergers
    - dividend: Dividend announcements, distributions
    - management: Executive changes, leadership announcements
    """

    # Category keywords - expanded for better matching
    CATEGORY_KEYWORDS = {
        'earnings': {
            'keywords': [
                'earnings', 'q1', 'q2', 'q3', 'q4', 'quarterly', 'eps', 'earnings per share',
                'revenue', 'profit', 'net income', 'guidance', 'forecast', 'beat', 'miss',
                'results', 'financial results', 'earnings release', 'earnings call',
                'annual report', 'fy', 'fiscal year', 'fye', 'year-end results',
                'quarterly results', 'ebitda', 'operating income', 'margin', 'margins'
            ],
            'weight': 1.0
        },
        'policy': {
            'keywords': [
                'regulatory', 'regulation', 'policy', 'government', 'sec', 'rbi', 'tax',
                'subsidy', 'tariff', 'trade', 'law', 'legislation', 'legal', 'compliance',
                'cra', 'fca', 'doj', 'antitrust', 'ban', 'restriction', 'rule', 'rules',
                'approval', 'license', 'permit', 'agency', 'federal', 'administration',
                'parliament', 'congress', 'senate', 'bill', 'act', 'fine', 'penalty'
            ],
            'weight': 1.0
        },
        'seasonal': {
            'keywords': [
                'year-end', 'q4', 'holiday', 'festival', 'quarter-end', 'year end',
                'seasonal', 'quarter-end', 'fiscal quarter', 'christmas', 'thanksgiving',
                'diwali', 'new year', 'summer', 'winter', 'spring', 'autumn', 'quarterly close'
            ],
            'weight': 0.9
        },
        'technical': {
            'keywords': [
                'ipo', 'split', 'dividend', 'buyback', 'listing', 'delisting', 'spin-off',
                'merger', 'acquisition', 'takeover', 'deal', 'consolidation', 'tender offer',
                'stock split', 'reverse split', 'share buyback', 'share repurchase',
                'rights issue', 'bonus issue', 'dilution', 'warrant', 'convertible'
            ],
            'weight': 1.0
        },
        'sector': {
            'keywords': [
                'industry', 'sector', 'competitor', 'rival', 'commodity', 'oil', 'gold',
                'market trend', 'industry trend', 'peer', 'competition', 'competitive',
                'technology', 'retail', 'healthcare', 'banking', 'energy', 'automotive',
                'pharmaceutical', 'consumer', 'industrial', 'infrastructure'
            ],
            'weight': 0.8
        },
        'merger': {
            'keywords': [
                'merger', 'acquisition', 'takeover', 'acquired', 'acquires', 'deal',
                'combination', 'consolidation', 'buyout', 'bid', 'offer', 'purchase',
                'acquired by', 'merged with', 'joint venture', 'partnership agreement',
                'strategic investment', 'stake', 'stake purchase'
            ],
            'weight': 1.0
        },
        'dividend': {
            'keywords': [
                'dividend', 'payout', 'distribution', 'special dividend', 'interim dividend',
                'final dividend', 'dividend announcement', 'yield', 'dps', 'ex-date',
                'record date', 'payment date', 'dividend increase', 'dividend cut',
                'dividend suspension', 'dividend per share'
            ],
            'weight': 1.0
        },
        'management': {
            'keywords': [
                'ceo', 'cfo', 'cto', 'management', 'executive', 'appointed', 'joins',
                'resignation', 'retires', 'retirement', 'stepping down', 'leadership',
                'board', 'director', 'president', 'vice president', 'founder', 'chairman',
                'promotion', 'new hire', 'departure', 'resignation', 'interim'
            ],
            'weight': 1.0
        }
    }

    def __init__(self):
        """Initialize categorizer with compiled regex patterns"""
        self.compiled_patterns = self._compile_patterns()
        logger.info("EventCategorizer initialized with %d categories", len(self.CATEGORY_KEYWORDS))

    def _compile_patterns(self) -> Dict[str, List]:
        """
        Compile regex patterns for each category keyword.
        Returns dict of category -> compiled patterns
        """
        compiled = {}
        for category, data in self.CATEGORY_KEYWORDS.items():
            patterns = []
            for keyword in data['keywords']:
                # Create case-insensitive word boundary patterns
                # Use \b for word boundaries to avoid partial matches
                pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                patterns.append(pattern)
            compiled[category] = patterns
        return compiled

    def categorize_event(
        self,
        headline: str,
        content: str = "",
        return_all: bool = False
    ) -> Tuple[str, float, Dict[str, float]]:
        """
        Categorize a news event into primary and secondary categories.

        Args:
            headline: News headline
            content: Full article content (optional, improves accuracy)
            return_all: If True, return all category scores; if False, return top category only

        Returns:
            Tuple of (primary_category, confidence, all_scores)
            - primary_category: str, the top category
            - confidence: float 0-1, confidence in the categorization
            - all_scores: dict of category -> confidence scores
        """
        if not headline or (not headline.strip() and not content.strip()):
            logger.warning("Empty headline and content provided to categorizer")
            return 'sector', 0.0, {}

        # Combine headline and content for analysis
        combined_text = f"{headline} {content}".strip()
        text_lower = combined_text.lower()

        # Count keyword matches for each category
        category_scores = {}
        keyword_counts = {}

        for category, patterns in self.compiled_patterns.items():
            match_count = 0
            for pattern in patterns:
                matches = pattern.findall(text_lower)
                match_count += len(matches)

            if match_count > 0:
                keyword_counts[category] = match_count

        if not keyword_counts:
            # No matches found - default to sector with low confidence
            logger.debug("No category keywords found for event: %s", headline[:50])
            return 'sector', 0.1, {'sector': 0.1}

        # Calculate confidence scores (0-1)
        max_matches = max(keyword_counts.values())
        total_text_length = len(combined_text.split())

        for category, count in keyword_counts.items():
            # Normalize by max matches and apply weight
            weight = self.CATEGORY_KEYWORDS[category]['weight']

            # Confidence = (match_count / max_matches) * weight * (matches / text_length boost)
            # The more matches relative to text length, the higher confidence
            match_ratio = count / max_matches
            text_density = min(count / max(total_text_length / 10, 1), 1.0)

            confidence = (match_ratio * weight) * 0.7 + (text_density * weight) * 0.3
            category_scores[category] = min(confidence, 1.0)

        # Get primary category (highest score)
        primary_category = max(category_scores.items(), key=lambda x: x[1])
        primary_name = primary_category[0]
        primary_confidence = primary_category[1]

        # Filter for secondary categories (>50% of primary confidence)
        secondary_threshold = primary_confidence * 0.5
        secondary_categories = {
            cat: score for cat, score in category_scores.items()
            if cat != primary_name and score >= secondary_threshold
        }

        # Log categorization result
        logger.debug(
            "Event categorized: primary=%s (confidence=%.2f), secondaries=%s",
            primary_name,
            primary_confidence,
            list(secondary_categories.keys())
        )

        if return_all:
            return primary_name, primary_confidence, category_scores
        else:
            return primary_name, primary_confidence, secondary_categories

    def get_all_categories(self) -> List[str]:
        """Get list of all supported categories"""
        return list(self.CATEGORY_KEYWORDS.keys())

    def batch_categorize(
        self,
        events: List[Dict[str, str]]
    ) -> List[Tuple[str, float, Dict]]:
        """
        Categorize multiple events efficiently.

        Args:
            events: List of dicts with 'headline' and optional 'content' keys

        Returns:
            List of categorization tuples
        """
        results = []
        for event in events:
            headline = event.get('headline', '')
            content = event.get('content', '')
            result = self.categorize_event(headline, content, return_all=True)
            results.append(result)

        return results
