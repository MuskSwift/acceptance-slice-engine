"""argparse CLI for Acceptance Slice Engine v0."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

from .generate import generate, strip_leading_preamble, strip_wrapping_fences
from .validate import validate_or_errors


def slugify(scope: str, max_len: int = 48) -> str:
    """ASCII-ish slug from scope text: keep letters, digits, CJK; spaces become hyphens."""
    first_line = next((ln.strip() for ln in scope.splitlines() if ln.strip()), scope)
    text = first_line.strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^\w\u4e00-\u9fff\-]+", "", text, flags=re.UNICODE)
    text = re.sub(r"-{2,}", "-", text).strip("-._")
    if not text:
        text = hashlib.sha1(scope.encode("utf-8")).hexdigest()[:10]
    return text[:max_len]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="acceptance-slice-engine",
        description=(
            "Acceptance Slice Engine v0 — turn a scope or PRD "
            "(plus optional constraints) into a six-heading Chinese acceptance slice."
        ),
    )
    parser.add_argument(
        "--scope",
        help="Scope or PRD text (same channel as --prd)",
    )
    parser.add_argument(
        "--scope-file",
        metavar="PATH",
        help="Path to a scope or PRD file (same channel as --prd-file)",
    )
    parser.add_argument(
        "--prd",
        help="Alias of --scope; joined into the same scope channel",
    )
    parser.add_argument(
        "--prd-file",
        metavar="PATH",
        help="Alias of --scope-file; joined into the same scope channel",
    )
    parser.add_argument(
        "--constraints",
        help="Optional constraints as a string",
    )
    parser.add_argument(
        "--constraints-file",
        metavar="PATH",
        help="Path to a file containing optional constraints",
    )
    parser.add_argument(
        "--out",
        help="Output markdown path (default: ./out/<slug>-acceptance-slice.md)",
    )
    return parser.parse_args(argv)


def _read_text(path: str) -> str:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"file not found: {path}")
    return file_path.read_text(encoding="utf-8")


def _join_parts(parts: list[str]) -> str:
    return "\n\n".join(part for part in parts if part)


def resolve_inputs(args: argparse.Namespace) -> tuple[str, str]:
    """Join every provided scope/PRD source; require at least one non-empty."""
    scope_parts: list[str] = []
    for inline in (args.scope, args.prd):
        if inline and inline.strip():
            scope_parts.append(inline.strip())
    for file_path in (args.scope_file, args.prd_file):
        if file_path:
            scope_parts.append(_read_text(file_path).strip())
    scope = _join_parts(scope_parts)
    if not scope:
        raise ValueError(
            "at least one of --scope, --scope-file, --prd, or --prd-file is required"
        )

    constraint_parts: list[str] = []
    if args.constraints and args.constraints.strip():
        constraint_parts.append(args.constraints.strip())
    if args.constraints_file:
        constraint_parts.append(_read_text(args.constraints_file).strip())
    constraints = _join_parts(constraint_parts)
    return scope, constraints


def resolve_out(out_arg: str | None, scope: str) -> Path:
    if out_arg:
        return Path(out_arg)
    return Path("out") / f"{slugify(scope)}-acceptance-slice.md"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_path: Path | None = None
    try:
        scope, constraints = resolve_inputs(args)
        markdown = strip_wrapping_fences(generate(scope, constraints))
        markdown = strip_leading_preamble(markdown)
        if not markdown.strip():
            raise RuntimeError("generation produced empty markdown")

        out_path = resolve_out(args.out, scope)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown.rstrip() + "\n", encoding="utf-8")

        errors = validate_or_errors(markdown)
        if errors:
            try:
                out_path.unlink()
            except OSError:
                pass
            print("validation failed:", file=sys.stderr)
            for error in errors:
                print(f"  {error}", file=sys.stderr)
            return 1

        print(str(out_path))
        return 0
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
