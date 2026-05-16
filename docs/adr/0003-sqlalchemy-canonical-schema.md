# ADR-0003: SQLAlchemy as canonical schema source

The database schema was maintained in two places: raw CREATE TABLE statements in db_helper.py and SQLAlchemy ORM models in admin.py. Adding a column or table required touching both files in lockstep.

We moved the ORM models into a shared schema.py module that both db_helper.py (for DDL generation) and admin.py (for admin panel models) import from. db_helper.py keeps raw sqlite3 for all CRUD operations — rewriting 14 query methods to use SQLAlchemy is not worth the leverage at this codebase's scale.

**Considered Options:**

1. **Dict/JSON schema as source of truth** — a Python dict mapping table names to column lists, compiled to both raw SQL and SQLAlchemy models. Rejected because it adds an abstraction layer without either output format's full expressiveness.

2. **Raw SQL as source of truth** — schema.py exports SQL strings that db_helper.py uses directly and admin.py parses into ORM models. Rejected because SQLAlchemy cannot be reliably reverse-engineered from arbitrary DDL strings.

3. **SQLAlchemy only** — rewrite all db_helper.py CRUD methods to use SQLAlchemy. Rejected because the 14 methods are stable, well-tested, and the rewrite carries risk without proportional benefit at this codebase's scale.
