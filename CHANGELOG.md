# Changelog

## 0.3.0 - 2026-06-09

- Check table paragraphs, headers, footers, footnotes, endnotes, and comments.
- Report the originating OOXML part for paragraph findings.
- Split single and multiple CJK-space findings.
- Reject OOXML parts larger than 20 MiB and bound custom pattern scan length.
- Accept rationale and false-positive documentation for custom pattern rules.

## 0.2.0 - 2026-06-08

- Add versioned JSON rule configurations.
- Add built-in rule toggles, severity overrides, and custom text pattern rules.

## 0.1.0 - 2026-06-08

- Add read-only DOCX package validation.
- Add checks for placeholders, repeated punctuation, CJK spacing, long
  paragraphs, consecutive empty paragraphs, references, and heading styles.
- Add text and JSON output formats.
