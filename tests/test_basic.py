import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from promptrace import LLMLogger, load_entries, summarize, group_by_model, to_csv
from promptrace.pricing import estimate_cost


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.tmpdir.name) / "session.jsonl"
        self.logger = LLMLogger(self.log_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_log_direct(self):
        self.logger.log(
            model="claude-sonnet-5",
            prompt="Hello",
            response="Hi there!",
            prompt_tokens=5,
            completion_tokens=3,
            tags=["greeting"],
        )
        entries = load_entries(self.log_path)
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual(e.model, "claude-sonnet-5")
        self.assertEqual(e.total_tokens, 8)
        self.assertEqual(e.tags, ["greeting"])
        self.assertIsNotNone(e.cost_usd)
        self.assertEqual(e.prompt_text, "Hello")

    def test_track_context_manager(self):
        with self.logger.track(model="gpt-4o-mini", prompt="ping", tags=["test"]) as call:
            call.set_response("pong", prompt_tokens=1, completion_tokens=1)
        entries = load_entries(self.log_path)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].response_text, "pong")
        self.assertIsNotNone(entries[0].latency_ms)
        self.assertGreaterEqual(entries[0].latency_ms, 0)

    def test_redaction(self):
        logger = LLMLogger(self.log_path, store_text=False)
        logger.log(model="claude-sonnet-5", prompt="secret data", response="reply",
                   prompt_tokens=2, completion_tokens=2)
        entries = load_entries(self.log_path)
        e = entries[0]
        self.assertIsNone(e.prompt_text)
        self.assertIsNone(e.response_text)
        self.assertIsNotNone(e.prompt_hash)
        self.assertEqual(e.prompt_len, len("secret data"))

    def test_summarize_and_group(self):
        self.logger.log(model="claude-sonnet-5", prompt_tokens=100, completion_tokens=50)
        self.logger.log(model="claude-sonnet-5", prompt_tokens=200, completion_tokens=100)
        self.logger.log(model="gpt-4o-mini", prompt_tokens=10, completion_tokens=5)
        entries = load_entries(self.log_path)

        overall = summarize(entries)
        self.assertEqual(overall["calls"], 3)
        self.assertEqual(overall["total_tokens"], 465)

        by_model = group_by_model(entries)
        self.assertEqual(by_model["claude-sonnet-5"]["calls"], 2)
        self.assertEqual(by_model["gpt-4o-mini"]["calls"], 1)

    def test_csv_export(self):
        self.logger.log(model="claude-sonnet-5", prompt="a", response="b",
                         prompt_tokens=1, completion_tokens=1, tags=["x", "y"])
        entries = load_entries(self.log_path)
        out_csv = Path(self.tmpdir.name) / "out.csv"
        to_csv(entries, out_csv)
        content = out_csv.read_text(encoding="utf-8")
        self.assertIn("claude-sonnet-5", content)
        self.assertIn("x;y", content)

    def test_unknown_model_cost_is_none(self):
        cost = estimate_cost("some-unlisted-model", 100, 100)
        self.assertIsNone(cost)

    def test_malformed_lines_are_skipped(self):
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write("not valid json\n")
        self.logger.log(model="claude-sonnet-5", prompt_tokens=1, completion_tokens=1)
        entries = load_entries(self.log_path)
        self.assertEqual(len(entries), 1)


if __name__ == "__main__":
    unittest.main()
