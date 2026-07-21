"""
test_config_loader.py - Tests for tools/config_loader.py.
Run: pytest tools/test_config_loader.py -v
"""

from __future__ import annotations

import pytest

from tools.config_loader import FeatureFlags, LLMParams, load_system_config
from tools.exceptions import ConfigError


class TestSystemConfig:
    def test_loads_all(self) -> None:
        c = load_system_config()
        assert len(c.skill_registry["skills"]) == 6
        assert len(c.tools["tools"]) == 12
        assert c.flags.enable_router is True
        assert c.llm.context_window > c.llm.reserve_for_output

    def test_skill_names_unique(self) -> None:
        c = load_system_config()
        names = [s["name"] for s in c.skill_registry["skills"]]
        assert len(names) == len(set(names))

    def test_to_dict(self) -> None:
        c = load_system_config()
        d = c.to_dict()
        assert "flags" in d and "llm" in d


class TestFeatureFlags:
    def test_defaults(self) -> None:
        f = FeatureFlags.from_dict({"flags": {}})
        assert f.enable_router is True
        assert f.max_gate_retries == 2

    def test_env_override(self, monkeypatch) -> None:
        monkeypatch.setenv("WPSD_FLAG_ENABLE_ROUTER", "false")
        monkeypatch.setenv("WPSD_FLAG_MAX_GATE_RETRIES", "5")
        f = FeatureFlags.from_dict({"flags": {}})
        assert f.enable_router is False
        assert f.max_gate_retries == 5


class TestLLMParams:
    def test_defaults(self) -> None:
        p = LLMParams.from_dict({"defaults": {}})
        assert 0 < p.soft_cap_ratio < 1
        assert p.model


class TestValidation:
    def test_invalid_soft_cap_raises(self) -> None:
        p = LLMParams.from_dict(
            {"defaults": {"soft_cap_ratio": 1.5, "context_window": 100000, "reserve_for_output": 10}}
        )
        with pytest.raises(ConfigError):
            from tools.config_loader import _validate, SystemConfig

            _validate(SystemConfig(llm=p, skill_registry={"skills": [{"name": "x"}]}, tools={"tools": [{"name": "t"}]}))
