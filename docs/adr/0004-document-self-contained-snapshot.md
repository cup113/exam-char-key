# ADR-0004: Document model with self-contained JSON snapshots

Documents save a reading session (source text + all word queries) so users can review and share their analysis later.

## Decision

A **self-contained JSON blob** stores all query data inside the `documents` row, rather than normalizing into related tables.

## Data model

```
documents
├── id            INTEGER PK
├── user_id       TEXT NOT NULL      -- owner
├── title         TEXT NOT NULL      -- auto-generated from text, user-editable
├── source_text   TEXT NOT NULL      -- editableText snapshot
├── tracked_words TEXT NOT NULL      -- JSON: TrackedWordSnapshot[]
├── is_public     INTEGER DEFAULT 0
├── public_uuid   TEXT UNIQUE        -- UUID v4, only when is_public=1
├── created_at    TEXT
└── updated_at    TEXT
```

`tracked_words` JSON stores one entry per queried word:

```json
{ "word", "context", "offset", "mode",
  "quickAnswer", "dictResult", "deepThink", "corpusEntries" }
```

Runtime-only fields (`id`, `status`, `*Status`, `startTime`) are excluded on save and regenerated on load.

## Considered options

### 1. Normalized references (rejected)

A `document_queries` join table linking documents to `query_history` records.

- **Rejected because**: Sharing requires exporting scattered related rows; deleting a history record silently corrupts documents; read path requires N+1 JOINs.
- **Wins on**: No data duplication.

### 2. Read-on-demand (rejected for now)

Keep only `{word, context, offset, mode, quickAnswer, deepThink}` in the snapshot; re-fetch `dictResult` (from `dict_cache`) and `corpusEntries` (from `corpus`) when opening a document.

- **Rejected because**: Sharing reliability degrades — if `dict_cache` is cleared during deployment, shared documents lose dictionary data permanently. Storage savings (≈80%) are not meaningful at this project's scale (<4 GB for 100 users × 100 documents).
- **Potential future optimization**: When single-user document count exceeds 1000, implement read-on-demand with a warm-up step at save time (pre-fetch all dict entries into cache).

### 3. Self-contained JSON snapshot (chosen)

- Storage: ≈150 KB per document (15-20 words). Negligible against SQLite's capacity.
- Sharing: fully self-describing, survives server resets.
- Complexity: lowest — serialise on save, deserialise on load, no JOINs.

## Implications

- Side effect for the client: when saving a snapshot, current localStorage-only views (`editableText`, `trackedWords`) become capture-on-write, enabling sharing and multi-device review.
