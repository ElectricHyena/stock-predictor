"""
Smart Data Manager - Intelligent data fetching with sync tracking.

This module implements a smart caching strategy:
1. FIRST VISIT: Full data load from Screener.in (all historical data)
2. SUBSEQUENT VISITS: Only fetch what's changed (prices, new quarters)

Key Principles:
- Minimize Screener.in requests (avoid rate limiting, respect the source)
- Store everything in database (single source of truth)
- Track sync status to know when data needs refresh
- Use lightweight price updates for real-time data
"""

import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models import (
    Stock, StockInfo, StockFinancial, StockCashflow, StockRatio,
    StockSyncStatus, StockBalanceSheet, StockShareholding
)
from app.exceptions import InvalidTickerError, DataValidationError
from app.services.screener_scraper import ScreenerScraper, RateLimitConfig, get_scraper
from app.services.data_fetchers import YahooFinanceFetcher

logger = logging.getLogger(__name__)


class SyncType(Enum):
    """Types of data synchronization"""
    FULL = "full"           # Complete data fetch (first time or refresh)
    PRICE_ONLY = "price"    # Just current price update
    QUARTERLY = "quarterly"  # New quarterly results available
    NONE = "none"           # Use cached data


class RefreshStrategy(Enum):
    """When to refresh different data types"""
    ALWAYS = "always"       # Fetch every request
    STALE = "stale"         # Fetch if older than threshold
    NEVER = "never"         # Never auto-refresh


# Refresh thresholds (in hours)
REFRESH_THRESHOLDS = {
    'price': 0.25,          # 15 minutes for price
    'quarterly': 24 * 30,   # 30 days for quarterly (check after earnings)
    'annual': 24 * 90,      # 90 days for annual
    'full': 24 * 180,       # 180 days for full re-sync
}


class SmartDataManager:
    """
    Intelligent data manager that minimizes external requests.

    Strategy:
    1. Check database first for existing data
    2. Check sync status to determine what needs updating
    3. Fetch only what's necessary
    4. Update sync timestamps
    """

    def __init__(self, db_session: Session, scraper: Optional[ScreenerScraper] = None):
        self.session = db_session
        self.scraper = scraper or get_scraper(
            rate_config=RateLimitConfig(min_delay=2.5, max_delay=5.0),
            cache_ttl=3600
        )

    def _safe_decimal(self, value: Any) -> Optional[Decimal]:
        """Safely convert value to Decimal."""
        if value is None:
            return None
        try:
            if isinstance(value, Decimal):
                return value
            return Decimal(str(float(value)))
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int."""
        if value is None:
            return None
        try:
            if isinstance(value, int):
                return value
            if isinstance(value, Decimal):
                return int(value)
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def get_or_create_sync_status(self, stock_id: int) -> StockSyncStatus:
        """Get or create sync status for a stock."""
        sync_status = self.session.query(StockSyncStatus).filter_by(stock_id=stock_id).first()

        if not sync_status:
            sync_status = StockSyncStatus(
                stock_id=stock_id,
                sync_status="PENDING",
                primary_source="screener"
            )
            self.session.add(sync_status)
            self.session.commit()

        return sync_status

    def determine_sync_type(self, stock_id: int) -> SyncType:
        """
        Determine what type of sync is needed based on current data state.

        Returns:
            SyncType indicating what needs to be fetched
        """
        sync_status = self.session.query(StockSyncStatus).filter_by(stock_id=stock_id).first()

        # No sync status = first time = full sync needed
        if not sync_status or not sync_status.last_full_sync:
            logger.info(f"Stock {stock_id}: No previous sync, needs FULL sync")
            return SyncType.FULL

        now = datetime.utcnow()

        # Check if full sync is stale (> 6 months)
        full_sync_age = (now - sync_status.last_full_sync).total_seconds() / 3600
        if full_sync_age > REFRESH_THRESHOLDS['full']:
            logger.info(f"Stock {stock_id}: Full sync stale ({full_sync_age:.0f}h old), needs FULL sync")
            return SyncType.FULL

        # Check if quarterly data needs refresh (new quarter available)
        if sync_status.latest_quarter_end:
            months_since_quarter = (now.date() - sync_status.latest_quarter_end).days / 30
            if months_since_quarter > 3.5:  # More than ~3.5 months since last quarter
                logger.info(f"Stock {stock_id}: New quarter likely available, needs QUARTERLY sync")
                return SyncType.QUARTERLY

        # Check if price is stale (> 15 minutes)
        if sync_status.last_price_sync:
            price_age = (now - sync_status.last_price_sync).total_seconds() / 3600
            if price_age > REFRESH_THRESHOLDS['price']:
                logger.info(f"Stock {stock_id}: Price stale ({price_age*60:.0f}m old), needs PRICE sync")
                return SyncType.PRICE_ONLY

        # Data is fresh, use cache
        logger.info(f"Stock {stock_id}: Data is fresh, using cache")
        return SyncType.NONE

    def full_sync(self, symbol: str, market: str = "NSE") -> Dict[str, Any]:
        """
        Perform a complete data sync from Screener.in.

        This fetches ALL available data:
        - Company info and key metrics
        - All quarterly results (13+ quarters)
        - All annual P&L (12+ years)
        - All cash flow statements
        - Balance sheet data
        - Financial ratios
        - Shareholding pattern

        Args:
            symbol: Stock symbol (e.g., "INFY")
            market: Exchange (NSE or BSE)

        Returns:
            Dict with sync results
        """
        logger.info(f"Starting FULL sync for {symbol}.{market}")

        # Fetch all data from Screener.in
        data = self.scraper.fetch_company_data(symbol, consolidated=True)

        if not data:
            raise InvalidTickerError(f"Could not fetch data for {symbol} from Screener.in")

        # Build ticker
        ticker = f"{symbol.upper()}.{'NS' if market == 'NSE' else 'BO'}"

        # Get or create stock
        stock = self.session.query(Stock).filter_by(ticker=ticker).first()
        if not stock:
            stock = Stock(
                ticker=ticker,
                company_name=data.get('company_name', symbol),
                market=market.upper(),
                sector=data.get('sector'),
                industry=data.get('industry'),
                analysis_status="PENDING"
            )
            self.session.add(stock)
            self.session.commit()
        else:
            # Update stock info
            stock.company_name = data.get('company_name', stock.company_name)
            stock.sector = data.get('sector') or stock.sector
            stock.industry = data.get('industry') or stock.industry

        # Save all data
        records = {
            'stock_info': 0,
            'quarterly_results': 0,
            'annual_results': 0,
            'cashflow': 0,
            'balance_sheet': 0,
            'ratios': 0,
            'shareholding': 0,
            'price_history': 0,
        }

        # Save stock info
        self._save_stock_info(stock.id, data)
        records['stock_info'] = 1

        # Save quarterly results
        for record in data.get('quarterly_results', []):
            if self._save_financial_record(stock.id, record, 'quarterly'):
                records['quarterly_results'] += 1

        # Save annual results
        for record in data.get('annual_results', []):
            if self._save_financial_record(stock.id, record, 'annual'):
                records['annual_results'] += 1

        # Save cash flow
        for record in data.get('cashflow', []):
            if self._save_cashflow_record(stock.id, record):
                records['cashflow'] += 1

        # Save balance sheet
        for record in data.get('balance_sheet', []):
            if self._save_balance_sheet_record(stock.id, record):
                records['balance_sheet'] += 1

        # Save ratios
        for record in data.get('ratios', []):
            if self._save_ratio_record(stock.id, record):
                records['ratios'] += 1

        # Save shareholding pattern
        for record in data.get('shareholding', []):
            if self._save_shareholding_record(stock.id, record):
                records['shareholding'] += 1

        # Fetch historical price data from Yahoo Finance
        records['price_history'] = 0
        try:
            price_fetcher = YahooFinanceFetcher(self.session)
            inserted, updated = price_fetcher.fetch_and_save(ticker)
            records['price_history'] = inserted + updated
            logger.info(f"Fetched {records['price_history']} price records for {ticker}")
        except Exception as e:
            logger.warning(f"Failed to fetch price history for {ticker}: {e}")

        # Update sync status
        sync_status = self.get_or_create_sync_status(stock.id)
        sync_status.last_full_sync = datetime.utcnow()
        sync_status.last_price_sync = datetime.utcnow()
        sync_status.last_quarterly_sync = datetime.utcnow()
        sync_status.last_annual_sync = datetime.utcnow()
        sync_status.sync_status = "COMPLETE"
        sync_status.primary_source = "screener"
        sync_status.quarters_available = records['quarterly_results']
        sync_status.years_available = records['annual_results']

        # Set latest period dates
        if data.get('quarterly_results'):
            dates = [r.get('period_end') for r in data['quarterly_results'] if r.get('period_end')]
            if dates:
                sync_status.latest_quarter_end = max(dates)

        if data.get('annual_results'):
            dates = [r.get('period_end') for r in data['annual_results'] if r.get('period_end')]
            if dates:
                sync_status.latest_annual_end = max(dates)

        self.session.commit()

        logger.info(f"FULL sync complete for {ticker}: {records}")
        return {
            'stock_id': stock.id,
            'ticker': ticker,
            'company_name': data.get('company_name'),
            'sync_type': 'full',
            'records_saved': records,
        }

    def price_sync(self, stock_id: int, ticker: str) -> Dict[str, Any]:
        """
        Lightweight price-only sync using yfinance.

        Much faster than full Screener scrape - just gets current price.

        Args:
            stock_id: Database stock ID
            ticker: Full ticker symbol (e.g., "INFY.NS")

        Returns:
            Dict with updated price info
        """
        logger.info(f"Starting PRICE sync for {ticker}")

        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            info = stock.info

            current_price = info.get('regularMarketPrice') or info.get('currentPrice')

            if current_price:
                # Update stock_info table
                stock_info = self.session.query(StockInfo).filter_by(stock_id=stock_id).first()
                if stock_info:
                    stock_info.current_price = self._safe_decimal(current_price)
                    stock_info.previous_close = self._safe_decimal(info.get('previousClose'))
                    stock_info.day_high = self._safe_decimal(info.get('dayHigh'))
                    stock_info.day_low = self._safe_decimal(info.get('dayLow'))
                    stock_info.volume = info.get('volume')
                    stock_info.last_updated = datetime.utcnow()
                    stock_info.data_source = 'yahoo'

                # Update sync status
                sync_status = self.get_or_create_sync_status(stock_id)
                sync_status.last_price_sync = datetime.utcnow()
                sync_status.price_source = 'yahoo'

                self.session.commit()

                logger.info(f"PRICE sync complete for {ticker}: ₹{current_price}")
                return {
                    'sync_type': 'price',
                    'current_price': current_price,
                    'source': 'yahoo'
                }

        except Exception as e:
            logger.warning(f"Price sync failed for {ticker}: {e}")

        return {'sync_type': 'price', 'error': 'Failed to fetch price'}

    def get_stock_data(
        self,
        symbol: str,
        market: str = "NSE",
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get complete stock data, fetching from source only if needed.

        This is the main entry point. It:
        1. Checks if stock exists in database
        2. Determines what sync is needed
        3. Performs necessary sync
        4. Returns complete data from database

        Args:
            symbol: Stock symbol (e.g., "INFY")
            market: Exchange (NSE or BSE)
            force_refresh: Force full sync regardless of cache

        Returns:
            Complete stock data from database
        """
        ticker = f"{symbol.upper()}.{'NS' if market == 'NSE' else 'BO'}"

        # Check if stock exists
        stock = self.session.query(Stock).filter_by(ticker=ticker).first()

        if not stock or force_refresh:
            # First time or forced refresh - do full sync
            result = self.full_sync(symbol, market)
            stock = self.session.query(Stock).filter_by(ticker=ticker).first()
        else:
            # Determine what sync is needed
            sync_type = self.determine_sync_type(stock.id)

            if sync_type == SyncType.FULL:
                self.full_sync(symbol, market)
            elif sync_type == SyncType.QUARTERLY:
                # For now, do full sync for quarterly updates
                # Could be optimized to just fetch new quarters
                self.full_sync(symbol, market)
            elif sync_type == SyncType.PRICE_ONLY:
                self.price_sync(stock.id, ticker)
            # NONE = use cached data

        # Return complete data from database
        return self._get_stock_data_from_db(stock.id, ticker)

    def _get_stock_data_from_db(self, stock_id: int, ticker: str) -> Dict[str, Any]:
        """Retrieve all stock data from database."""
        stock = self.session.query(Stock).filter_by(id=stock_id).first()
        if not stock:
            return None

        # Get stock info
        info = self.session.query(StockInfo).filter_by(stock_id=stock_id).first()

        # Get sync status
        sync_status = self.session.query(StockSyncStatus).filter_by(stock_id=stock_id).first()

        # Get quarterly financials (all available)
        quarterly = (
            self.session.query(StockFinancial)
            .filter_by(stock_id=stock_id, period_type='quarterly')
            .order_by(StockFinancial.period_end.desc())
            .all()
        )

        # Get annual financials (all available)
        annual = (
            self.session.query(StockFinancial)
            .filter_by(stock_id=stock_id, period_type='annual')
            .order_by(StockFinancial.period_end.desc())
            .all()
        )

        # Get cash flows
        cashflows = (
            self.session.query(StockCashflow)
            .filter_by(stock_id=stock_id, period_type='annual')
            .order_by(StockCashflow.period_end.desc())
            .all()
        )

        # Get balance sheets
        balance_sheets = (
            self.session.query(StockBalanceSheet)
            .filter_by(stock_id=stock_id, period_type='annual')
            .order_by(StockBalanceSheet.period_end.desc())
            .all()
        )

        # Get shareholding
        shareholdings = (
            self.session.query(StockShareholding)
            .filter_by(stock_id=stock_id)
            .order_by(StockShareholding.period_end.desc())
            .all()
        )

        return {
            'stock': stock,
            'ticker': ticker,
            'info': info,
            'sync_status': sync_status,
            'quarterly_financials': quarterly,
            'annual_financials': annual,
            'cashflows': cashflows,
            'balance_sheets': balance_sheets,
            'shareholdings': shareholdings,
            'data_freshness': {
                'last_full_sync': sync_status.last_full_sync if sync_status else None,
                'last_price_sync': sync_status.last_price_sync if sync_status else None,
                'quarters_available': len(quarterly),
                'years_available': len(annual),
            }
        }

    def _save_stock_info(self, stock_id: int, data: Dict[str, Any]) -> bool:
        """Save or update stock info."""
        try:
            stock_info = self.session.query(StockInfo).filter_by(stock_id=stock_id).first()

            if not stock_info:
                stock_info = StockInfo(stock_id=stock_id)
                self.session.add(stock_info)

            stock_info.current_price = self._safe_decimal(data.get('current_price'))
            stock_info.market_cap = self._safe_decimal(data.get('market_cap'))
            stock_info.pe_ratio = self._safe_decimal(data.get('pe_ratio'))
            stock_info.pb_ratio = self._safe_decimal(data.get('pb_ratio'))
            stock_info.book_value = self._safe_decimal(data.get('book_value'))
            stock_info.dividend_yield = self._safe_decimal(data.get('dividend_yield'))
            stock_info.roe = self._safe_decimal(data.get('roe'))
            stock_info.roce = self._safe_decimal(data.get('roce'))
            stock_info.fifty_two_week_high = self._safe_decimal(data.get('fifty_two_week_high'))
            stock_info.fifty_two_week_low = self._safe_decimal(data.get('fifty_two_week_low'))
            stock_info.face_value = self._safe_decimal(data.get('face_value'))
            stock_info.currency = 'INR'
            stock_info.data_source = 'screener'
            stock_info.last_updated = datetime.utcnow()

            return True
        except Exception as e:
            logger.warning(f"Failed to save stock info: {e}")
            return False

    def _save_financial_record(self, stock_id: int, record: Dict[str, Any], period_type: str) -> bool:
        """Save a financial record using upsert."""
        if not record.get('period_end'):
            return False

        try:
            stmt = insert(StockFinancial).values(
                stock_id=stock_id,
                period_type=period_type,
                period_end=record['period_end'],
                revenue=self._safe_decimal(record.get('sales')),
                operating_profit=self._safe_decimal(record.get('operating_profit')),
                operating_margin=self._safe_decimal(record.get('operating_margin')),
                other_income=self._safe_decimal(record.get('other_income')),
                interest_expense=self._safe_decimal(record.get('interest')),
                depreciation=self._safe_decimal(record.get('depreciation')),
                profit_before_tax=self._safe_decimal(record.get('profit_before_tax')),
                tax_expense=self._safe_decimal(record.get('tax')),
                net_profit=self._safe_decimal(record.get('net_profit')),
                eps=self._safe_decimal(record.get('eps')),
                currency='INR',
            ).on_conflict_do_update(
                constraint='uq_stock_period',
                set_={
                    'revenue': self._safe_decimal(record.get('sales')),
                    'operating_profit': self._safe_decimal(record.get('operating_profit')),
                    'net_profit': self._safe_decimal(record.get('net_profit')),
                    'eps': self._safe_decimal(record.get('eps')),
                    'updated_at': datetime.utcnow(),
                }
            )
            self.session.execute(stmt)
            return True
        except Exception as e:
            logger.warning(f"Failed to save financial record: {e}")
            return False

    def _save_cashflow_record(self, stock_id: int, record: Dict[str, Any]) -> bool:
        """Save a cash flow record using upsert."""
        if not record.get('period_end'):
            return False

        try:
            stmt = insert(StockCashflow).values(
                stock_id=stock_id,
                period_type=record.get('period_type', 'annual'),
                period_end=record['period_end'],
                operating_cashflow=self._safe_decimal(record.get('operating_cashflow')),
                investing_cashflow=self._safe_decimal(record.get('investing_cashflow')),
                financing_cashflow=self._safe_decimal(record.get('financing_cashflow')),
                net_cashflow=self._safe_decimal(record.get('net_cashflow')),
                currency='INR',
            ).on_conflict_do_update(
                constraint='uq_cashflow_period',
                set_={
                    'operating_cashflow': self._safe_decimal(record.get('operating_cashflow')),
                    'investing_cashflow': self._safe_decimal(record.get('investing_cashflow')),
                    'financing_cashflow': self._safe_decimal(record.get('financing_cashflow')),
                    'net_cashflow': self._safe_decimal(record.get('net_cashflow')),
                }
            )
            self.session.execute(stmt)
            return True
        except Exception as e:
            logger.warning(f"Failed to save cashflow record: {e}")
            return False

    def _save_balance_sheet_record(self, stock_id: int, record: Dict[str, Any]) -> bool:
        """Save a balance sheet record using upsert."""
        if not record.get('period_end'):
            return False

        try:
            # Map scraper fields to database fields
            # Note: Database has: total_assets, current_assets, non_current_assets, cash_and_equivalents,
            #       inventory, receivables, fixed_assets, investments, total_liabilities, current_liabilities,
            #       non_current_liabilities, short_term_debt, long_term_debt, total_debt, total_equity,
            #       share_capital, reserves, currency
            stmt = insert(StockBalanceSheet).values(
                stock_id=stock_id,
                period_type=record.get('period_type', 'annual'),
                period_end=record['period_end'],
                total_assets=self._safe_decimal(record.get('total_assets')),
                current_assets=self._safe_decimal(record.get('current_assets')),
                fixed_assets=self._safe_decimal(record.get('fixed_assets')),
                investments=self._safe_decimal(record.get('investments')),
                total_liabilities=self._safe_decimal(record.get('total_liabilities')),
                current_liabilities=self._safe_decimal(record.get('current_liabilities')),
                total_debt=self._safe_decimal(record.get('total_debt') or record.get('borrowings')),
                total_equity=self._safe_decimal(record.get('total_equity')),
                share_capital=self._safe_decimal(record.get('share_capital') or record.get('equity_capital')),
                reserves=self._safe_decimal(record.get('reserves')),
                currency='INR',
            ).on_conflict_do_update(
                constraint='uq_balance_sheet_period',
                set_={
                    'total_assets': self._safe_decimal(record.get('total_assets')),
                    'fixed_assets': self._safe_decimal(record.get('fixed_assets')),
                    'investments': self._safe_decimal(record.get('investments')),
                    'total_liabilities': self._safe_decimal(record.get('total_liabilities')),
                    'total_debt': self._safe_decimal(record.get('total_debt') or record.get('borrowings')),
                    'share_capital': self._safe_decimal(record.get('share_capital') or record.get('equity_capital')),
                    'reserves': self._safe_decimal(record.get('reserves')),
                    'total_equity': self._safe_decimal(record.get('total_equity')),
                    'updated_at': datetime.utcnow(),
                }
            )
            self.session.execute(stmt)
            return True
        except Exception as e:
            logger.warning(f"Failed to save balance sheet record: {e}")
            return False

    def _save_ratio_record(self, stock_id: int, record: Dict[str, Any]) -> bool:
        """Save a ratio record using upsert."""
        if not record.get('period_end'):
            return False

        try:
            # Map scraper fields to database fields
            # Scraper uses: debtor_days, inventory_days, days_payable, cash_conversion_cycle, working_capital_days, roce_percent
            stmt = insert(StockRatio).values(
                stock_id=stock_id,
                period_end=record['period_end'],
                roe=self._safe_decimal(record.get('roe')),
                roce=self._safe_decimal(record.get('roce') or record.get('roce_percent')),
                pe_ratio=self._safe_decimal(record.get('pe_ratio')),
                pb_ratio=self._safe_decimal(record.get('pb_ratio')),
                debt_to_equity=self._safe_decimal(record.get('debt_to_equity')),
                current_ratio=self._safe_decimal(record.get('current_ratio')),
                dividend_yield=self._safe_decimal(record.get('dividend_yield')),
                debtor_days=self._safe_int(record.get('debtor_days')),
                inventory_days=self._safe_int(record.get('inventory_days')),
                payable_days=self._safe_int(record.get('days_payable')),
                cash_conversion_cycle=self._safe_int(record.get('cash_conversion_cycle')),
                working_capital_days=self._safe_int(record.get('working_capital_days')),
            ).on_conflict_do_update(
                constraint='uq_ratios_period',
                set_={
                    'roe': self._safe_decimal(record.get('roe')),
                    'roce': self._safe_decimal(record.get('roce') or record.get('roce_percent')),
                    'debtor_days': self._safe_int(record.get('debtor_days')),
                    'inventory_days': self._safe_int(record.get('inventory_days')),
                    'payable_days': self._safe_int(record.get('days_payable')),
                    'cash_conversion_cycle': self._safe_int(record.get('cash_conversion_cycle')),
                    'working_capital_days': self._safe_int(record.get('working_capital_days')),
                }
            )
            self.session.execute(stmt)
            return True
        except Exception as e:
            logger.warning(f"Failed to save ratio record: {e}")
            return False

    def _save_shareholding_record(self, stock_id: int, record: Dict[str, Any]) -> bool:
        """Save a shareholding record using upsert."""
        if not record.get('period_end'):
            return False

        try:
            # Map scraper fields to database fields
            # Database has: promoter_holding, promoter_pledge, fii_holding, dii_holding,
            #              public_holding, government_holding, num_shareholders
            # Note: no other_holding column in database
            stmt = insert(StockShareholding).values(
                stock_id=stock_id,
                period_end=record['period_end'],
                promoter_holding=self._safe_decimal(record.get('promoters')),
                fii_holding=self._safe_decimal(record.get('fiis')),
                dii_holding=self._safe_decimal(record.get('diis')),
                government_holding=self._safe_decimal(record.get('government')),
                public_holding=self._safe_decimal(record.get('public')),
                num_shareholders=self._safe_int(record.get('num_shareholders')),
            ).on_conflict_do_update(
                constraint='uq_shareholding_period',
                set_={
                    'promoter_holding': self._safe_decimal(record.get('promoters')),
                    'fii_holding': self._safe_decimal(record.get('fiis')),
                    'dii_holding': self._safe_decimal(record.get('diis')),
                    'government_holding': self._safe_decimal(record.get('government')),
                    'public_holding': self._safe_decimal(record.get('public')),
                    'num_shareholders': self._safe_int(record.get('num_shareholders')),
                }
            )
            self.session.execute(stmt)
            return True
        except Exception as e:
            logger.warning(f"Failed to save shareholding record: {e}")
            return False

    def get_sync_summary(self, stock_id: int) -> Dict[str, Any]:
        """Get a summary of sync status for a stock."""
        sync_status = self.session.query(StockSyncStatus).filter_by(stock_id=stock_id).first()

        if not sync_status:
            return {'status': 'NEVER_SYNCED', 'needs_sync': True}

        now = datetime.utcnow()
        needs_price_update = False
        needs_full_sync = False

        if sync_status.last_price_sync:
            price_age_hours = (now - sync_status.last_price_sync).total_seconds() / 3600
            needs_price_update = price_age_hours > REFRESH_THRESHOLDS['price']

        if sync_status.last_full_sync:
            full_age_hours = (now - sync_status.last_full_sync).total_seconds() / 3600
            needs_full_sync = full_age_hours > REFRESH_THRESHOLDS['full']

        return {
            'status': sync_status.sync_status,
            'last_full_sync': sync_status.last_full_sync,
            'last_price_sync': sync_status.last_price_sync,
            'primary_source': sync_status.primary_source,
            'quarters_available': sync_status.quarters_available,
            'years_available': sync_status.years_available,
            'needs_price_update': needs_price_update,
            'needs_full_sync': needs_full_sync,
        }

    def sync_stock(self, ticker: str, sync_type: SyncType = None) -> Dict[str, Any]:
        """
        Unified entry point for syncing stock data.

        This method routes to the appropriate sync method based on sync_type.
        Used by Celery tasks for scheduled data updates.

        Args:
            ticker: Full ticker symbol (e.g., "TCS.NS", "INFY.NS")
            sync_type: Type of sync to perform (auto-determined if None)

        Returns:
            Dict with sync results and status
        """
        # Parse ticker to get symbol and market
        if '.' in ticker:
            parts = ticker.split('.')
            symbol = parts[0]
            market = 'NSE' if parts[1] in ('NS', 'NSE') else 'BSE'
        else:
            symbol = ticker
            market = 'NSE'

        # Get stock from database
        stock = self.session.query(Stock).filter_by(ticker=ticker).first()

        if not stock:
            # Stock doesn't exist, create via full sync
            logger.info(f"Stock {ticker} not found, performing full sync")
            return self.full_sync(symbol, market)

        # Auto-determine sync type if not specified
        if sync_type is None:
            sync_type = self.determine_sync_type(stock.id)

        # Route to appropriate sync method
        try:
            if sync_type == SyncType.FULL:
                result = self.full_sync(symbol, market)
                result['status'] = 'success'
                return result

            elif sync_type == SyncType.PRICE_ONLY:
                result = self.price_sync(stock.id, ticker)
                result['status'] = 'success'
                return result

            elif sync_type == SyncType.QUARTERLY:
                result = self.quarterly_sync(stock.id, symbol, market)
                result['status'] = 'success'
                return result

            elif sync_type == SyncType.NONE:
                return {
                    'status': 'success',
                    'sync_type': 'none',
                    'message': 'Data is fresh, no sync needed'
                }

            else:
                return {
                    'status': 'error',
                    'message': f'Unknown sync type: {sync_type}'
                }

        except Exception as e:
            logger.error(f"Sync failed for {ticker}: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def quarterly_sync(self, stock_id: int, symbol: str, market: str = "NSE") -> Dict[str, Any]:
        """
        Incremental quarterly data sync.

        Only fetches new quarterly results that don't already exist in the database.
        Used by weekly_quarterly_sync_task.

        Args:
            stock_id: Database stock ID
            symbol: Stock symbol (e.g., "INFY")
            market: Exchange (NSE or BSE)

        Returns:
            Dict with sync results including new_quarters count
        """
        logger.info(f"Starting QUARTERLY sync for {symbol}.{market}")

        ticker = f"{symbol.upper()}.{'NS' if market == 'NSE' else 'BO'}"

        # Get current sync status
        sync_status = self.get_or_create_sync_status(stock_id)
        existing_quarters = sync_status.quarters_available or 0
        latest_quarter = sync_status.latest_quarter_end

        # Fetch fresh data from Screener.in
        data = self.scraper.fetch_company_data(symbol, consolidated=True)

        if not data:
            return {
                'sync_type': 'quarterly',
                'error': f'Could not fetch data for {symbol}',
                'new_quarters': 0
            }

        new_quarters = 0
        new_quarter_dates = []

        # Process quarterly results
        for record in data.get('quarterly_results', []):
            period_end = record.get('period_end')
            if not period_end:
                continue

            # Check if this quarter is new
            if latest_quarter and period_end <= latest_quarter:
                continue  # Already have this quarter

            if self._save_financial_record(stock_id, record, 'quarterly'):
                new_quarters += 1
                new_quarter_dates.append(period_end)

        # Update shareholding (often changes quarterly)
        shareholding_updated = 0
        for record in data.get('shareholding', []):
            if self._save_shareholding_record(stock_id, record):
                shareholding_updated += 1

        # Update sync status
        if new_quarters > 0:
            sync_status.last_quarterly_sync = datetime.utcnow()
            sync_status.quarters_available = existing_quarters + new_quarters
            if new_quarter_dates:
                sync_status.latest_quarter_end = max(new_quarter_dates)
            self.session.commit()

        logger.info(
            f"QUARTERLY sync complete for {ticker}: "
            f"{new_quarters} new quarters, {shareholding_updated} shareholding records"
        )

        return {
            'sync_type': 'quarterly',
            'new_quarters': new_quarters,
            'new_quarter_dates': [str(d) for d in new_quarter_dates],
            'shareholding_updated': shareholding_updated,
            'quarterly_results': {
                'new_quarters': new_quarters,
                'total_quarters': existing_quarters + new_quarters
            }
        }

    def annual_sync(self, stock_id: int, symbol: str, market: str = "NSE") -> Dict[str, Any]:
        """
        Incremental annual data sync.

        Only fetches new annual results (P&L, cash flow, balance sheet) that
        don't already exist in the database. Used by monthly_annual_sync_task.

        Args:
            stock_id: Database stock ID
            symbol: Stock symbol (e.g., "INFY")
            market: Exchange (NSE or BSE)

        Returns:
            Dict with sync results including new_years count
        """
        logger.info(f"Starting ANNUAL sync for {symbol}.{market}")

        ticker = f"{symbol.upper()}.{'NS' if market == 'NSE' else 'BO'}"

        # Get current sync status
        sync_status = self.get_or_create_sync_status(stock_id)
        existing_years = sync_status.years_available or 0
        latest_annual = sync_status.latest_annual_end

        # Fetch fresh data from Screener.in
        data = self.scraper.fetch_company_data(symbol, consolidated=True)

        if not data:
            return {
                'sync_type': 'annual',
                'error': f'Could not fetch data for {symbol}',
                'new_years': 0
            }

        new_years = 0
        new_annual_dates = []
        new_cashflows = 0
        new_balance_sheets = 0
        new_ratios = 0

        # Process annual P&L results
        for record in data.get('annual_results', []):
            period_end = record.get('period_end')
            if not period_end:
                continue

            # Check if this year is new
            if latest_annual and period_end <= latest_annual:
                continue

            if self._save_financial_record(stock_id, record, 'annual'):
                new_years += 1
                new_annual_dates.append(period_end)

        # Process cash flow (aligned with annual data)
        for record in data.get('cashflow', []):
            period_end = record.get('period_end')
            if latest_annual and period_end and period_end <= latest_annual:
                continue
            if self._save_cashflow_record(stock_id, record):
                new_cashflows += 1

        # Process balance sheet (aligned with annual data)
        for record in data.get('balance_sheet', []):
            period_end = record.get('period_end')
            if latest_annual and period_end and period_end <= latest_annual:
                continue
            if self._save_balance_sheet_record(stock_id, record):
                new_balance_sheets += 1

        # Process ratios (aligned with annual data)
        for record in data.get('ratios', []):
            period_end = record.get('period_end')
            if latest_annual and period_end and period_end <= latest_annual:
                continue
            if self._save_ratio_record(stock_id, record):
                new_ratios += 1

        # Update sync status
        if new_years > 0:
            sync_status.last_annual_sync = datetime.utcnow()
            sync_status.years_available = existing_years + new_years
            if new_annual_dates:
                sync_status.latest_annual_end = max(new_annual_dates)
            self.session.commit()

        logger.info(
            f"ANNUAL sync complete for {ticker}: "
            f"{new_years} years, {new_cashflows} cashflows, "
            f"{new_balance_sheets} balance sheets, {new_ratios} ratios"
        )

        return {
            'sync_type': 'annual',
            'new_years': new_years,
            'new_annual_dates': [str(d) for d in new_annual_dates],
            'new_cashflows': new_cashflows,
            'new_balance_sheets': new_balance_sheets,
            'new_ratios': new_ratios,
            'annual_results': {
                'new_years': new_years,
                'total_years': existing_years + new_years
            }
        }

    def info_sync(self, stock_id: int, ticker: str) -> Dict[str, Any]:
        """
        Lightweight info-only sync.

        Updates company metrics (P/E, ROE, ROCE, market cap) without
        fetching historical data. Used by refresh_company_info_task.

        Args:
            stock_id: Database stock ID
            ticker: Full ticker symbol (e.g., "INFY.NS")

        Returns:
            Dict with updated info
        """
        logger.info(f"Starting INFO sync for {ticker}")

        # Parse ticker
        if '.' in ticker:
            symbol = ticker.split('.')[0]
        else:
            symbol = ticker

        try:
            # Try Yahoo Finance first (faster, no rate limiting concerns)
            import yfinance as yf
            yf_stock = yf.Ticker(ticker)
            info = yf_stock.info

            # Update stock_info table
            stock_info = self.session.query(StockInfo).filter_by(stock_id=stock_id).first()
            if not stock_info:
                stock_info = StockInfo(stock_id=stock_id)
                self.session.add(stock_info)

            # Update metrics from Yahoo Finance
            stock_info.current_price = self._safe_decimal(
                info.get('regularMarketPrice') or info.get('currentPrice')
            )
            stock_info.market_cap = self._safe_decimal(info.get('marketCap'))
            stock_info.pe_ratio = self._safe_decimal(info.get('trailingPE'))
            stock_info.pb_ratio = self._safe_decimal(info.get('priceToBook'))
            stock_info.dividend_yield = self._safe_decimal(info.get('dividendYield'))
            stock_info.fifty_two_week_high = self._safe_decimal(info.get('fiftyTwoWeekHigh'))
            stock_info.fifty_two_week_low = self._safe_decimal(info.get('fiftyTwoWeekLow'))
            stock_info.previous_close = self._safe_decimal(info.get('previousClose'))
            stock_info.day_high = self._safe_decimal(info.get('dayHigh'))
            stock_info.day_low = self._safe_decimal(info.get('dayLow'))
            stock_info.volume = info.get('volume')
            stock_info.data_source = 'yahoo'
            stock_info.last_updated = datetime.utcnow()

            # Update sync status
            sync_status = self.get_or_create_sync_status(stock_id)
            sync_status.last_price_sync = datetime.utcnow()
            sync_status.price_source = 'yahoo'

            self.session.commit()

            logger.info(f"INFO sync complete for {ticker}: price={stock_info.current_price}")
            return {
                'sync_type': 'info',
                'status': 'success',
                'current_price': float(stock_info.current_price) if stock_info.current_price else None,
                'market_cap': float(stock_info.market_cap) if stock_info.market_cap else None,
                'source': 'yahoo'
            }

        except Exception as e:
            logger.warning(f"Yahoo Finance failed for {ticker}, trying Screener.in: {e}")

            # Fallback to Screener.in (slower, but has Indian stock specific data)
            try:
                data = self.scraper.fetch_company_data(symbol, consolidated=True)
                if data:
                    self._save_stock_info(stock_id, data)
                    self.session.commit()

                    return {
                        'sync_type': 'info',
                        'status': 'success',
                        'current_price': data.get('current_price'),
                        'source': 'screener'
                    }
            except Exception as e2:
                logger.error(f"Info sync completely failed for {ticker}: {e2}")

        return {
            'sync_type': 'info',
            'status': 'failed',
            'error': 'Could not fetch info from any source'
        }
