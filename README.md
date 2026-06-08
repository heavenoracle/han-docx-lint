# han-docx-lint

[中文](#中文) | [English](#english)

## 中文

`han-docx-lint` 是一个零运行时依赖的命令行工具，用于发现中文课程论文、报告和学术
文档中的常见质量问题。它直接读取 DOCX 内部的 OOXML，不会修改原文件，也不会上传文档。

当前检查项：

- 损坏或缺少关键内容的 DOCX 文件
- 文档中遗留的 `TODO`、`TBD`、`待补充` 等占位文本
- 连续重复标点，如 `！！`、`，，`
- 中文字符之间多余的空格
- 过长段落
- 连续空段落
- 缺少参考文献章节
- 缺少标题样式

### 安装与使用

```bash
python -m pip install .
han-docx-lint paper.docx
han-docx-lint paper.docx --format json
han-docx-lint paper.docx --max-paragraph-chars 800 --allow-no-references
```

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
```

The tool checks package integrity, placeholder text, repeated punctuation,
spaces between CJK characters, long paragraphs, consecutive empty paragraphs,
reference-section presence, and heading-style usage.

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

