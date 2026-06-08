from __future__ import annotations

import re
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree

from .config import LintConfig


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{WORD_NS}}}"
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME)\b|待补充|待填写|此处填写", re.I)
REPEATED_PUNCTUATION_RE = re.compile(r"([，。！？；：、,.!?;:])\1+")
CJK_SPACE_RE = re.compile(r"(?<=[\u3400-\u9fff]) {2,}(?=[\u3400-\u9fff])")
REFERENCE_RE = re.compile(r"^\s*(?:参考文献|引用文献|References)\s*[:：]?\s*$", re.I)
SPACED_LABEL_RE = re.compile(r"(摘  要|关 键 词)")


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    message: str
    paragraph: int | None = None
    excerpt: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class Paragraph:
    number: int
    text: str
    style: str | None


def _paragraphs(root: ElementTree.Element) -> list[Paragraph]:
    result: list[Paragraph] = []
    for number, node in enumerate(root.findall(f".//{W}body/{W}p"), start=1):
        text = "".join(part.text or "" for part in node.findall(f".//{W}t"))
        style_node = node.find(f"./{W}pPr/{W}pStyle")
        style = style_node.get(f"{W}val") if style_node is not None else None
        result.append(Paragraph(number=number, text=text, style=style))
    return result


def _excerpt(text: str, limit: int = 80) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def _content_findings(
    paragraphs: Iterable[Paragraph],
    *,
    config: LintConfig,
) -> list[Finding]:
    findings: list[Finding] = []
    items = list(paragraphs)
    empty_run = 0
    has_references = False
    has_heading_style = False

    for paragraph in items:
        text = paragraph.text.strip()
        if not text:
            empty_run += 1
            if empty_run == 3:
                if config.enabled("consecutive-empty-paragraphs"):
                    findings.append(
                    Finding(
                        "consecutive-empty-paragraphs",
                        config.severity("consecutive-empty-paragraphs", "warning"),
                        "Three or more consecutive empty paragraphs found.",
                        paragraph.number,
                    )
                )
            continue

        empty_run = 0
        has_references = has_references or bool(REFERENCE_RE.match(text))
        has_heading_style = has_heading_style or bool(
            paragraph.style
            and (
                paragraph.style.lower().startswith("heading")
                or paragraph.style.startswith("标题")
            )
        )

        spacing_text = SPACED_LABEL_RE.sub("", text)
        checks = (
            (
                PLACEHOLDER_RE,
                text,
                "placeholder-text",
                "error",
                "Placeholder text remains in the document.",
            ),
            (
                REPEATED_PUNCTUATION_RE,
                text,
                "repeated-punctuation",
                "warning",
                "Repeated punctuation found.",
            ),
            (
                CJK_SPACE_RE,
                spacing_text,
                "cjk-spacing",
                "warning",
                "Multiple spaces found between Chinese characters.",
            ),
        )
        for pattern, checked_text, rule, severity, message in checks:
            if config.enabled(rule) and pattern.search(checked_text):
                findings.append(
                    Finding(
                        rule,
                        config.severity(rule, severity),
                        message,
                        paragraph.number,
                        _excerpt(text),
                    )
                )

        if config.enabled("long-paragraph") and len(text) > config.max_paragraph_chars:
            findings.append(
                Finding(
                    "long-paragraph",
                    config.severity("long-paragraph", "warning"),
                    f"Paragraph exceeds {config.max_paragraph_chars} characters.",
                    paragraph.number,
                    _excerpt(text),
                )
            )

        for pattern_rule in config.pattern_rules:
            if pattern_rule.pattern.search(text):
                findings.append(
                    Finding(
                        pattern_rule.rule,
                        pattern_rule.severity,
                        pattern_rule.message,
                        paragraph.number,
                        _excerpt(text),
                    )
                )

    if (
        config.require_references
        and config.enabled("missing-references")
        and not has_references
    ):
        findings.append(
            Finding(
                "missing-references",
                config.severity("missing-references", "warning"),
                "No standalone references-section heading was found.",
            )
        )
    if items and config.enabled("missing-heading-styles") and not has_heading_style:
        findings.append(
            Finding(
                "missing-heading-styles",
                config.severity("missing-heading-styles", "warning"),
                "No paragraph using a Heading/标题 style was found.",
            )
        )
    return findings


def lint_docx(
    path: str | Path,
    *,
    max_paragraph_chars: int = 600,
    require_references: bool = True,
    config: LintConfig | None = None,
) -> list[Finding]:
    active_config = config or LintConfig(
        max_paragraph_chars=max_paragraph_chars,
        require_references=require_references,
    )
    source = Path(path)
    if not source.is_file():
        return [Finding("file-not-found", "error", f"File not found: {source}")]
    if source.suffix.lower() != ".docx":
        return [Finding("unsupported-file", "error", "Expected a .docx file.")]

    try:
        with zipfile.ZipFile(source) as package:
            try:
                document_xml = package.read("word/document.xml")
            except KeyError:
                return [
                    Finding(
                        "missing-document-xml",
                        "error",
                        "DOCX package does not contain word/document.xml.",
                    )
                ]
    except zipfile.BadZipFile:
        return [Finding("invalid-docx", "error", "File is not a valid DOCX/ZIP package.")]
    except OSError as exc:
        return [Finding("read-error", "error", f"Unable to read file: {exc}")]

    try:
        root = ElementTree.fromstring(document_xml)
    except ElementTree.ParseError:
        return [Finding("invalid-document-xml", "error", "word/document.xml is invalid.")]

    return _content_findings(
        _paragraphs(root),
        config=active_config,
    )
