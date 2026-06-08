import tempfile
import unittest
import zipfile
from pathlib import Path

from han_docx_lint.config import ConfigError, config_from_dict
from han_docx_lint.core import lint_docx


DOCUMENT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>{paragraphs}</w:body>
</w:document>
"""


def paragraph(text="", style=None):
    properties = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{properties}<w:r><w:t>{text}</w:t></w:r></w:p>"


def make_docx(path, paragraphs):
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("word/document.xml", DOCUMENT.format(paragraphs=paragraphs))


class LintDocxTests(unittest.TestCase):
    def test_clean_document_has_no_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clean.docx"
            make_docx(
                path,
                paragraph("正文标题", "Heading1")
                + paragraph("这是一段格式正常的正文。")
                + paragraph("参考文献"),
            )

            self.assertEqual([], lint_docx(path))

    def test_reports_content_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "issues.docx"
            make_docx(
                path,
                paragraph("待补充！！")
                + paragraph("中文  字符")
                + paragraph()
                + paragraph()
                + paragraph(),
            )

            rules = {finding.rule for finding in lint_docx(path)}

            self.assertEqual(
                {
                    "placeholder-text",
                    "repeated-punctuation",
                    "cjk-spacing",
                    "consecutive-empty-paragraphs",
                    "missing-references",
                    "missing-heading-styles",
                },
                rules,
            )

    def test_reports_invalid_package(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.docx"
            path.write_text("not a docx", encoding="utf-8")

            findings = lint_docx(path)

            self.assertEqual("invalid-docx", findings[0].rule)
            self.assertEqual("error", findings[0].severity)

    def test_allows_typographic_abstract_label(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "abstract.docx"
            make_docx(
                path,
                paragraph("摘  要：这是摘要。", "Heading1") + paragraph("参考文献"),
            )

            rules = {finding.rule for finding in lint_docx(path)}

            self.assertNotIn("cjk-spacing", rules)

    def test_missing_file_is_an_error(self):
        findings = lint_docx("/definitely/missing.docx")
        self.assertEqual("file-not-found", findings[0].rule)

    def test_config_disables_rule_and_changes_severity(self):
        config = config_from_dict(
            {
                "version": 1,
                "disabled_rules": ["missing-heading-styles"],
                "severity_overrides": {"missing-references": "error"},
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "configured.docx"
            make_docx(path, paragraph("正文"))

            findings = lint_docx(path, config=config)

        self.assertEqual(["missing-references"], [item.rule for item in findings])
        self.assertEqual("error", findings[0].severity)

    def test_config_adds_pattern_rule(self):
        config = config_from_dict(
            {
                "version": 1,
                "settings": {"require_references": False},
                "disabled_rules": ["missing-heading-styles"],
                "pattern_rules": [
                    {
                        "id": "informal-wording",
                        "pattern": "超级",
                        "severity": "info",
                        "message": "Informal wording found.",
                    }
                ],
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "custom.docx"
            make_docx(path, paragraph("这是超级重要的结论。"))

            findings = lint_docx(path, config=config)

        self.assertEqual(["informal-wording"], [item.rule for item in findings])

    def test_config_rejects_reserved_pattern_rule_id(self):
        with self.assertRaises(ConfigError):
            config_from_dict(
                {
                    "version": 1,
                    "pattern_rules": [
                        {
                            "id": "cjk-spacing",
                            "pattern": "x",
                            "message": "reserved",
                        }
                    ],
                }
            )


if __name__ == "__main__":
    unittest.main()
