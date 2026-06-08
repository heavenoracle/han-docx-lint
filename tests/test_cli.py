import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from han_docx_lint.cli import main


class CliTests(unittest.TestCase):
    def test_missing_file_returns_error_and_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.docx"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main([str(path), "--format", "json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(2, status)
        self.assertEqual("file-not-found", payload["findings"][0]["rule"])


if __name__ == "__main__":
    unittest.main()
