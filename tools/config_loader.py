"""
config_loader.py - Type-safe loader for the modular YAML configuration.

Loads the declarative configuration under ``config/`` (skill registry, tools,
hooks, feature flags, LLM parameters, sources) into typed dataclasses. This is
the configuration counterpart of ``tools/config.py`` (which carries the
knowledge-crawl AppConfig). Feature flags can be overridden via environment
variables of the form ``WPSD_FLAG_<NAME_UPPER>``.

PyYAML is required for YAML loading. If unavailable, a clear ConfigError is
raised with install instructions; JSON fallback files (``config/*.json``) are
read when present.

Usage:
    from tools.config_loader import load_system_config, FeatureFlags
    sys_cfg = load_system_config()
    if sys_cfg.flags.enable_router: ...
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.exceptions import ConfigError
from tools.logger import setup_logger

logger = setup_logger("config_loader")

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


def _load_yaml_or_json(path_no_ext: Path) -> dict[str, Any]:
    yaml_path = path_no_ext.with_suffix(".yaml")
    json_path = path_no_ext.with_suffix(".json")
    if yaml_path.exists():
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as ex:  # pragma: no cover - environment guard
            raise ConfigError(
                "PyYAML is required to read config/*.yaml. Install with: pip install pyyaml",
                key="pyyaml",
            ) from ex
        with yaml_path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))
    raise ConfigError(f"Config file not found: {path_no_ext}.yaml or .json", key=str(path_no_ext))


def _env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name, "").lower()
    if val in ("1", "true", "yes", "on"):
        return True
    if val in ("0", "false", "no", "off"):
        return False
    return default


@dataclass
class FeatureFlags:
    enable_router: bool = True
    enable_hooks: bool = True
    enable_schema_validation: bool = True
    enable_token_budget: bool = True
    enable_compaction: bool = True
    enable_event_emitter: bool = False
    enable_live_fetch: bool = False
    enable_knowledge_crawl: bool = True
    enable_bilingual: bool = True
    strict_gates: bool = True
    max_gate_retries: int = 2

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FeatureFlags":
        flags = data.get("flags", data)
        f = cls(
            enable_router=bool(flags.get("enable_router", True)),
            enable_hooks=bool(flags.get("enable_hooks", True)),
            enable_schema_validation=bool(flags.get("enable_schema_validation", True)),
            enable_token_budget=bool(flags.get("enable_token_budget", True)),
            enable_compaction=bool(flags.get("enable_compaction", True)),
            enable_event_emitter=bool(flags.get("enable_event_emitter", False)),
            enable_live_fetch=bool(flags.get("enable_live_fetch", False)),
            enable_knowledge_crawl=bool(flags.get("enable_knowledge_crawl", True)),
            enable_bilingual=bool(flags.get("enable_bilingual", True)),
            strict_gates=bool(flags.get("strict_gates", True)),
            max_gate_retries=int(flags.get("max_gate_retries", 2)),
        )
        return f.apply_env_overrides()

    def apply_env_overrides(self) -> "FeatureFlags":
        for attr in (
            "enable_router",
            "enable_hooks",
            "enable_schema_validation",
            "enable_token_budget",
            "enable_compaction",
            "enable_event_emitter",
            "enable_live_fetch",
            "enable_knowledge_crawl",
            "enable_bilingual",
            "strict_gates",
        ):
            env_name = f"WPSD_FLAG_{attr.upper()}"
            if os.environ.get(env_name) is not None:
                setattr(self, attr, _env_bool(env_name, getattr(self, attr)))
        env_retries = os.environ.get("WPSD_FLAG_MAX_GATE_RETRIES")
        if env_retries and env_retries.isdigit():
            self.max_gate_retries = int(env_retries)
        return self


@dataclass
class LLMParams:
    model: str = "claude-sonnet-4.5"
    temperature: float = 0.2
    top_p: float = 0.95
    max_output_tokens: int = 8192
    context_window: int = 200_000
    reserve_for_output: int = 8192
    soft_cap_ratio: float = 0.80
    timeout_seconds: int = 30
    max_retries: int = 3
    skill_budgets: dict[str, int] = field(default_factory=dict)
    compaction: dict[str, Any] = field(default_factory=dict)
    error_handling: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMParams":
        d = data.get("defaults", data)
        return cls(
            model=str(d.get("model", "claude-sonnet-4.5")),
            temperature=float(d.get("temperature", 0.2)),
            top_p=float(d.get("top_p", 0.95)),
            max_output_tokens=int(d.get("max_output_tokens", 8192)),
            context_window=int(d.get("context_window", 200_000)),
            reserve_for_output=int(d.get("reserve_for_output", 8192)),
            soft_cap_ratio=float(d.get("soft_cap_ratio", 0.80)),
            timeout_seconds=int(d.get("timeout_seconds", 30)),
            max_retries=int(d.get("max_retries", 3)),
            skill_budgets=dict(data.get("skill_budgets", {})),
            compaction=dict(data.get("compaction", {})),
            error_handling=dict(data.get("error_handling", {})),
        )


@dataclass
class SystemConfig:
    skill_registry: dict[str, Any] = field(default_factory=dict)
    tools: dict[str, Any] = field(default_factory=dict)
    hooks: dict[str, Any] = field(default_factory=dict)
    flags: FeatureFlags = field(default_factory=FeatureFlags)
    llm: LLMParams = field(default_factory=LLMParams)
    sources: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_registry": dict(self.skill_registry),
            "tools": dict(self.tools),
            "hooks": dict(self.hooks),
            "flags": self.flags.__dict__,
            "llm": self.llm.__dict__,
            "sources": dict(self.sources),
        }


def load_system_config(config_dir: Path | None = None) -> SystemConfig:
    """Load and validate all modular config files into a SystemConfig."""
    base = config_dir or CONFIG_DIR
    logger.debug("loading system config from %s", base)
    cfg = SystemConfig()
    cfg.skill_registry = _load_yaml_or_json(base / "skill_registry")
    cfg.tools = _load_yaml_or_json(base / "tools")
    cfg.hooks = _load_yaml_or_json(base / "hooks")
    cfg.flags = FeatureFlags.from_dict(_load_yaml_or_json(base / "feature_flags"))
    cfg.llm = LLMParams.from_dict(_load_yaml_or_json(base / "llm_params"))
    cfg.sources = _load_yaml_or_json(base / "sources")
    _validate(cfg)
    return cfg


def _validate(cfg: SystemConfig) -> None:
    if not cfg.skill_registry.get("skills"):
        raise ConfigError("skill_registry.yaml defines no skills", key="skills")
    if not cfg.tools.get("tools"):
        raise ConfigError("tools.yaml defines no tools", key="tools")
    if cfg.llm.context_window <= cfg.llm.reserve_for_output:
        raise ConfigError("llm_params: context_window must exceed reserve_for_output", key="context_window")
    if not (0 < cfg.llm.soft_cap_ratio < 1):
        raise ConfigError("llm_params: soft_cap_ratio must be in (0,1)", key="soft_cap_ratio")
    names = [s["name"] for s in cfg.skill_registry["skills"]]
    if len(names) != len(set(names)):
        raise ConfigError("skill_registry: duplicate skill names", key="skills")
