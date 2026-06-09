from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable


DEFAULT_LLM_ENV_PATH = Path(".env")
PLACEHOLDER_API_KEY = "replace-with-your-dedicated-api-key"
DEFAULT_CONTEXT_MAX_CHARS = 12000


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
    context_max_chars: int = DEFAULT_CONTEXT_MAX_CHARS
    timeout_seconds: int = 60
    retry_count: int = 2
    auth_header: str = "api-key"
    anthropic_base_url: str = ""

    @property
    def is_openai_compatible(self) -> bool:
        return self.api_protocol == "openai"

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model and self.api_key != PLACEHOLDER_API_KEY)

    @property
    def chat_completions_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/chat/completions"

    def to_safe_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["api_key"] = _mask_secret(self.api_key)
        payload["configured"] = self.is_configured
        return payload

    def request_headers(self) -> dict[str, str]:
        if self.auth_header == "authorization":
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        return {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

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
            "max_completion_tokens": self.max_tokens,
        }


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    finish_reason: str = ""
    usage: dict[str, int | float] = field(default_factory=dict)
    raw: dict[str, object] = field(default_factory=dict)


class LLMError(RuntimeError):
    pass


class LLMConfigurationError(LLMError):
    pass


class LLMHTTPError(LLMError):
    def __init__(self, status_code: int, message: str, payload: dict[str, object] | None = None) -> None:
        super().__init__(f"LLM request failed with HTTP {status_code}: {message}")
        self.status_code = status_code
        self.payload = payload or {}


Transport = Callable[[str, dict[str, str], dict[str, object], int], tuple[int, dict[str, object]]]


class OpenAICompatibleChatClient:
    """Small MiMo/OpenAI-compatible chat-completions client with retry support."""

    def __init__(
        self,
        config: LLMConfig,
        *,
        transport: Transport | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.transport = transport or _urllib_transport
        self.sleeper = sleeper
        self._validate_config()

    def chat(self, messages: list[dict[str, str]]) -> LLMResponse:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_completion_tokens": self.config.max_tokens,
        }
        status_code, response = self._send_with_retries(payload)
        if not (200 <= status_code < 300):
            raise self._http_error(status_code, response)
        return _parse_chat_response(response, self.config.model)

    def dry_run_plan(self, prompt: str = "ping") -> dict[str, object]:
        return build_llm_request_plan(self.config, prompt)

    def _send_with_retries(self, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
        attempts = self.config.retry_count + 1
        for attempt in range(attempts):
            status_code, response = self.transport(
                self.config.chat_completions_url,
                self.config.request_headers(),
                payload,
                self.config.timeout_seconds,
            )
            if 200 <= status_code < 300:
                return status_code, response
            if status_code in _TRANSIENT_STATUS_CODES and attempt < attempts - 1:
                self.sleeper(float(2**attempt))
                continue
            return status_code, response
        raise LLMError("unreachable retry state")

    def _validate_config(self) -> None:
        if not self.config.is_openai_compatible:
            raise LLMConfigurationError("Only OpenAI-compatible LLM protocol is supported")
        if not self.config.base_url:
            raise LLMConfigurationError("LLM_BASE_URL is required")
        if not self.config.model:
            raise LLMConfigurationError("LLM_MODEL is required")
        if not self.config.api_key or self.config.api_key == PLACEHOLDER_API_KEY:
            raise LLMConfigurationError("LLM_API_KEY must be set to a real MiMo credential")
        if self.config.auth_header not in {"api-key", "authorization"}:
            raise LLMConfigurationError("LLM_AUTH_HEADER must be api-key or authorization")
        if self.config.context_max_chars <= 0:
            raise LLMConfigurationError("LLM_CONTEXT_MAX_CHARS must be positive")

    @staticmethod
    def _http_error(status_code: int, payload: dict[str, object]) -> LLMHTTPError:
        error = payload.get("error")
        if isinstance(error, dict):
            message = str(error.get("message", "unknown error"))
        else:
            message = str(payload.get("message", "unknown error"))
        return LLMHTTPError(status_code, message, payload)


def build_grounded_rag_messages(
    question: str,
    contexts: list[object],
    *,
    max_context_chars: int | None = None,
) -> list[dict[str, str]]:
    context_lines = _build_context_lines(
        contexts,
        max_context_chars=DEFAULT_CONTEXT_MAX_CHARS if max_context_chars is None else max_context_chars,
    )

    return [
        {
            "role": "system",
            "content": (
                "你是企业知识库问答助手。只依据给定上下文回答，不要编造。"
                "如果上下文不足，请明确说明。回答要简洁，并在关键结论后引用 chunk_id。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"问题：{question}\n\n"
                "上下文：\n"
                + "\n\n".join(context_lines)
                + "\n\n请用中文回答，并引用 chunk_id。"
            ),
        },
    ]


def build_llm_request_plan(config: LLMConfig, prompt: str = "ping") -> dict[str, object]:
    payload = config.openai_chat_payload(prompt)
    headers = config.request_headers()
    safe_headers = {
        key: ("***" if key.lower() in {"api-key", "authorization"} else value)
        for key, value in headers.items()
    }
    return {
        "provider": config.provider,
        "protocol": config.api_protocol,
        "endpoint": config.chat_completions_url,
        "model": config.model,
        "auth_header": config.auth_header,
        "headers": safe_headers,
        "payload": {
            "model": payload["model"],
            "message_count": len(payload["messages"]),
            "temperature": payload["temperature"],
            "top_p": payload["top_p"],
            "max_completion_tokens": payload["max_completion_tokens"],
        },
        "context": {
            "max_chars": config.context_max_chars,
        },
        "configured": config.is_configured,
    }


def generate_grounded_answer(
    *,
    client: OpenAICompatibleChatClient,
    question: str,
    contexts: list[object],
) -> LLMResponse:
    return client.chat(
        build_grounded_rag_messages(
            question,
            contexts,
            max_context_chars=client.config.context_max_chars,
        )
    )


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
        context_max_chars=_int_env(values, "LLM_CONTEXT_MAX_CHARS", DEFAULT_CONTEXT_MAX_CHARS),
        timeout_seconds=_int_env(values, "LLM_TIMEOUT_SECONDS", 60),
        retry_count=_int_env(values, "LLM_RETRY_COUNT", 2),
        auth_header=values.get("LLM_AUTH_HEADER", "api-key").strip().lower(),
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


def _build_context_lines(contexts: list[object], *, max_context_chars: int) -> list[str]:
    if max_context_chars <= 0:
        return ["[context truncated]"]

    context_lines = []
    used_chars = 0
    for index, context in enumerate(contexts, start=1):
        chunk_id = _context_value(context, "chunk_id", f"context:{index}")
        text = _context_value(context, "text", "")
        line = f"[{index}] chunk_id={chunk_id}\n{text}"
        separator_chars = 2 if context_lines else 0
        remaining_chars = max_context_chars - used_chars - separator_chars
        if remaining_chars <= 0:
            break
        if len(line) <= remaining_chars:
            context_lines.append(line)
            used_chars += separator_chars + len(line)
            continue
        context_lines.append(_truncate_context_line(chunk_id, index, text, remaining_chars))
        break
    return context_lines or ["[context truncated]"]


def _truncate_context_line(chunk_id: str, index: int, text: str, max_chars: int) -> str:
    header = f"[{index}] chunk_id={chunk_id}\n"
    marker = "\n[context truncated]"
    if max_chars <= len(header):
        return header[:max_chars]
    text_budget = max_chars - len(header)
    if text_budget <= len(marker):
        return header + marker[:text_budget]
    return header + text[: text_budget - len(marker)] + marker


def _urllib_transport(
    url: str,
    headers: dict[str, str],
    payload: dict[str, object],
    timeout_seconds: int,
) -> tuple[int, dict[str, object]]:
    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            body = response.read().decode("utf-8")
            return int(response.status), json.loads(body)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"message": body}
        return int(error.code), payload
    except urllib.error.URLError as error:
        return 599, {"error": {"message": str(error.reason)}}


def _parse_chat_response(payload: dict[str, object], fallback_model: str) -> LLMResponse:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LLMError("LLM response does not contain choices")
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise LLMError("LLM response choice is malformed")
    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise LLMError("LLM response choice does not contain a message")
    content = message.get("content")
    if not isinstance(content, str):
        raise LLMError("LLM response message content is missing")
    usage = payload.get("usage")
    return LLMResponse(
        content=content,
        model=str(payload.get("model") or fallback_model),
        finish_reason=str(first_choice.get("finish_reason") or ""),
        usage=usage if isinstance(usage, dict) else {},
        raw=payload,
    )


def _context_value(context: object, key: str, default: str) -> str:
    if isinstance(context, dict):
        return str(context.get(key, default))
    return str(getattr(context, key, default))


_TRANSIENT_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504, 599}


_LLM_ENV_KEYS = {
    "LLM_PROVIDER",
    "LLM_API_PROTOCOL",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "LLM_MODEL",
    "LLM_TEMPERATURE",
    "LLM_TOP_P",
    "LLM_MAX_TOKENS",
    "LLM_CONTEXT_MAX_CHARS",
    "LLM_TIMEOUT_SECONDS",
    "LLM_RETRY_COUNT",
    "LLM_AUTH_HEADER",
    "ANTHROPIC_BASE_URL",
}
