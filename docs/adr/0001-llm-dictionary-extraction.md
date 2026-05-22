# ADR-0001: Dictionary extraction — HTML parser with LLM fallback

Dictionary entries are obtained by scraping from zdic.net. The primary extraction path is direct HTML parsing of the new semantic UI; LLM-mediated extraction is retained only as a fallback for structural changes.

## Context

The original implementation parsed zdic.net's HTML structure directly. When zdic.net changed its frontend, the parser broke. We switched to LLM-mediated extraction for robustness, but this introduced a significant cost: ~$0.01/word for the preprocessing LLM call.

Users reported quota exhaustion during heavy reading sessions. The LLM preprocessing accounted for >95% of per-word cost (Quick $0.0001 + Deep $0.0004 + Dict $0.01).

In May 2026 zdic.net released a new UI with BEM-named semantic CSS classes, Schema.org markup, and clean separation of definitions, citations, examples, and part-of-speech tags. This made reliable direct parsing feasible again.

## Decision

**Primary path**: Parse the HTML directly using BeautifulSoup selectors targeting the new UI's semantic classes (`.jbjs-item`, `.xxjs-pos-section`, `.xxjs-item`, `.xxjs-citation`, `.xxjs-english`, etc.). The extracted data is structured into JSON with `pos` (词性), `citations`, and `examples` as separate fields.

**Fallback path**: If the HTML structure is unrecognizable (e.g., zdic changes UI again), fall back to the LLM preprocessing pipeline (`structure_dict_data`) using the same prompt as before.

**Quota**: Since the dictionary extraction no longer incurs LLM cost, dictionary queries are free (no quota consumption). The daily quota for LLM-based query modes (quick/deep) has been increased accordingly.

## Consequences

- **Cost reduction**: Dictionary lookups cost effectively $0 (only an HTTP request + cache write). The $0.01/word LLM cost is eliminated for >99% of lookups.
- **Better data**: The parser extracts `pos` (词性) which the LLM pipeline lost, and separates `citations` from `examples`.
- **Faster lookups**: Direct parsing completes in <100ms vs 1-3s for LLM preprocessing.
- **Cache schema upgrade**: New cache entries include `pinyin`, `zhuyin`, `radical`, `strokes`, and per-item `pos` + `citations`. Old cache entries remain compatible — `format_dict_for_prompt` handles missing fields gracefully.
- **Robustness**: If zdic.net changes UI again, the LLM fallback is still available. The fallback prompt and flow require no code changes.
