"""shell_confirm.ConfirmPicker: the blocking spend-approval question.

The rule these tests exist to pin down is that every path which is not an explicit "yes"
denies. A guard that fails open would be worse than no guard, because the user would
believe they were being asked.
"""

from __future__ import annotations

import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import shell_confirm  # noqa: E402

DETAIL = {
    "title": "Generate a TTS vocal?",
    "body": "This calls cartesia with your saved API key.",
    "rows": [("Profile", "Lead Voice"), ("Text", "Hello from the studio")],
    "confirmLabel": "Generate",
}


class _Harness:
    """A ConfirmPicker plus the patches it pushed, with the session model's lock shape."""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.patches: list[dict] = []
        self.picker = shell_confirm.ConfirmPicker(self.lock, lambda **kw: self.patches.append(kw))

    def ask_in_thread(self, kind: str = "tts_spend", detail: dict | None = None) -> dict:
        """Start ask() on a worker and wait until the question is actually pending."""
        box: dict = {}
        box["thread"] = threading.Thread(
            target=lambda: box.__setitem__("result", self.picker.ask(kind, detail or DETAIL)),
            daemon=True,
        )
        box["thread"].start()
        deadline = time.time() + 2.0
        while self.picker.snapshot() is None and time.time() < deadline:
            time.sleep(0.005)
        box["view"] = self.picker.snapshot()
        return box

    def finish(self, box: dict) -> bool:
        box["thread"].join(timeout=2.0)
        assert not box["thread"].is_alive(), "ask() never returned -- the worker is stranded"
        return box["result"]


class ApprovalTests(unittest.TestCase):
    def test_approval_returns_true_and_clears_the_question(self) -> None:
        h = _Harness()
        box = h.ask_in_thread()
        self.assertIsNotNone(box["view"])
        self.assertEqual(h.picker.answer(box["view"]["id"], True), {"ok": True, "approved": True})
        self.assertTrue(h.finish(box))
        self.assertIsNone(h.picker.snapshot())

    def test_decline_returns_false(self) -> None:
        h = _Harness()
        box = h.ask_in_thread()
        h.picker.answer(box["view"]["id"], False)
        self.assertFalse(h.finish(box))

    def test_cancel_denies(self) -> None:
        # The X, Escape and the app closing all land here.
        h = _Harness()
        box = h.ask_in_thread()
        h.picker.cancel()
        self.assertFalse(h.finish(box))

    def test_the_view_carries_what_the_user_is_approving(self) -> None:
        h = _Harness()
        box = h.ask_in_thread()
        view = box["view"]
        self.assertEqual(view["title"], "Generate a TTS vocal?")
        self.assertEqual(view["confirmLabel"], "Generate")
        self.assertIn({"label": "Text", "value": "Hello from the studio"}, view["rows"])
        self.assertTrue(view["rememberLabel"])
        h.picker.cancel()
        h.finish(box)

    def test_question_is_pushed_and_then_withdrawn(self) -> None:
        h = _Harness()
        box = h.ask_in_thread()
        h.picker.answer(box["view"]["id"], True)
        h.finish(box)
        self.assertEqual([p.get("confirm") is not None for p in h.patches], [True, False])

    def test_quiet_cancel_pushes_nothing(self) -> None:
        # The window is being disposed; a patch into it would be a use-after-free.
        h = _Harness()
        box = h.ask_in_thread()
        h.patches.clear()
        h.picker.cancel(quiet=True)
        self.assertFalse(h.finish(box))
        self.assertEqual(h.patches, [])


class StaleAnswerTests(unittest.TestCase):
    def test_answer_to_a_closed_question_is_refused(self) -> None:
        h = _Harness()
        box = h.ask_in_thread()
        req_id = box["view"]["id"]
        h.picker.answer(req_id, True)
        h.finish(box)
        again = h.picker.answer(req_id, True)
        self.assertTrue(again["stale"])
        self.assertFalse(again["ok"])

    def test_answer_with_the_wrong_id_is_refused(self) -> None:
        h = _Harness()
        box = h.ask_in_thread()
        self.assertTrue(h.picker.answer(box["view"]["id"] + 99, True)["stale"])
        h.picker.cancel()
        h.finish(box)


class SessionSuppressionTests(unittest.TestCase):
    def test_remember_skips_the_next_question_of_the_same_kind(self) -> None:
        h = _Harness()
        box = h.ask_in_thread()
        h.picker.answer(box["view"]["id"], True, remember=True)
        self.assertTrue(h.finish(box))

        h.patches.clear()
        self.assertTrue(h.picker.ask("tts_spend", DETAIL))      # returns without blocking
        self.assertEqual(h.patches, [], "a suppressed question must not be pushed to the page")

    def test_remember_is_scoped_to_its_kind(self) -> None:
        h = _Harness()
        box = h.ask_in_thread("tts_spend")
        h.picker.answer(box["view"]["id"], True, remember=True)
        h.finish(box)

        other = h.ask_in_thread("something_else")
        self.assertIsNotNone(other["view"], "a different kind must still ask")
        h.picker.cancel()
        h.finish(other)

    def test_remember_on_a_decline_does_not_stick(self) -> None:
        # "No, and stop asking" would silently approve everything afterwards -- the
        # opposite of what the checkbox says. Declining never suppresses.
        h = _Harness()
        box = h.ask_in_thread()
        h.picker.answer(box["view"]["id"], False, remember=True)
        self.assertFalse(h.finish(box))
        self.assertFalse(h.picker.suppressed("tts_spend"))

    def test_suppression_can_be_cleared(self) -> None:
        h = _Harness()
        box = h.ask_in_thread()
        h.picker.answer(box["view"]["id"], True, remember=True)
        h.finish(box)
        self.assertTrue(h.picker.suppressed("tts_spend"))
        h.picker.clear_suppression()
        self.assertFalse(h.picker.suppressed("tts_spend"))


class SupersedeTests(unittest.TestCase):
    def test_a_second_question_denies_the_first_rather_than_stranding_it(self) -> None:
        h = _Harness()
        first = h.ask_in_thread()
        second = h.ask_in_thread()
        self.assertFalse(h.finish(first), "the superseded worker must be released, denied")
        h.picker.answer(second["view"]["id"], True)
        self.assertTrue(h.finish(second))


if __name__ == "__main__":
    unittest.main()
