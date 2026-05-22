# Changelog

## 0.4.0 (2026-05-22)

### Features
- Improved UI/UX with better loading states, error handling, and POS display in query results
- Migrated dictionary parsing to HTML parser with LLM fallback for more robust ZDIC scraping

### Refactors
- Extracted API layer — centralized `apiClient` + 7 service modules for cleaner separation of concerns

### Tests
- Added frontend test infra (vitest + @vue/test-utils + happy-dom) and first 25 tests
- Added 49 tests for services layer + utils (20.72% coverage)

### Chores
- Fixed ruff lints — E402, F401, F841

## 0.3.0 (2026-05-17)

### Features
- Document save/share: save reading sessions as documents with public sharing links
- Guest-friendly quota: inline quota display in TextContent, removed intrusive quota prompt banner
- External text search: search ctext, 识典古籍, 古文岛 for classical Chinese passages
- Configurable ZDIC timeout via `ZDIC_TIMEOUT` env var
- Full test suite for admin panel and database layer

### Refactors
- Extract composable/schema/export services from HomeView
- Remove unused `showQuotaPrompt` / `dismissQuotaPrompt` from auth store

### Docs
- Add CONTEXT.md with domain model
- Add ADRs under docs/adr/
- Add Admin Panel section in README

### Fixes
- Admin panel HTTPS mixed content via `trust_forwarded_proxy` middleware
- Missing `ADMIN_USERS` in docker-compose.yml
- Production defaults for LLM_BASE_URL and models
- Retry button and `retryDictionary()` for ZDIC fetch failures
- Auto-refresh quota display after query completes
