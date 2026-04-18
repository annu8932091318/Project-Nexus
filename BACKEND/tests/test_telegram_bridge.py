import unittest

from src.bot.telegram_bridge import TelegramBotBridge


class _FakeService:
    def message(self, request):  # pragma: no cover - not used in these tests
        raise NotImplementedError


class TelegramBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge = TelegramBotBridge(token="test-token", service=_FakeService(), poll_timeout_seconds=5)

    def test_parse_message_returns_expected_payload(self) -> None:
        update = {
            "update_id": 10,
            "message": {
                "chat": {"id": 12345},
                "text": "hello",
            },
        }

        parsed = self.bridge._parse_message(update)

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.update_id, 10)
        self.assertEqual(parsed.chat_id, 12345)
        self.assertEqual(parsed.text, "hello")

    def test_parse_message_ignores_non_text_update(self) -> None:
        update = {
            "update_id": 12,
            "message": {
                "chat": {"id": 12345},
            },
        }
        self.assertIsNone(self.bridge._parse_message(update))

    def test_chunk_text_splits_large_output(self) -> None:
        text = "A" * 8000
        chunks = self.bridge._chunk_text(text, 3500)

        self.assertGreaterEqual(len(chunks), 3)
        self.assertTrue(all(len(chunk) <= 3500 for chunk in chunks))
        self.assertEqual("".join(chunks), text)

    def test_wants_files_detector(self) -> None:
        self.assertTrue(self.bridge._wants_files("send me files"))
        self.assertTrue(self.bridge._wants_files("please share artifacts"))
        self.assertFalse(self.bridge._wants_files("hello there"))


if __name__ == "__main__":
    unittest.main()
