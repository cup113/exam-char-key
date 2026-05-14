# Exam Char Key

AI-assisted platform for Classical Chinese (文言文) character and word lookup. Users select a character from a passage and receive AI-generated explanations enriched with dictionary data from zdic.net.

## Language

**Word**:
A Chinese character or multi-character word selected by the user for lookup.
_Avoid_: 字, 字符, 词

**Context**:
A ±30 character window around the selected word, extracted from the source text. No metadata (chapter, source) attached.

**Quick Answer**:
A concise AI-generated explanation of the word's meaning in context, streamed via SSE. Does not use dictionary data.

**Deep Answer**:
An AI analysis that incorporates structured dictionary data. Contains two sections: contextual analysis (labeled `[解释]`) and meaning summary (labeled `[词义]`). Streamed via SSE; requires prior dictionary cache.

**Dictionary**:
zdic.net content processed by an LLM into structured JSON with two tiers: basic_explanation and detailed_explanation. Obtained via LLM restructuring rather than direct HTML parsing. Cached in SQLite.

**Corpus**:
A reference dataset of word usages from three sources: textbook (教材), mock exam (模考), and user queries. Displayed for browsing only; not fed into LLM prompts.

**Quota**:
Daily usage limit. Authenticated users: 50/day per user. Unauthenticated users: 50/day shared pool for all guests.

**Identifier**:
Identity in the quota system. Authenticated: `user:{sub}`. Guest: `ip:guest` (single shared identifier for all unauthenticated users).

**Mode**:
Either "quick" or "deep". Both modes fetch Quick Answer + Dictionary + Corpus in parallel. Deep mode additionally runs Deep Answer after the dictionary is cached.

## Relationships

```
User selects a Word → SelectionTooltip (mode: quick/deep)
  └─ wordsStore.queryWord()
       ├─ GET /api/query/quick     ← SSE stream  → Quick Answer
       ├─ GET /api/query/corpus    ← JSON        → Corpus entries
       ├─ GET /api/query/dictionary← JSON        → Dictionary
       └─ (deep mode) GET /api/query/deep ← SSE  → Deep Answer
              ↑ Deep requires Dictionary already cached (server reads it from cache)
       └─ status: done → QueryPanel displays all results
```

- A query always produces Quick Answer + Dictionary + Corpus; Deep Answer is optional
- Deep Answer depends on Dictionary being cached first
- Each query consumes Quota: quick=1, deep=1+1=2, dictionary=1
- Saving history writes a user_query entry to Corpus
- Context governs relevance of both Quick Answer and Deep Answer

## Example dialogue

> **Dev:** "When a user selects '居', what is the Context?"
> **Domain expert:** "A ±30 character slice. If the full text is '譬如北辰，居其所而众星共之' and the user selects the middle character '居', the context is roughly a 60-character window centered on '居'."

> **Dev:** "Why does Quick mode still call the Dictionary endpoint?"
> **Domain expert:** "Dictionary data has educational value — seeing the full entry is more rewarding than just the AI summary. The cost is acceptable at current usage levels."

## Flagged ambiguities

- **Mode**: Despite selecting "quick" or "deep", both modes always fetch Dictionary. The mode only controls whether the additional Deep Answer step runs.
- **Guest Quota**: A single shared pool for all guests, not per-IP. Intentionally simplified.
