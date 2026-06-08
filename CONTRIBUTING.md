# Contributing

Issues and pull requests are welcome.

## Rule design

- Report only issues that can be identified reliably from DOCX OOXML.
- Keep checks read-only and local.
- Use `warning` when a finding may be intentional.
- Use `error` only for invalid files or unambiguous document defects.
- Include a focused test for every behavior change.

## Development checks

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

Please explain the practical document problem addressed by a new rule and note
known false-positive cases.

