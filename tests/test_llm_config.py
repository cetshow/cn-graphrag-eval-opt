import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.llm import LLMConfig, load_llm_config


class LLMConfigTest(unittest.TestCase):
    def test_load_llm_config_from_env_file(self):
        with TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "LLM_PROVIDER=mimo",
                        "LLM_API_PROTOCOL=openai",
                        "LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1",
                        "LLM_API_KEY=sk-test-secret",
                        "LLM_MODEL=mimo-v2.5-pro",
                        "LLM_TEMPERATURE=0.2",
                        "LLM_MAX_TOKENS=2048",
                        "LLM_TIMEOUT_SECONDS=45",
                        "LLM_AUTH_HEADER=api-key",
                        "ANTHROPIC_BASE_URL=https://token-plan-sgp.xiaomimimo.com/anthropic",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            config = load_llm_config(env_path)

            self.assertEqual(config.provider, "mimo")
            self.assertEqual(config.api_protocol, "openai")
            self.assertEqual(config.base_url, "https://token-plan-cn.xiaomimimo.com/v1")
            self.assertEqual(config.model, "mimo-v2.5-pro")
            self.assertEqual(config.temperature, 0.2)
            self.assertEqual(config.max_tokens, 2048)
            self.assertEqual(config.timeout_seconds, 45)
            self.assertEqual(config.auth_header, "api-key")
            self.assertTrue(config.is_openai_compatible)

    def test_llm_config_masks_secret_values(self):
        config = LLMConfig(
            provider="mimo",
            api_protocol="openai",
            base_url="https://token-plan-cn.xiaomimimo.com/v1",
            api_key="sk-1234567890abcdef",
            model="mimo-v2.5-pro",
        )

        safe = config.to_safe_dict()

        self.assertEqual(safe["api_key"], "sk-1...cdef")
        self.assertNotIn("1234567890", str(safe))

    def test_openai_client_payload_uses_configured_model_parameters(self):
        config = LLMConfig(
            provider="mimo",
            api_protocol="openai",
            base_url="https://token-plan-cn.xiaomimimo.com/v1",
            api_key="sk-test-secret",
            model="mimo-v2.5-pro",
            temperature=0.1,
            max_tokens=512,
        )

        payload = config.openai_chat_payload("回答问题", system_prompt="你是企业知识库助手")

        self.assertEqual(payload["model"], "mimo-v2.5-pro")
        self.assertEqual(payload["temperature"], 0.1)
        self.assertEqual(payload["max_completion_tokens"], 512)
        self.assertNotIn("max_tokens", payload)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][1]["content"], "回答问题")

    def test_env_example_loads_mimo_defaults(self):
        config = load_llm_config(".env.example")

        self.assertEqual(config.provider, "mimo")
        self.assertEqual(config.api_protocol, "openai")
        self.assertEqual(config.model, "mimo-v2.5-pro")
        self.assertEqual(config.max_tokens, 2048)

    def test_gitignore_excludes_local_env_file(self):
        gitignore = Path(".gitignore").read_text(encoding="utf-8").splitlines()

        self.assertIn(".env", gitignore)
        self.assertNotIn(".env.example", gitignore)


if __name__ == "__main__":
    unittest.main()
