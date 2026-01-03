---
# Database Schema & Migrations

**Story ID:** STORY_1_2
**Phase:** 1 (Foundation)
**Story Points:** 8
**Status:** Not Started

## User Story
**As a** Backend Developer
**I want** to define the database schema with proper migrations and relationships
**So that** we have a solid, scalable data model for storing stock data and predictions

## Acceptance Criteria
- [ ] Database schema is designed with proper normalization and relationships
- [ ] Migration files are created and can be applied to clean database
- [ ] All tables have appropriate indexes for query optimization
- [ ] Foreign key constraints are properly configured
- [ ] Data types are appropriate for each field
- [ ] Timestamps (created_at, updated_at) are included in all tables
- [ ] Migration rollback functionality is tested and working
- [ ] Database schema documentation is complete

## Implementation Tasks
- [ ] Design and create users table (id, email, password_hash, created_at, updated_at)
- [ ] Design and create stocks table (id, symbol, name, sector, created_at, updated_at)
- [ ] Design and create stock_prices table (id, stock_id, date, open, high, low, close, volume, created_at)
- [ ] Design and create news table (id, stock_id, title, description, source, published_at, url, created_at)
- [ ] Design and create predictions table (id, stock_id, predicted_price, confidence, prediction_date, created_at)
- [ ] Design and create watchlist table (id, user_id, stock_id, created_at)
- [ ] Create initial migration file with all tables
- [ ] Add appropriate indexes on frequently queried columns (symbol, stock_id, date)
- [ ] Set up foreign key relationships
- [ ] Configure cascading delete rules
- [ ] Create seed data migration for initial stocks
- [ ] Set up database initialization script

## Test Cases
- [ ] Verify migration creates all tables correctly
- [ ] Test that migration can be rolled back successfully
- [ ] Verify foreign key constraints prevent orphaned records
- [ ] Test that indexes improve query performance
- [ ] Confirm all data types accept appropriate values
- [ ] Verify timestamps are automatically set on creation
- [ ] Test cascading deletes work as expected
- [ ] Confirm database schema matches design documentation
- [ ] Test migration idempotency (running twice has no effect)
- [ ] Verify seed data loads correctly

## Dependencies
Depends on: STORY_1_1 (Infrastructure Setup)

## Notes
- Use SQLAlchemy ORM for database interactions
- Implement proper connection pooling
- Consider partitioning for large historical price tables
- Plan for future scalability with read replicas
- Document all migration steps clearly

---
