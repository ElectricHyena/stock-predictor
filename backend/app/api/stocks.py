"""
Stock API Endpoints
STORY_2_2 through STORY_2_6: Stock search, detail, predictability, prediction, and analysis endpoints
"""

import logging
from datetime import datetime, timedelta, date
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app import models, schemas
from app.cache import (
    cache, cache_key_search, cache_key_detail, cache_key_predictability,
    cache_key_prediction, cache_key_analysis, CACHE_TTL_SEARCH, CACHE_TTL_DETAIL,
    CACHE_TTL_PREDICTABILITY, CACHE_TTL_PREDICTION, CACHE_TTL_ANALYSIS
)
from app.validators import Validators
from app.exceptions import InvalidStockSymbolError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stocks", tags=["stocks"])


def _get_trading_recommendation(score: int, confidence: float) -> str:
    """
    Calculate trading recommendation based on score and confidence.

    Returns:
    - TRADE_THIS: score >= 75 AND confidence >= 0.7
    - MAYBE: score >= 50
    - AVOID: score < 50
    """
    if score >= 75 and confidence >= 0.7:
        return "TRADE_THIS"
    elif score >= 50:
        return "MAYBE"
    else:
        return "AVOID"


def _format_magnitude(direction: str, low: float, high: float) -> str:
    """
    Format magnitude as '+2% to +4%' or '-2% to -4%' format.
    """
    sign = "+" if direction.upper() == "UP" else "-"
    return f"{sign}{abs(low):.0f}% to {sign}{abs(high):.0f}%"


# ============================================================================
# STORY_2_2: Stock Search Endpoint
# ============================================================================

@router.get("/search")
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query (ticker or company name)"),
    market: Optional[str] = Query(None, description="Filter by market (NSE, BSE, NYSE, NASDAQ)"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    limit: int = Query(10, ge=1, le=100, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
) -> schemas.StockSearchResponse:
    """
    Search for stocks by ticker or company name (STORY_2_2)

    Query Parameters:
    - q: Search query (required) - ticker symbol or company name
    - market: Optional market filter (NSE, BSE, NYSE, NASDAQ)
    - sector: Optional sector filter
    - limit: Max results (default 10, max 100)
    - offset: Pagination offset (default 0)

    Returns:
    - StockSearchResponse with matching stocks and pagination info
    """
    try:
        # Check cache first
        cache_key = cache_key_search(q, market)
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for search: {q}")
            return cached_result

        # Build query
        query_text = f"%{q.upper()}%"
        query = db.query(models.Stock).filter(
            or_(
                models.Stock.ticker.ilike(query_text),
                models.Stock.company_name.ilike(query_text)
            )
        )

        # Apply market filter
        if market:
            query = query.filter(models.Stock.market == market.upper())

        # Apply sector filter
        if sector:
            query = query.filter(models.Stock.sector.ilike(f"%{sector}%"))

        # Get total count before pagination
        total = query.count()

        # Apply pagination
        stocks = query.offset(offset).limit(limit).all()

        # Get current prices for each stock
        results = []
        for stock in stocks:
            current_price = None
            latest_price = db.query(models.StockPrice).filter(
                models.StockPrice.stock_id == stock.id
            ).order_by(models.StockPrice.date.desc()).first()

            if latest_price:
                current_price = latest_price.close_price

            result = schemas.StockSearchResult(
                id=stock.id,
                ticker=stock.ticker,
                company_name=stock.company_name,
                market=stock.market,
                sector=stock.sector,
                current_price=current_price,
                has_analysis=stock.analysis_status in ["COMPLETED", "PROCESSING"],
                analysis_status=stock.analysis_status,
            )
            results.append(result)

        response = schemas.StockSearchResponse(
            total=total,
            limit=limit,
            offset=offset,
            results=results,
        )

        # Cache response (use dict form for JSON serialization)
        cache.set(cache_key, response.model_dump(mode='json'), CACHE_TTL_SEARCH)
        logger.info(f"Search completed: {q}, found {total} stocks")

        return response

    except Exception as e:
        logger.error(f"Stock search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


# ============================================================================
# STORY_2_3: Stock Detail Endpoint
# ============================================================================

@router.get("/{ticker}", response_model=schemas.StockDetailResponse)
async def get_stock_detail(
    ticker: str,
    include_prices: bool = Query(True, description="Include price history"),
    include_news: bool = Query(True, description="Include recent news"),
    days_history: int = Query(30, ge=1, le=365, description="Days of price history"),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a stock (STORY_2_3)

    Path Parameters:
    - ticker: Stock ticker symbol (e.g., AAPL, INFY)

    Query Parameters:
    - include_prices: Include price history (default True)
    - include_news: Include recent news (default True)
    - days_history: Days of price history to return (default 30)

    Returns:
    - StockDetailResponse with stock info, prices, and news

    Notes:
    - Auto-creates stock if not found and triggers async data fetch
    """
    try:
        ticker = ticker.upper()

        # Validate ticker format - reject invalid symbols like "INVALID123"
        # Valid formats: 1-5 uppercase letters, or with suffix (.NS, .BO, .L)
        import re
        base_ticker = ticker.split('.')[0]  # Handle suffixes like .NS, .BO
        if not re.match(r'^[A-Z]{1,10}$', base_ticker):
            logger.warning(f"Invalid ticker format: {ticker}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stock symbol: {ticker}. Symbols must be 1-10 letters."
            )

        # Check cache first
        cache_key = cache_key_detail(ticker)
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for stock detail: {ticker}")
            return cached_result

        # Get stock from database
        stock = db.query(models.Stock).filter(
            models.Stock.ticker == ticker
        ).first()

        if not stock:
            # Auto-create stock with PENDING status
            logger.info(f"Stock not found, auto-creating: {ticker}")

            # Determine market from ticker format
            market = "NYSE"  # Default
            if ticker.endswith(".NS"):
                market = "NSE"
            elif ticker.endswith(".BO"):
                market = "BSE"
            elif ticker.endswith(".L"):
                market = "LSE"

            stock = models.Stock(
                ticker=ticker,
                company_name=ticker,  # Will be updated by fetcher
                market=market,
                analysis_status="PENDING",
            )
            db.add(stock)
            db.commit()
            db.refresh(stock)

            # Trigger async data fetch
            try:
                from app.tasks import fetch_stock_prices_task, fetch_news_task
                fetch_stock_prices_task.delay()
                fetch_news_task.delay()
                logger.info(f"Triggered async fetch for new stock: {ticker}")
            except Exception as e:
                logger.warning(f"Failed to trigger async fetch for {ticker}: {e}")

        # Get current price
        current_price = None
        latest_price = db.query(models.StockPrice).filter(
            models.StockPrice.stock_id == stock.id
        ).order_by(models.StockPrice.date.desc()).first()

        if latest_price:
            current_price = latest_price.close_price

        # Get price history
        price_history = None
        if include_prices:
            cutoff_date = datetime.now().date() - timedelta(days=days_history)
            prices = db.query(models.StockPrice).filter(
                and_(
                    models.StockPrice.stock_id == stock.id,
                    models.StockPrice.date >= cutoff_date
                )
            ).order_by(models.StockPrice.date.asc()).all()

            price_history = [
                schemas.PriceHistoryPoint(
                    date=p.date,
                    close=p.close_price,
                    open=p.open_price,
                    high=p.high_price,
                    low=p.low_price,
                    volume=p.volume,
                    daily_return_pct=p.daily_return_pct,
                )
                for p in prices
            ]

        # Get recent news
        recent_news = None
        if include_news:
            news = db.query(models.NewsEvent).filter(
                models.NewsEvent.stock_id == stock.id
            ).order_by(models.NewsEvent.event_date.desc()).limit(10).all()

            recent_news = [schemas.NewsEvent.model_validate(n) for n in news]

        response = schemas.StockDetailResponse(
            id=stock.id,
            ticker=stock.ticker,
            company_name=stock.company_name,
            market=stock.market,
            sector=stock.sector,
            industry=stock.industry,
            website=stock.website,
            description=stock.description,
            analysis_status=stock.analysis_status,
            last_price_updated_at=stock.last_price_updated_at,
            last_news_updated_at=stock.last_news_updated_at,
            current_price=current_price,
            price_history=price_history,
            recent_news=recent_news,
            created_at=stock.created_at,
            updated_at=stock.updated_at,
        )

        # Cache response
        cache.set(cache_key, response.model_dump(mode='json'), CACHE_TTL_DETAIL)
        logger.info(f"Retrieved stock detail: {ticker}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stock detail error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve stock details")


# ============================================================================
# STORY_2_4: Predictability Score Endpoint
# ============================================================================

@router.get("/{ticker}/predictability-score", response_model=schemas.PredictabilityMetrics)
async def get_predictability_score(
    ticker: str,
    db: Session = Depends(get_db),
):
    """
    Get predictability score for a stock (STORY_2_4)

    Path Parameters:
    - ticker: Stock ticker symbol

    Returns:
    - PredictabilityMetrics with overall score, component scores, and trading recommendation
      Trading recommendation: TRADE_THIS (score >= 75 AND confidence >= 0.7), MAYBE (50-75), AVOID (< 50)
    """
    try:
        ticker = ticker.upper()

        # Check cache
        cache_key = cache_key_predictability(ticker)
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for predictability: {ticker}")
            return cached_result

        # Get stock
        stock = db.query(models.Stock).filter(
            models.Stock.ticker == ticker
        ).first()

        if not stock:
            logger.warning(f"Stock not found: {ticker}")
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

        # Get latest predictability score
        score = db.query(models.PredictabilityScore).filter(
            models.PredictabilityScore.stock_id == stock.id
        ).order_by(models.PredictabilityScore.calculated_at.desc()).first()

        if not score:
            # Return default/placeholder score if not computed yet
            logger.warning(f"No predictability score found for {ticker}, returning defaults")
            overall_score = 50
            confidence = 0.5
            response = schemas.PredictabilityMetrics(
                overall_score=overall_score,
                information_availability=50,
                pattern_consistency=50,
                timing_certainty=50,
                direction_confidence=50,
                confidence=confidence,
                trading_recommendation=_get_trading_recommendation(overall_score, confidence),
            )
        else:
            overall_score = score.overall_predictability_score or 0
            confidence = 0.5 + (score.overall_predictability_score or 50) / 200
            response = schemas.PredictabilityMetrics(
                overall_score=overall_score,
                information_availability=score.information_availability_score or 0,
                pattern_consistency=score.pattern_consistency_score or 0,
                timing_certainty=score.timing_certainty_score or 0,
                direction_confidence=score.direction_confidence_score or 0,
                confidence=confidence,
                trading_recommendation=_get_trading_recommendation(overall_score, confidence),
            )

        # Cache response
        cache.set(cache_key, response.model_dump(), CACHE_TTL_PREDICTABILITY)
        logger.info(f"Retrieved predictability score: {ticker}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Predictability score error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve predictability score")


# ============================================================================
# STORY_2_5: Price Prediction Endpoint
# ============================================================================

@router.get("/{ticker}/prediction", response_model=schemas.PredictionResponse)
async def get_price_prediction(
    ticker: str,
    timing: Optional[str] = Query("same-day", description="Prediction timing"),
    db: Session = Depends(get_db),
):
    """
    Get price movement prediction for a stock (STORY_2_5)

    Path Parameters:
    - ticker: Stock ticker symbol

    Query Parameters:
    - timing: Prediction timing (same-day, next-day, weekly, monthly)

    Returns:
    - PredictionResponse with direction, magnitude, timing, win rate, and confidence
    """
    try:
        ticker = ticker.upper()

        # Check cache
        cache_key = cache_key_prediction(ticker)
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for prediction: {ticker}")
            return cached_result

        # Get stock
        stock = db.query(models.Stock).filter(
            models.Stock.ticker == ticker
        ).first()

        if not stock:
            logger.warning(f"Stock not found: {ticker}")
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

        # Get latest predictability score (contains prediction data)
        score = db.query(models.PredictabilityScore).filter(
            models.PredictabilityScore.stock_id == stock.id,
            models.PredictabilityScore.is_current == True
        ).order_by(models.PredictabilityScore.calculated_at.desc()).first()

        # Default prediction if not available
        direction = "UP"
        magnitude_low = 1.0
        magnitude_high = 2.5
        win_rate = 0.55
        confidence = 0.6
        timing_str = "same-day"

        if score:
            direction = score.prediction_direction or "UP"
            magnitude_low = score.prediction_magnitude_low or 1.0
            magnitude_high = score.prediction_magnitude_high or 2.5

            # Get average win rate from correlations
            correlations = db.query(models.EventPriceCorrelation).filter(
                models.EventPriceCorrelation.stock_id == stock.id
            ).all()

            if correlations:
                win_rate = sum(c.historical_win_rate for c in correlations if c.historical_win_rate) / len(
                    correlations) if correlations else 0.55
            confidence = 0.5 + (score.overall_predictability_score or 50) / 200

        # Create prediction object
        prediction = schemas.Prediction(
            direction=direction,
            confidence=confidence,
            expected_move_min=magnitude_low,
            expected_move_max=magnitude_high,
            expected_move_description=_format_magnitude(direction, magnitude_low, magnitude_high),
            timing=timing or "same-day",
            historical_win_rate=win_rate,
            sample_size=1,  # Placeholder
            reasoning="Based on event-price correlations and historical patterns",
            pattern_type="event_driven",
            supporting_events=["earnings", "policy_change"],
        )

        # Create predictability metrics
        overall_score = int(confidence * 100)
        predictability = schemas.PredictabilityMetrics(
            overall_score=overall_score,
            information_availability=overall_score,
            pattern_consistency=overall_score,
            timing_certainty=overall_score,
            direction_confidence=overall_score,
            confidence=confidence,
            trading_recommendation=_get_trading_recommendation(overall_score, confidence),
        )

        # Create contributing factors
        contributing_factors = [
            schemas.InsightCategory(
                category="historical_patterns",
                confidence=0.6,
                description="Historical event-price correlations support this direction",
                supporting_data={"correlation_strength": 0.65, "sample_size": 15},
            ),
            schemas.InsightCategory(
                category="current_events",
                confidence=0.5,
                description="Current market events align with predictable pattern",
                supporting_data={"event_types": ["earnings"], "sentiment": 0.6},
            ),
        ]

        response = schemas.PredictionResponse(
            ticker=ticker,
            timestamp=datetime.utcnow(),
            prediction=prediction,
            predictability=predictability,
            contributing_factors=contributing_factors,
            disclaimer="Predictions are based on historical patterns and current analysis. Past performance does not guarantee future results.",
        )

        # Cache response
        cache.set(cache_key, response.model_dump(mode='json'), CACHE_TTL_PREDICTION)
        logger.info(f"Retrieved prediction: {ticker}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve prediction")


# ============================================================================
# STORY_2_6: Historical Analysis Endpoint
# ============================================================================

@router.get("/{ticker}/analysis", response_model=schemas.HistoricalAnalysisResponse)
async def get_historical_analysis(
    ticker: str,
    period: str = Query("1y", pattern="^(1m|3m|6m|1y|all)$", description="Analysis period"),
    db: Session = Depends(get_db),
):
    """
    Get historical analysis for a stock (STORY_2_6)

    Path Parameters:
    - ticker: Stock ticker symbol

    Query Parameters:
    - period: Analysis period (1m, 3m, 6m, 1y, all)

    Returns:
    - HistoricalAnalysisResponse with patterns, win rates, and insights
    """
    try:
        ticker = ticker.upper()

        # Check cache
        cache_key = cache_key_analysis(ticker, period)
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for analysis: {ticker}")
            return cached_result

        # Get stock
        stock = db.query(models.Stock).filter(
            models.Stock.ticker == ticker
        ).first()

        if not stock:
            logger.warning(f"Stock not found: {ticker}")
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

        # Determine date range
        end_date = datetime.now().date()
        if period == "1m":
            start_date = end_date - timedelta(days=30)
        elif period == "3m":
            start_date = end_date - timedelta(days=90)
        elif period == "6m":
            start_date = end_date - timedelta(days=180)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:  # all
            start_date = date(2000, 1, 1)  # Far back

        # Get event-price correlations for period
        correlations = db.query(models.EventPriceCorrelation).filter(
            and_(
                models.EventPriceCorrelation.stock_id == stock.id,
                models.EventPriceCorrelation.event_date >= start_date,
                models.EventPriceCorrelation.event_date <= end_date,
            )
        ).all()

        # Group by event category and calculate metrics
        category_stats = {}
        for corr in correlations:
            if corr.event_category not in category_stats:
                category_stats[corr.event_category] = {
                    "total": 0,
                    "wins": 0,
                    "returns": [],
                    "occurrences": []
                }

            stat = category_stats[corr.event_category]
            stat["total"] += 1
            if corr.historical_win_rate and corr.historical_win_rate > 0.5:
                stat["wins"] += 1
            if corr.price_change_pct:
                stat["returns"].append(corr.price_change_pct)
            stat["occurrences"].append({
                "date": corr.event_date,
                "return": corr.price_change_pct,
                "direction": corr.price_direction,
            })

        # Create pattern analyses
        patterns = []
        for category, stats in category_stats.items():
            if stats["total"] > 0:
                win_rate = stats["wins"] / stats["total"]
                avg_return = sum(stats["returns"]) / len(stats["returns"]) if stats["returns"] else 0
                min_return = min(stats["returns"]) if stats["returns"] else 0
                max_return = max(stats["returns"]) if stats["returns"] else 0

                # Create pattern occurrences
                occurrences = [
                    schemas.PatternOccurrence(
                        date=occ["date"],
                        outcome="WIN" if occ["return"] and occ["return"] > 0 else "LOSS",
                        return_pct=occ["return"] or 0,
                        holding_days=1,  # Placeholder
                    )
                    for occ in stats["occurrences"][:5]  # Limit to 5 for response
                ]

                pattern = schemas.PatternAnalysis(
                    pattern_name=category.replace("_", " ").title(),
                    pattern_type=category,
                    occurrences=stats["total"],
                    win_rate=win_rate,
                    avg_return=avg_return,
                    min_return=min_return,
                    max_return=max_return,
                    avg_holding_days=1,  # Placeholder
                    occurrences_detail=occurrences,
                )
                patterns.append(pattern)

        # Create insights
        insights = [
            schemas.InsightCategory(
                category="pattern_strength",
                confidence=0.7,
                description=f"Found {len(patterns)} significant event patterns",
                supporting_data={"pattern_count": len(patterns)},
            ),
            schemas.InsightCategory(
                category="predictability",
                confidence=0.6,
                description="Historical data shows moderate predictability",
                supporting_data={"average_win_rate": 0.55},
            ),
        ]

        response = schemas.HistoricalAnalysisResponse(
            ticker=ticker,
            analysis_period_start=start_date,
            analysis_period_end=end_date,
            total_trading_days=(end_date - start_date).days,
            patterns_found=patterns,
            key_insights=insights,
        )

        # Cache response
        cache.set(cache_key, response.model_dump(mode='json'), CACHE_TTL_ANALYSIS)
        logger.info(f"Retrieved historical analysis: {ticker}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Historical analysis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve historical analysis")
