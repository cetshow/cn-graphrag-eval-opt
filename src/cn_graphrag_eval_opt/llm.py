from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_LLM_ENV_PATH = Path(".env")


@dataclass(frozen=True)
class LLMConfig:
    provider: str = "local"
    api_protocol: str = "none"
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    temperature: float = 0.2
    top_p: float = 1.0
    max_tokens: int = 2048
    timeout_seconds: int = 60
    retry_count: int = 2
    anthropic_base_url: str = ""

    @property
    def is_openai_compatible(self) -> bool:
        return self.api_protocol == "openai"

    def to_safe_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["api_key"] = _mask_secret(self.api_key)
        return payload

    def openai_chat_payload(
        self,
        user_prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> dict[str, object]:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }


def load_llm_config(env_path: str | Path = DEFAULT_LLM_ENV_PATH) -> LLMConfig:
    values = _read_env_file(Path(env_path))
    values.update({key: value for key, value in os.environ.items() if key in _LLM_ENV_KEYS})
    return LLMConfig(
        provider=values.get("LLM_PROVIDER", "local").strip().lower(),
        api_protocol=values.get("LLM_API_PROTOCOL", "none").strip().lower(),
        base_url=values.get("LLM_BASE_URL", "").strip().rstrip("/"),
        api_key=values.get("LLM_API_KEY", "").strip(),
        model=values.get("LLM_MODEL", "").strip(),
        temperature=_float_env(values, "LLM_TEMPERATURE", 0.2),
        top_p=_float_env(values, "LLM_TOP_P", 1.0),
        max_tokens=_int_env(values, "LLM_MAX_TOKENS", 2048),
        timeout_seconds=_int_env(values, "LLM_TIMEOUT_SECONDS", 60),
        retry_count=_int_env(values, "LLM_RETRY_COUNT", 2),
        anthropic_base_url=values.get("ANTHROPIC_BASE_URL", "").strip().rstrip("/"),
    )


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid .env line {line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_quotes(value.strip())
        if key:
            values[key] = value
    return values


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _float_env(values: dict[str, str], key: str, default: float) -> float:
    raw = values.get(key, "")
    return default if raw == "" else float(raw)


def _int_env(values: dict[str, str], key: str, default: int) -> int:
    raw = values.get(key, "")
    return default if raw == "" else int(raw)


def _mask_secret(secret: str) -> str:
    if not secret:
        return ""
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}...{secret[-4:]}"


_LLM_ENV_KEYS = {
    "LLM_PROVIDER",
    "LLM_API_PROTOCOL",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "LLM_MODEL",
    "LLM_TEMPERATURE",
    "LLM_TOP_P",
    "LLM_MAX_TOKENS",
    "LLM_TIMEOUT_SECONDS",
    "LLM_RETRY_COUNT",
    "ANTHROPIC_BASE_URL",
}
