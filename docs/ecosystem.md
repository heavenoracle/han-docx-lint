# Han DOCX Quality Ecosystem

The ecosystem provides privacy-first, extensible quality infrastructure for
Chinese academic DOCX files.

```text
han-docx-rules -- JSON profiles --> han-docx-lint -- JSON findings
                                        ^
                                        |
                                han-docx-action
                              GitHub CI orchestration
```

## Responsibilities

- `han-docx-lint` owns DOCX parsing, configuration validation, rule execution,
  findings, and exit-code behavior.
- `han-docx-rules` owns reusable, reviewable profiles. It does not claim that
  profiles represent an institution's official requirements.
- `han-docx-action` owns file discovery, CI orchestration, aggregate reports,
  and artifact upload.

## Design constraints

- Documents are processed locally or inside the selected CI runner.
- The checking engine remains dependency-free at runtime.
- Profiles are versioned JSON and can be audited before use.
- Machine-readable findings allow future editor and reporting integrations.
- Rules should avoid claiming correctness where human judgment is required.

