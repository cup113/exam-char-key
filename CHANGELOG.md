# Changelog

## 0.4.3 (2026-05-31)

### Features
- Document content update: `PATCH /api/documents/{id}` now accepts `source_text` and `tracked_words`; frontend tracks `currentDocId` and shows update-or-save-as-new dialog
- UI: search bar reordered (识典古籍 first); help guide renumbered ①→7; credits now show real logos (汉典, 识典古籍 long logos; ctext, 古文岛 icons)

### Fixes
- Public shared doc "Continue querying" no longer binds another user's doc ID, preventing confusing 404 on save

### Tests
- Added 7 backend tests for document content update, JSON roundtrip, and cross-user isolation
- Fixed frontend test mocks for new `closeDocument` and `createDoc` response shape

## 0.4.2 (2026-05-31)

### Refactors
- Extracted shared `typeLabel`/`deepMeaning`/`aiAnswerForDict` into `utils/wordAnalysis.ts`

### Tests
- Added frontend tests: auth/theme stores, router, 3 dialog components, 5 more components
- Raised client coverage from 57% to 79%
- Added type annotations and non-null assertions for vue-tsc compliance

### Chores
- Updated zdic.net User-Agent header; removed unused pytest import

## 0.4.1 (2026-05-23)

### Features
- Tabbed usage guide with collapsible sections and new About & Credits tab
- Document update endpoint now returns 404 when document not found

### Fixes
- `update_document` returns success status; route respects it with proper HTTP error

### Tests
- Added frontend tests: TextContent, useDocumentLoader, words store
- Added backend tests: document API routes and spider module
- Added `user_token_b` fixture for user isolation testing

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
