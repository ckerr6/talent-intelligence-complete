# SQL Directory

SQL scripts and queries for database operations.

## Structure

- `schema/` - Schema definitions and migrations
- `maintenance/` - Database maintenance scripts (VACUUM, indexing)
- `queries/` - Common queries and examples
- `analysis/` - Complex analysis queries

## Usage

Run SQL scripts with:

```bash
psql -d talent -f sql/maintenance/emergency_performance_fix.sql
psql -d talent -f sql/queries/sample_queries.sql
```
