from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .config import ConfigError, LintConfig, load_config
from .core import Finding, lint_docx


READ_FAILURE_RULES = {
    "file-not-found",
    "unsupported-file",
    "missing-document-xml",
    "invalid-docx",
    "read-error",
    "invalid-document-xml",
    "document-part-too-large",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="han-docx-lint",
        description="Check common quality issues in Chinese academic DOCX files.",
    )
    parser.add_argument("file", type=Path, help="DOCX file to inspect")
    parser.add_argument(
        "--config",
        type=Path,
        help="JSON rules configuration (version 1)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--max-paragraph-chars",
        type=int,
        default=600,
        metavar="N",
        help="warn when a paragraph exceeds N characters (default: 600)",
    )
    parser.add_argument(
        "--allow-no-references",
        action="store_true",
        help="do not warn when a references-section heading is absent",
    )
    return parser


def _text_output(path: Path, findings: list[Finding]) -> str:
    if not findings:
        return f"{path}: no findings"
    lines = [f"{path}: {len(findings)} finding(s)"]
    for finding in findings:
        location = f" paragraph {finding.paragraph}" if finding.paragraph else ""
        if finding.part:
            location = f" {finding.part}{location}"
        lines.append(
            f"{finding.severity.upper()} [{finding.rule}]{location}: {finding.message}"
        )
        if finding.excerpt:
            lines.append(f"  {finding.excerpt}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.max_paragraph_chars < 1:
        parser.error("--max-paragraph-chars must be greater than zero")

    try:
        config = load_config(args.config) if args.config else LintConfig(
            max_paragraph_chars=args.max_paragraph_chars,
            require_references=not args.allow_no_references,
        )
    except ConfigError as exc:
        parser.error(str(exc))

    findings = lint_docx(args.file, config=config)
    if args.format == "json":
        print(
            json.dumps(
                {
                    "file": str(args.file),
                    "findings": [finding.to_dict() for finding in findings],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(_text_output(args.file, findings))

    if any(finding.rule in READ_FAILURE_RULES for finding in findings):
        return 2
    if any(finding.severity == "error" for finding in findings):
        return 1
    return 0
