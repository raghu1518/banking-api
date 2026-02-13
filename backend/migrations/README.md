# SQL Migration Scripts

This project auto-manages additive schema updates at runtime (create missing tables, add missing columns) through `app/core/schema.py`.

For production databases, apply explicit SQL migrations for stronger control and auditing.

## PostgreSQL
- Initial schema: `migrations/postgresql/001_initial.sql`
- Additive update template: `migrations/postgresql/002_additive_sample.sql`

Run:
```bash
psql "$DATABASE_URL" -f migrations/postgresql/001_initial.sql
```

## MySQL
- Initial schema: `migrations/mysql/001_initial.sql`
- Additive update template: `migrations/mysql/002_additive_sample.sql`

Run:
```bash
mysql --host=<host> --user=<user> --password <db_name> < migrations/mysql/001_initial.sql
```

## Notes
- Migrations are additive/non-destructive by default.
- Do not drop columns/tables in production without backup and rollback plan.
- Keep runtime compatibility updater enabled as a safeguard for newly added nullable/defaulted columns.
