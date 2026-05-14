# ADR-0002: External export service for Word and Anki

Export to Word (.docx) and Anki (.apkg) is delegated to an external service at `anki.cup11.top`, rather than implemented in-process. The server constructs a JSON document with a standard schema and sends it to the external service, which returns a downloadable file.

The alternative was to generate these formats locally using libraries like `python-docx`. Offloading keeps the server lightweight: the export service handles format-specific complexity (templates, pagination, media embedding) independently. Since the external service is also owned by the project author, this is not a third-party dependency risk.

The JSON format is the canonical export and is assembled locally; Word and Anki are downstream transformations.
