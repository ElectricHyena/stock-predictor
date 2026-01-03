# STORY 5.3: Backtest Results Display

**Epic:** EPIC-05 (Advanced Features)
**Phase:** 5 (Advanced Features)
**Points:** 5
**Priority:** Must Have
**Status:** PENDING

---

## User Story

As a trader, I want to see detailed results and performance metrics from my backtested strategies so that I can evaluate their effectiveness and compare them with other strategies.

---

## Description

Build a comprehensive Backtest Results display page that shows:
- Overall performance metrics (return %, Sharpe ratio, max drawdown, etc.)
- Equity curve visualization showing account growth over time
- Trade-by-trade analysis with entry/exit details
- Win/loss statistics and probability
- Monthly and yearly performance breakdowns
- Comparison with benchmark performance
- Risk metrics and exposure analysis
- Strategy performance rankings
- Downloadable backtest reports

---

## Acceptance Criteria

- [ ] Backtest Results page created and routed
- [ ] Overall performance metrics displayed (total return, annualized return, Sharpe ratio)
- [ ] Equity curve chart showing account growth over backtest period
- [ ] Win rate, profit factor, and drawdown statistics visible
- [ ] Trade list with individual trade details (entry, exit, P&L, duration)
- [ ] Monthly and yearly performance breakdown tables/charts
- [ ] Benchmark comparison showing strategy vs market performance
- [ ] Risk metrics clearly displayed (max drawdown, Sortino ratio, Calmar ratio)
- [ ] Exposure analysis showing position sizing and leverage
- [ ] Filters/sort options for trade list
- [ ] Strategy comparison view (side-by-side metrics)
- [ ] Export functionality for report (PDF/CSV)
- [ ] Mobile responsive design verified
- [ ] Page loads within 3 seconds (performance target)

---

## Technical Notes

### Implementation Steps

1. **Create Results Page Component**
   ```
   /src/components/pages/BacktestResults.tsx
   - Main results display page
   - Tabs for different views (Summary, Trades, Performance)
   - Navigation between strategies
   ```

2. **Build Metrics Dashboard**
   - Key performance metrics cards
   - Display calculations for Sharpe ratio, max drawdown
   - Format percentages and currency values
   - Color coding for positive/negative returns

3. **Implement Equity Curve Chart**
   - Line chart showing account value over time
   - Interactive hover tooltips
   - Highlight trade entry/exit points
   - Mark drawdown periods
   - Comparison overlay with benchmark

4. **Create Trade List Component**
   - Table with trade details (entry date, exit date, entry price, exit price, P&L, %)
   - Sort by date, P&L, duration, etc.
   - Filter by trade type (winners, losers, all)
   - Pagination for large trade lists

5. **Build Performance Breakdown**
   - Monthly return heatmap
   - Yearly performance comparison
   - Calendar view of daily returns
   - Drawdown analysis chart

6. **Add Comparison Features**
   - Benchmark performance overlay
   - Multi-strategy comparison view
   - Metric comparison table
   - Performance vs market correlation

7. **Implement Export Functionality**
   - PDF report generation with charts and metrics
   - CSV export of trade list and metrics
   - Summary statistics export

### Files to Create/Modify

- `src/components/pages/BacktestResults.tsx` - Main results page
- `src/components/results/MetricsCard.tsx` - Individual metric display
- `src/components/results/EquityCurve.tsx` - Equity curve chart
- `src/components/results/TradeList.tsx` - Trade list table
- `src/components/results/PerformanceBreakdown.tsx` - Monthly/yearly performance
- `src/components/results/RiskAnalysis.tsx` - Risk metrics display
- `src/components/results/ComparisonView.tsx` - Strategy comparison
- `src/components/results/ResultsExport.tsx` - Export functionality
- `src/services/backtestResultsService.ts` - Results data service
- `src/types/backtest.ts` - Backtest TypeScript types
- `src/utils/backtestCalculations.ts` - Calculation utilities (Sharpe, drawdown, etc.)

### Dependencies

- Chart library (Chart.js, Recharts, or Plotly)
- Table library (TanStack Table, ag-Grid)
- PDF export library (jsPDF, html2pdf)
- Financial calculation library (for Sharpe ratio, etc.)
- Date handling (date-fns or dayjs)

### Performance Considerations

- Lazy load trade list if > 1000 trades
- Cache calculated metrics
- Virtual scrolling for large tables
- Debounce chart updates on resize

---

## Dependencies

- **Upstream:** STORY-5.2 (Backtest Strategy Builder), EPIC-05 Backtest Engine implementation
- **Downstream:** STORY-5.4 (Strategy Analysis), Optimization features

---

## Testing Checklist

- [ ] Metrics calculate correctly from backtest data
- [ ] Equity curve displays accurate account values
- [ ] Trade list shows all trades with correct details
- [ ] Filters work for trade list sorting
- [ ] Monthly/yearly breakdowns calculate accurately
- [ ] Benchmark comparison shows correct performance difference
- [ ] Export to PDF/CSV works without errors
- [ ] Charts render without errors and are interactive
- [ ] Page is responsive on mobile devices
- [ ] Performance metrics are formatted correctly
- [ ] No console errors or warnings
- [ ] Comparison view handles multiple strategies

---

## Definition of Done

- [ ] Component created and integrated into routing
- [ ] All acceptance criteria met
- [ ] All calculations verified for accuracy
- [ ] Unit tests written (80%+ coverage)
- [ ] Integration tests passing
- [ ] Export functionality verified
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Performance meets 3-second load target
- [ ] Accessibility standards met (WCAG 2.1 AA)

---

## Notes

- Ensure all financial calculations are accurate and verified
- Consider using industry-standard backtest metrics
- Performance optimization critical for large trade lists
- Provide tooltips explaining complex metrics (Sharpe, Sortino, Calmar)
- Consider heat-map for better visual performance breakdown
- Add ability to hide/show specific metrics based on user preference
- Provide downloadable sample backtest results for testing

