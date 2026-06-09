# han-docx-lint

[中文](#中文) | [English](#english)

## 中文

`han-docx-lint` 是一个零运行时依赖的命令行工具，用于发现中文课程论文、报告和学术
文档中的常见质量问题。它直接读取 DOCX 内部的 OOXML，不会修改原文件，也不会上传文档。

当前检查项：

- 损坏或缺少关键内容的 DOCX 文件
- 正文、表格、页眉、页脚、脚注、尾注和批注中的文本
- 文档中遗留的 `TODO`、`TBD`、`待补充` 等占位文本
- 连续重复标点，如 `！！`、`，，`
- 中文字符之间单个或连续多个 ASCII 空格
- 过长段落
- 连续空段落
- 缺少参考文献章节
- 缺少标题样式

### 安装与使用

```bash
python -m pip install .
han-docx-lint paper.docx
han-docx-lint paper.docx --format json
han-docx-lint paper.docx --config rules.json
han-docx-lint paper.docx --max-paragraph-chars 800 --allow-no-references
```

### 桌面 GUI、Windows exe 与 macOS app

如果不想使用命令行，可以使用桌面 GUI：

```bash
python -m pip install .
han-docx-lint-gui
```

GUI 支持选择 `.docx` 文件、选择可选的 JSON 规则配置、运行检查、复制结果，并导出 JSON 报告。

从 release 构建时，GitHub Actions 会生成两个压缩包：

- `han-docx-lint-gui-windows.zip`：包含 `han-docx-lint-gui.exe`
- `han-docx-lint-gui-macos.zip`：包含 `HanDocxLint.app`

本地打包桌面程序：

```bash
python -m pip install . pyinstaller
python scripts/build_desktop.py
```

Windows 构建产物位于 `dist/han-docx-lint-gui.exe`；macOS 构建产物位于 `dist/HanDocxLint.app`。

规则配置采用版本化 JSON，可关闭内置规则、调整严重级别并定义可审计的正则文本规则。
可直接使用配套规则库：[han-docx-rules](https://github.com/heavenoracle/han-docx-rules)。
在 GitHub 仓库中自动检查文档可使用
[han-docx-action](https://github.com/heavenoracle/han-docx-action)。
最小配置示例见 [`examples/rules.json`](examples/rules.json)。
架构与仓库职责见 [`docs/ecosystem.md`](docs/ecosystem.md)。

使用 `--config` 时，配置文件接管 `max_paragraph_chars` 和
`require_references`；`--max-paragraph-chars` 与 `--allow-no-references`
仅在没有提供配置文件时生效。配置文件应像代码一样经过审查，不应直接运行来自不可信
Pull Request 的规则。为限制资源消耗，单个 OOXML 部件最大为 20 MiB，自定义正则仅扫描
每段前 100,000 个字符。

退出码为 `0` 表示未发现错误级问题，`1` 表示发现错误，`2` 表示文件无法读取或参数错误。
警告不会导致退出码为 `1`。

该工具只负责发现可机械检查的问题，无法判断论文内容是否真实、论证是否充分、引用是否
准确，也不能替代学校或期刊的具体格式规范。

## English

`han-docx-lint` is a dependency-free CLI that detects common quality issues in
Chinese academic and coursework DOCX files. It reads OOXML locally, never
modifies the source file, and does not upload documents.

```bash
python -m pip install .
han-docx-lint paper.docx
han-docx-lint paper.docx --format json
han-docx-lint paper.docx --config rules.json
```

### Desktop GUI, Windows exe, and macOS app

A desktop GUI is available for non-CLI use:

```bash
python -m pip install .
han-docx-lint-gui
```

The GUI lets users select a `.docx` file, optionally select a JSON rules profile, run checks, copy results, and export a JSON report.

Release builds generate:

- `han-docx-lint-gui-windows.zip`, containing `han-docx-lint-gui.exe`
- `han-docx-lint-gui-macos.zip`, containing `HanDocxLint.app`

To build locally:

```bash
python -m pip install . pyinstaller
python scripts/build_desktop.py
```

The tool checks package integrity, placeholder text, repeated punctuation,
single and multiple ASCII spaces between CJK characters, long paragraphs,
consecutive empty paragraphs, reference-section presence, and heading-style
usage. It checks paragraphs in the main document, tables, headers, footers,
footnotes, endnotes, and comments, and reports the originating OOXML part.

Versioned JSON configurations can disable built-in checks, override severities,
and add auditable regex-based text rules. See
[han-docx-rules](https://github.com/heavenoracle/han-docx-rules) for profiles and
[han-docx-action](https://github.com/heavenoracle/han-docx-action) for CI use.
See [`examples/rules.json`](examples/rules.json) for the configuration format.
See [`docs/ecosystem.md`](docs/ecosystem.md) for architecture and repository
responsibilities.

When `--config` is provided, the profile controls `max_paragraph_chars` and
`require_references`; the corresponding CLI flags apply only without a profile.
Review profiles like code before use. The engine limits each OOXML part to
20 MiB and scans at most the first 100,000 characters of a paragraph with each
custom regular expression.

## Development

```bash
python -m unittest discover -s tests -v
python -m han_docx_lint --help
```

See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a rule. Each rule should
have a clear rationale, avoid changing files, and include tests for both
positive and negative cases.

## License

MIT
