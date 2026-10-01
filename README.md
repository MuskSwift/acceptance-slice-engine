# Acceptance Slice Engine

CLI that turns a **scope or PRD** (plus optional constraints) into an acceptance-slice Markdown an engineer can pick up. Output is Chinese. The six H2 headings are a fixed contract so review and diff can key off structure.

This repository is its own package, system prompt, and heading contract. Decision One-Pager and Release Notes Engine are separate tools; this CLI does not call them.

Python **3.10+**, standard library only — no pip packages required. Licensed under MIT.

## Six H2 contract (exact, in order)

The file starts at the first heading. These strings must appear exactly, in this order:

1. `## 工单目标`
2. `## 验收条目`
3. `## 非本单 / 明确不做`
4. `## 风险与 sev 提示`
5. `## 给实现的边界`
6. `## 待确认的开放问题`

Do not translate, rephrase, or change heading level. Body wording may vary between runs. When there is nothing to confirm, the body under `## 待确认的开放问题` is `无`.

Content rules the model is instructed to follow:

- Write in Chinese. Keep paths, codes, column names, and sev labels as given.
- 「验收条目」: checkboxes that are testable; a failure must be observable. No vague filler.
- 「非本单 / 明确不做」: must be non-empty.
- 「给实现的边界」: repository path and shape only. Where the material names no stack, write `材料未指定`. Do not pick a tech stack for Eng.
- Do not claim login, payment, automatic Issue creation, acquisition, marketing, or “已可售”.
- Third-party `## …` headings in the source stay verbatim. Do not rewrite them into this engine’s six headings. This document’s structure is still only those six H2s.

## Install

From the repo root (no install):

```bash
python3 -m acceptance_slice_engine --help
```

Optional editable install (exposes the `acceptance-slice-engine` console script):

```bash
pip install -e .
```

## Authentication (bring your own)

Generation uses model **grok-4.7-build-fast**. This project does not ship API keys or implement login.

**Option A — xAI HTTP API (used when a key is present).** Set `XAI_API_KEY`. The CLI POSTs to `https://api.x.ai/v1/chat/completions` with stdlib `urllib.request`.

```bash
export XAI_API_KEY="xai-..."
```

**Option B — grok CLI fallback.** If `XAI_API_KEY` is unset, the CLI shells out to an already-authenticated grok CLI (`~/.grok/bin` is prepended to `PATH`). The subprocess uses model `grok-4.7-build-fast`, `--effort xhigh`, and a 600s timeout:

```bash
export PATH="$HOME/.grok/bin:$PATH"
grok -p "<prompt>" -m grok-4.7-build-fast --effort xhigh --always-approve
```

Authenticate the grok CLI yourself before running this tool. If neither a key nor `grok` is available, generation fails.

## End-to-end example

From the repo root, using the bundled fixtures:

```bash
python3 -m acceptance_slice_engine \
  --scope-file examples/sample-scope.md \
  --constraints-file examples/sample-constraints.txt \
  --out out/finance-recon-acceptance-slice.md
```

On success the CLI prints the output path and exits `0`. The file starts at `## 工单目标` and includes all six headings in order.

`--prd` is an alias of `--scope`, and `--prd-file` is an alias of `--scope-file`. Every source you pass is joined, in this order: `--scope`, `--prd`, `--scope-file`, `--prd-file`. At least one of them is required. `--constraints` and `--constraints-file` are optional and are joined the same way; when both are omitted, the prompt records constraints as `（无）`.

```bash
python3 -m acceptance_slice_engine \
  --prd "对账差异导出 v0：已关闭账期可下载差异 CSV。" \
  --constraints "不点名技术栈。"
```

Default output path: `./out/<slug>-acceptance-slice.md`. The slug comes from the first non-empty line of the joined scope (spaces become `-`; other unsafe characters are stripped; CJK is kept).

## Example paths

| Path | What it is |
| --- | --- |
| [`examples/sample-scope.md`](examples/sample-scope.md) | Scope / PRD fixture |
| [`examples/sample-constraints.txt`](examples/sample-constraints.txt) | Optional constraints fixture |
| [`examples/sample-output.md`](examples/sample-output.md) | Hand-written slice in the six-heading shape |

## Post-processing

After generation:

1. A single wrapping markdown fence (including `` ```markdown ``) is removed when it encloses the whole document.
2. Any leading preamble before the first exact `## 工单目标` is sliced off, so the saved file starts at that heading.
3. The six heading strings are checked for presence and for strictly ascending first-occurrence order. If any heading is missing or the order is wrong, the CLI exits `1` and deletes the output file.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Slice written; all six headings present and in order. stdout is the output path. |
| `1` | Input error, generation failure, empty output, missing heading, or wrong heading order. Validation errors are listed on stderr; a failed output file is removed. |
| `130` | Interrupted (`Ctrl-C`). |

## Re-run heading assert

From the repo root:

```bash
bash scripts/assert_stable_headings.sh
```

The script runs `python3 -m acceptance_slice_engine --scope-file examples/sample-scope.md` twice into temp files and asserts that all six heading strings appear in each output. It prints `PASS` or `FAIL`. It needs a working backend (`XAI_API_KEY` or an authenticated `grok` CLI).

## License

[MIT](LICENSE). See [CHANGELOG.md](CHANGELOG.md) for releases.
