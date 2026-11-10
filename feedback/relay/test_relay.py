#!/usr/bin/env python3
"""离线检查：密封箱能解开，垃圾消息会被丢掉，Issue 不会重复开。"""

import base64
import json
import unittest

from nacl.public import PrivateKey, SealedBox

import kaneo_import
import relay


class RelayTest(unittest.TestCase):
    def setUp(self):
        self.secret = PrivateKey.generate()
        self.secret_b64 = base64.b64encode(bytes(self.secret)).decode()

    def seal(self, payload: dict) -> str:
        raw = SealedBox(self.secret.public_key).encrypt(json.dumps(payload).encode())
        return "v1." + base64.b64encode(raw).decode()

    def test_roundtrip_and_junk(self):
        secret = relay.load_secret(self.secret_b64)
        opened = relay.open_message(secret, self.seal({"v": 1, "category": "bug", "text": "翻页卡住"}))
        self.assertEqual(opened["text"], "翻页卡住")
        self.assertIsNone(relay.open_message(secret, "hello"))
        self.assertIsNone(relay.open_message(secret, "v1.not-base64"))
        self.assertIsNone(relay.open_message(secret, self.seal({"v": 1, "text": "  "})))
        self.assertEqual(relay.open_message(secret, self.seal({"v": 1, "category": "nope", "text": "x"}))["category"], "other")

    def test_issue_is_idempotent(self):
        data = {"v": 1, "category": "idea", "text": "想要夜间自动翻页", "contact": "", "platform": "ios", "os": "iOS 18", "app": "0.1.0 (1)", "sentAt": 1_700_000_000_000}
        title = relay.issue_title(data)
        body = relay.issue_body("abc123", data)
        self.assertTrue(title.startswith("[建议]"))
        self.assertEqual(relay.safe_id("ab c-->x"), "abc--x")
        self.assertNotIn(">", relay.safe_id("-->"))
        seen = relay.known_ids([
            {"body": body},
            {"body": "no marker"},
            {"body": body, "pull_request": {}},
        ])
        self.assertEqual(seen, {"abc123"})

    def test_kaneo_marker(self):
        text = kaneo_import.task_description("wtino/yuyue-feedback", 12, "<!-- ntfy-id: abc -->\n\n**类别**：问题\n\n正文")
        self.assertIn("yuyue-feedback-issue:12", text)
        self.assertNotIn("ntfy-id", text.split("\n", 1)[0])
        self.assertEqual(kaneo_import.MARKER_RE.findall(text), ["12"])
        self.assertEqual(kaneo_import.priority_for(text), "high")


if __name__ == "__main__":
    unittest.main()
