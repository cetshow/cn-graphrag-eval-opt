import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.llm import (
    LLMConfig,
    LLMHTTPError,
    OpenAICompatibleChatClient,
    build_grounded_rag_messages,
)


class LLMRuntimeTest(unittest.TestCase):
    def test_openai_compatible_client_posts_mimo_chat_completion(self):
        calls = []

        def transport(url, headers, payload, timeout_seconds):
            calls.append((url, headers, payload, timeout_seconds))
            return 200, {
                "choices": [
                    {
                        "message": {"content": "安全部每月复核高危权限。"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
                "model": "mimo-v2.5-pro",
            }

        client = OpenAICompatibleChatClient(
            LLMConfig(
                provider="mimo",
                api_protocol="openai",
                base_url="https://token-plan-cn.xiaomimimo.com/v1",
                api_key="tp-test-secret",
                model="mimo-v2.5-pro",
                temperature=0.1,
                max_tokens=512,
            ),
            transport=transport,
        )

        response = client.chat([{"role": "user", "content": "谁复核高危权限？"}])

        self.assertEqual(response.content, "安全部每月复核高危权限。")
        self.assertEqual(response.usage["total_tokens"], 20)
        url, headers, payload, timeout_seconds = calls[0]
        self.assertEqual(url, "https://token-plan-cn.xiaomimimo.com/v1/chat/completions")
        self.assertEqual(headers["api-key"], "tp-test-secret")
        self.assertNotIn("Authorization", headers)
        self.assertEqual(payload["model"], "mimo-v2.5-pro")
        self.assertEqual(payload["max_completion_tokens"], 512)
        self.assertNotIn("max_tokens", payload)
        self.assertEqual(timeout_seconds, 60)

    def test_client_retries_transient_rate_limit_response(self):
        statuses = [429, 200]
        delays = []

        def transport(url, headers, payload, timeout_seconds):
            status = statuses.pop(0)
            if status == 429:
                return status, {"error": {"message": "rate limited"}}
            return status, {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}

        client = OpenAICompatibleChatClient(
            LLMConfig(
                provider="mimo",
                api_protocol="openai",
                base_url="https://token-plan-cn.xiaomimimo.com/v1",
                api_key="tp-test-secret",
                model="mimo-v2.5-pro",
                retry_count=1,
            ),
            transport=transport,
            sleeper=delays.append,
        )

        response = client.chat([{"role": "user", "content": "ping"}])

        self.assertEqual(response.content, "ok")
        self.assertEqual(delays, [1.0])

    def test_client_raises_clear_error_for_non_retryable_response(self):
        def transport(url, headers, payload, timeout_seconds):
            return 401, {"error": {"message": "invalid api key"}}

        client = OpenAICompatibleChatClient(
            LLMConfig(
                provider="mimo",
                api_protocol="openai",
                base_url="https://token-plan-cn.xiaomimimo.com/v1",
                api_key="bad",
                model="mimo-v2.5-pro",
            ),
            transport=transport,
        )

        with self.assertRaises(LLMHTTPError) as raised:
            client.chat([{"role": "user", "content": "ping"}])

        self.assertEqual(raised.exception.status_code, 401)
        self.assertIn("invalid api key", str(raised.exception))

    def test_grounded_rag_messages_include_question_contexts_and_citation_rules(self):
        messages = build_grounded_rag_messages(
            "哪个部门复核高危权限？",
            [
                {"chunk_id": "security:0001", "text": "安全部每月复核高危权限。"},
                {"chunk_id": "hr:0001", "text": "人力资源部负责入职材料。"},
            ],
        )

        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("只依据给定上下文", messages[0]["content"])
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("security:0001", messages[1]["content"])
        self.assertIn("哪个部门复核高危权限？", messages[1]["content"])
        self.assertIn("引用 chunk_id", messages[1]["content"])


if __name__ == "__main__":
    unittest.main()
