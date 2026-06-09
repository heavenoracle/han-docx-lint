import unittest

from han_docx_lint.core import Finding
from han_docx_lint.gui import finding_location, findings_to_text


class GuiHelperTests(unittest.TestCase):
    def test_finding_location_uses_part_and_paragraph(self):
        finding = Finding(
            rule="placeholder-text",
            severity="error",
            message="Placeholder text remains in the document.",
            part="word/document.xml",
            paragraph=3,
        )

        self.assertEqual("word/document.xml / paragraph 3", finding_location(finding))

    def test_findings_to_text_includes_rule_and_excerpt(self):
        finding = Finding(
            rule="cjk-single-space",
            severity="warning",
            message="Single ASCII space found between Chinese characters.",
            part="word/header1.xml",
            paragraph=1,
            excerpt="中 文",
        )

        output = findings_to_text([finding])

        self.assertIn("WARNING [cjk-single-space]", output)
        self.assertIn("word/header1.xml / paragraph 1", output)
        self.assertIn("中 文", output)


if __name__ == "__main__":
    unittest.main()
