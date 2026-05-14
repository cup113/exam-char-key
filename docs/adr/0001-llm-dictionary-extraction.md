# ADR-0001: LLM-mediated dictionary extraction

Dictionary entries are obtained by scraping raw text from zdic.net, then passing it to an LLM (configured as `MODEL_DICT_PREPROCESS`) for restructuring into JSON, rather than parsing the HTML directly.

The original implementation parsed zdic.net's HTML structure directly. When zdic.net changed its frontend, the parser broke — the HTML structure shifted and Google Ads polluted the content. Repairing the parser would have been fragile against future changes. Switching to LLM-mediated extraction trades token cost and latency for robustness: the LLM handles variable formatting, missing sections, and ad injection without code changes. The resulting JSON is cached in SQLite so subsequent lookups for the same word skip both scraping and LLM calls.

The caching invariant means the LLM cost is paid at most once per distinct word, making the trade-off acceptable even under light usage (<3 DAU).
