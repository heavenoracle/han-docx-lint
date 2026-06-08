from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


BUILTIN_RULES = {
    "placeholder-text",
    "repeated-punctuation",
    "cjk-spacing",
    "long-paragraph",
    "consecutive-empty-paragraphs",
    "missing-references",
    "missing-heading-styles",
}
SEVERITIES = {"error", "warning", "info"}


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class PatternRule:
    rule: str
    pattern: re.Pattern[str]
    severity: str
    message: str


@dataclass(frozen=True)
class LintConfig:
    max_paragraph_chars: int = 600
    require_references: bool = True
    disabled_rules: frozenset[str] = field(default_factory=frozenset)
    severity_overrides: dict[str, str] = field(default_factory=dict)
    pattern_rules: tuple[PatternRule, ...] = ()

    def enabled(self, rule: str) -> bool:
        return rule not in self.disabled_rules

    def severity(self, rule: str, default: str) -> str:
        return self.severity_overrides.get(rule, default)


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{name} must be an object")
    return value


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{name} must be a non-empty string")
    return value


def _severity(value: Any, name: str) -> str:
    severity = _string(value, name)
    if severity not in SEVERITIES:
        raise ConfigError(f"{name} must be one of: {', '.join(sorted(SEVERITIES))}")
    return severity


def _pattern_rules(value: Any) -> tuple[PatternRule, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ConfigError("pattern_rules must be an array")

    result: list[PatternRule] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        rule_data = _object(item, f"pattern_rules[{index}]")
        rule = _string(rule_data.get("id"), f"pattern_rules[{index}].id")
        if rule in BUILTIN_RULES or rule in seen:
            raise ConfigError(f"duplicate or reserved rule id: {rule}")
        seen.add(rule)
        pattern_text = _string(
            rule_data.get("pattern"), f"pattern_rules[{index}].pattern"
        )
        flags_text = rule_data.get("flags", "")
        if not isinstance(flags_text, str) or any(flag not in "im" for flag in flags_text):
            raise ConfigError(f"pattern_rules[{index}].flags may contain only i and m")
        flags = (re.I if "i" in flags_text else 0) | (re.M if "m" in flags_text else 0)
        try:
            pattern = re.compile(pattern_text, flags)
        except re.error as exc:
            raise ConfigError(f"invalid regex for {rule}: {exc}") from exc
        result.append(
            PatternRule(
                rule=rule,
                pattern=pattern,
                severity=_severity(
                    rule_data.get("severity", "warning"),
                    f"pattern_rules[{index}].severity",
                ),
                message=_string(
                    rule_data.get("message"), f"pattern_rules[{index}].message"
                ),
            )
        )
    return tuple(result)


def config_from_dict(data: dict[str, Any]) -> LintConfig:
    version = data.get("version")
    if version != 1:
        raise ConfigError("version must be 1")

    settings = _object(data.get("settings", {}), "settings")
    max_chars = settings.get("max_paragraph_chars", 600)
    if not isinstance(max_chars, int) or isinstance(max_chars, bool) or max_chars < 1:
        raise ConfigError("settings.max_paragraph_chars must be a positive integer")
    require_references = settings.get("require_references", True)
    if not isinstance(require_references, bool):
        raise ConfigError("settings.require_references must be a boolean")

    disabled = data.get("disabled_rules", [])
    if not isinstance(disabled, list) or not all(isinstance(item, str) for item in disabled):
        raise ConfigError("disabled_rules must be an array of strings")
    unknown_disabled = set(disabled) - BUILTIN_RULES
    if unknown_disabled:
        raise ConfigError(f"unknown disabled rule: {sorted(unknown_disabled)[0]}")

    overrides_data = _object(data.get("severity_overrides", {}), "severity_overrides")
    unknown_overrides = set(overrides_data) - BUILTIN_RULES
    if unknown_overrides:
        raise ConfigError(f"unknown severity override: {sorted(unknown_overrides)[0]}")
    overrides = {
        rule: _severity(value, f"severity_overrides.{rule}")
        for rule, value in overrides_data.items()
    }

    return LintConfig(
        max_paragraph_chars=max_chars,
        require_references=require_references,
        disabled_rules=frozenset(disabled),
        severity_overrides=overrides,
        pattern_rules=_pattern_rules(data.get("pattern_rules")),
    )


def load_config(path: str | Path) -> LintConfig:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"unable to read config: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON config: {exc}") from exc
    return config_from_dict(_object(data, "config"))

