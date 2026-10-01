# Changelog

## 0.1.3 — 2026-10-01

- ENG-019: model `grok-4.7-build-fast` + `--effort xhigh` (timeout remains 600s).

## 0.1.2 — 2026-10-01

- ENG-018: Option B grok CLI uses `--effort xhigh` (subprocess timeout remains 600s). Model remains `grok-4.7`.

## 0.1.1 — 2026-10-01

- ENG-016: Option B grok CLI timeout raised to 600s (effort later aligned to xhigh in 0.1.2). Model `grok-4.7`.

## 0.1.0 — 2026-10-01

- Initial CLI: turns a scope or PRD (plus optional constraints) into a six-heading Chinese acceptance slice for Eng dispatch, via xAI (`XAI_API_KEY`, model `grok-4.7`) or the grok CLI (`grok-4.7`, `--effort xhigh`, subprocess timeout 600s).
- Heading check requires all six H2 strings and strictly ascending order. A failed check deletes the output file.
- Third-party `## …` headings in source material stay verbatim; this engine’s six headings are not projected onto those descriptions.
