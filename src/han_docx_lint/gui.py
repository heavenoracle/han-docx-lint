from __future__ import annotations

import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .cli import READ_FAILURE_RULES
from .config import ConfigError, LintConfig, load_config
from .core import Finding, lint_docx

APP_TITLE = "han-docx-lint"


def finding_location(finding: Finding) -> str:
    parts: list[str] = []
    if finding.part:
        parts.append(finding.part)
    if finding.paragraph:
        parts.append(f"paragraph {finding.paragraph}")
    return " / ".join(parts) if parts else "document"


def findings_to_text(findings: list[Finding]) -> str:
    if not findings:
        return "No findings."

    lines: list[str] = []
    for index, finding in enumerate(findings, start=1):
        lines.append(
            f"{index}. {finding.severity.upper()} [{finding.rule}] "
            f"{finding_location(finding)}: {finding.message}"
        )
        if finding.excerpt:
            lines.append(f"   {finding.excerpt}")
    return "\n".join(lines)


def _summary(findings: list[Finding]) -> str:
    errors = sum(1 for finding in findings if finding.severity == "error")
    warnings = sum(1 for finding in findings if finding.severity == "warning")
    infos = sum(1 for finding in findings if finding.severity == "info")
    read_failures = sum(1 for finding in findings if finding.rule in READ_FAILURE_RULES)
    return (
        f"{len(findings)} finding(s): "
        f"{errors} error(s), {warnings} warning(s), {infos} info(s), "
        f"{read_failures} read failure(s)"
    )


class HanDocxLintGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x680")
        self.minsize(780, 520)

        self.docx_path = tk.StringVar()
        self.config_path = tk.StringVar()
        self.status_text = tk.StringVar(value="Select a DOCX file to begin.")
        self.last_findings: list[Finding] = []
        self.last_file: Path | None = None

        self._build_layout()

    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=12)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(4, weight=1)

        ttk.Label(container, text="DOCX file").grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        ttk.Entry(container, textvariable=self.docx_path).grid(
            row=0, column=1, sticky=tk.EW, padx=(8, 8), pady=(0, 8)
        )
        ttk.Button(container, text="Browse...", command=self._choose_docx).grid(
            row=0, column=2, sticky=tk.E, pady=(0, 8)
        )

        ttk.Label(container, text="Rules JSON").grid(row=1, column=0, sticky=tk.W, pady=(0, 8))
        ttk.Entry(container, textvariable=self.config_path).grid(
            row=1, column=1, sticky=tk.EW, padx=(8, 8), pady=(0, 8)
        )
        config_buttons = ttk.Frame(container)
        config_buttons.grid(row=1, column=2, sticky=tk.E, pady=(0, 8))
        ttk.Button(config_buttons, text="Browse...", command=self._choose_config).pack(side=tk.LEFT)
        ttk.Button(config_buttons, text="Clear", command=lambda: self.config_path.set("")).pack(
            side=tk.LEFT, padx=(6, 0)
        )

        actions = ttk.Frame(container)
        actions.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=(4, 10))
        self.run_button = ttk.Button(actions, text="Run check", command=self._run_check)
        self.run_button.pack(side=tk.LEFT)
        ttk.Button(actions, text="Copy results", command=self._copy_results).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(actions, text="Save JSON report...", command=self._save_json).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        ttk.Label(container, textvariable=self.status_text).grid(
            row=3, column=0, columnspan=3, sticky=tk.W, pady=(0, 8)
        )

        table_frame = ttk.Frame(container)
        table_frame.grid(row=4, column=0, columnspan=3, sticky=tk.NSEW)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        columns = ("severity", "rule", "location", "message", "excerpt")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.table.heading("severity", text="Severity")
        self.table.heading("rule", text="Rule")
        self.table.heading("location", text="Location")
        self.table.heading("message", text="Message")
        self.table.heading("excerpt", text="Excerpt")
        self.table.column("severity", width=80, stretch=False)
        self.table.column("rule", width=180, stretch=False)
        self.table.column("location", width=210, stretch=False)
        self.table.column("message", width=280, stretch=True)
        self.table.column("excerpt", width=260, stretch=True)
        self.table.grid(row=0, column=0, sticky=tk.NSEW)

        y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.table.yview)
        y_scroll.grid(row=0, column=1, sticky=tk.NS)
        self.table.configure(yscrollcommand=y_scroll.set)

    def _choose_docx(self) -> None:
        path = filedialog.askopenfilename(
            title="Select DOCX file",
            filetypes=(("Word document", "*.docx"), ("All files", "*.*")),
        )
        if path:
            self.docx_path.set(path)

    def _choose_config(self) -> None:
        path = filedialog.askopenfilename(
            title="Select rules JSON",
            filetypes=(("JSON rules", "*.json"), ("All files", "*.*")),
        )
        if path:
            self.config_path.set(path)

    def _run_check(self) -> None:
        path_text = self.docx_path.get().strip()
        if not path_text:
            messagebox.showerror(APP_TITLE, "Please select a DOCX file first.")
            return

        source = Path(path_text)
        config_text = self.config_path.get().strip()
        config_path = Path(config_text) if config_text else None

        self.run_button.configure(state=tk.DISABLED)
        self.status_text.set("Checking document...")
        self._clear_table()

        thread = threading.Thread(
            target=self._run_check_worker,
            args=(source, config_path),
            daemon=True,
        )
        thread.start()

    def _run_check_worker(self, source: Path, config_path: Path | None) -> None:
        try:
            config = load_config(config_path) if config_path else LintConfig()
            findings = lint_docx(source, config=config)
        except ConfigError as exc:
            self.after(0, self._show_error, f"Invalid rules config: {exc}")
            return
        except Exception as exc:  # Defensive GUI boundary; core returns findings for normal read errors.
            self.after(0, self._show_error, f"Unexpected error: {exc}")
            return
        self.after(0, self._show_results, source, findings)

    def _show_error(self, message: str) -> None:
        self.run_button.configure(state=tk.NORMAL)
        self.status_text.set(message)
        messagebox.showerror(APP_TITLE, message)

    def _show_results(self, source: Path, findings: list[Finding]) -> None:
        self.last_file = source
        self.last_findings = findings
        self._clear_table()
        for finding in findings:
            self.table.insert(
                "",
                tk.END,
                values=(
                    finding.severity,
                    finding.rule,
                    finding_location(finding),
                    finding.message,
                    finding.excerpt or "",
                ),
            )
        self.status_text.set(_summary(findings) if findings else "No findings.")
        self.run_button.configure(state=tk.NORMAL)

    def _clear_table(self) -> None:
        for item in self.table.get_children():
            self.table.delete(item)

    def _copy_results(self) -> None:
        text = findings_to_text(self.last_findings)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_text.set("Copied results to clipboard.")

    def _save_json(self) -> None:
        if self.last_file is None:
            messagebox.showerror(APP_TITLE, "Run a check before saving a report.")
            return
        default_name = f"{self.last_file.stem}-han-docx-lint-report.json"
        target = filedialog.asksaveasfilename(
            title="Save JSON report",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=(("JSON report", "*.json"), ("All files", "*.*")),
        )
        if not target:
            return
        payload = {
            "file": str(self.last_file),
            "findings": [finding.to_dict() for finding in self.last_findings],
        }
        try:
            Path(target).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"Unable to save report: {exc}")
            return
        self.status_text.set(f"Saved JSON report: {target}")


def main() -> int:
    app = HanDocxLintGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
