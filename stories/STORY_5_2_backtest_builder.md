# STORY 5.2: Backtest Strategy Builder

**Epic:** EPIC-05 (Advanced Features)
**Phase:** 5 (Advanced Features)
**Points:** 5
**Priority:** Must Have
**Status:** PENDING

---

## User Story

As a trader, I want to build and customize trading strategies with various parameters so that I can test their effectiveness before applying them to real trading.

---

## Description

Build an interactive Backtest Strategy Builder interface that allows users to:
- Create custom trading strategies with visual rule builder
- Define entry and exit conditions
- Set position sizing and risk management parameters
- Select stocks/watchlist to test against
- Configure technical indicators and thresholds
- Save strategy templates for reuse
- Preview strategy logic before backtesting

---

## Acceptance Criteria

- [ ] Backtest Strategy Builder page created and routed
- [ ] Visual rule builder for entry/exit conditions implemented
- [ ] Support for multiple condition types (price, indicator, volume, etc.)
- [ ] AND/OR logic operators for combining conditions
- [ ] Position sizing options (fixed, percentage, dynamic) available
- [ ] Risk management parameters (stop loss, take profit, max risk)
- [ ] Stock/watchlist selector for backtest universe
- [ ] Technical indicator selector with customizable thresholds
- [ ] Strategy name and description input
- [ ] Save/Load strategy templates functionality
- [ ] Strategy preview showing logic in human-readable format
- [ ] Validation of strategy logic before submission
- [ ] Mobile responsive design verified

---

## Technical Notes

### Implementation Steps

1. **Create Strategy Builder Component**
   ```
   /src/components/pages/BacktestBuilder.tsx
   - Main page with form layout
   - Strategy configuration panels
   - Preview section
   ```

2. **Build Rule Builder UI**
   - Rule component for single condition
   - Add/remove rule buttons
   - Logic operator selectors (AND/OR)
   - Support for rule groups

3. **Implement Condition Types**
   - Price-based conditions (>, <, =, range)
   - Indicator-based conditions (SMA crossover, RSI threshold)
   - Volume conditions (volume spike, increase %)
   - Time-based conditions (specific hours/days)

4. **Create Parameter Forms**
   - Entry condition builder
   - Exit condition builder
   - Position sizing form
   - Risk management form

5. **Add Stock Universe Selector**
   - Watchlist picker
   - Individual stock selector
   - Market cap/sector filters
   - Quantity selector

6. **Implement Strategy Management**
   - Save strategy to database
   - Load saved strategies
   - Template library
   - Duplicate strategy functionality

7. **Build Strategy Preview**
   - Display strategy logic in text format
   - Show all parameters summary
   - Validation messages
   - Warnings for complex strategies

### Files to Create/Modify

- `src/components/pages/BacktestBuilder.tsx` - Main builder page
- `src/components/strategy/RuleBuilder.tsx` - Rule builder component
- `src/components/strategy/RuleGroup.tsx` - Rule group component
- `src/components/strategy/EntryConditions.tsx` - Entry rules section
- `src/components/strategy/ExitConditions.tsx` - Exit rules section
- `src/components/strategy/PositionSizing.tsx` - Position sizing form
- `src/components/strategy/RiskManagement.tsx` - Risk parameters form
- `src/components/strategy/StockUniverse.tsx` - Stock selection
- `src/components/strategy/StrategyPreview.tsx` - Preview display
- `src/services/strategyService.ts` - Strategy API calls
- `src/types/strategy.ts` - Strategy TypeScript types

### Dependencies

- Form library (React Hook Form or Formik)
- Validation library (Zod or Yup)
- Database migrations for strategy storage
- API endpoints for strategy CRUD operations

---

## Dependencies

- **Upstream:** STORY-3.2 (Stock Detail Page), STORY-4.2 (Indicator Calculation)
- **Downstream:** STORY-5.3 (Backtest Results), STORY-5.4 (Strategy Analysis)

---

## Testing Checklist

- [ ] Rule builder adds/removes conditions correctly
- [ ] AND/OR logic operators work as expected
- [ ] All condition types validate properly
- [ ] Position sizing calculations are correct
- [ ] Risk parameters apply correctly
- [ ] Strategy saves to database
- [ ] Saved strategies load correctly
- [ ] Strategy preview displays accurate logic
- [ ] Form validation prevents invalid strategies
- [ ] Page is responsive on mobile devices
- [ ] No console errors or warnings

---

## Definition of Done

- [ ] Component created and integrated into routing
- [ ] All acceptance criteria met
- [ ] Unit tests written (80%+ coverage)
- [ ] Integration tests passing
- [ ] Form validation comprehensive
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Database migrations applied
- [ ] Accessibility standards met (WCAG 2.1 AA)

---

## Notes

- Start with simple rules and expand to complex logic
- Consider query builder libraries for better UX
- Provide example strategies/templates
- Validate rule combinations for feasibility
- Consider maximum rule limits for performance
- Add strategy complexity indicator (simple/moderate/complex)

