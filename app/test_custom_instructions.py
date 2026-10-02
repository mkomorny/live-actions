"""Tests for Genius custom instructions (app/custom_instructions.py).

The behavioural rules these pin come from the feature's design, not from
general good practice, so they are worth stating plainly:

- Presets are a global, reusable library; which one is ACTIVE is bound per
  Live Set.
- Genius may only ever ADD an instruction, and only when the user asked it to.
  The single removal path is `replaces`, for a direct contradiction. There is
  no delete operation on the Genius-facing tool at all -- the schema test at
  the bottom is what keeps that true as the tool description evolves.

Run from app\\:  python -m unittest test_custom_instructions
"""

from __future__ import annotations

import unittest

import custom_instructions as ci


class SetKeyTests(unittest.TestCase):
    def test_extension_and_case_do_not_change_the_key(self) -> None:
        # Live reports the Set name with and without .als depending on whether
        # it has been saved; both must resolve to the same binding.
        self.assertEqual(ci.set_key("Neon Nights 128.als"), ci.set_key("neon nights 128"))

    def test_punctuation_is_normalised(self) -> None:
        self.assertEqual(ci.set_key("My Track (v2)"), "my-track-v2")

    def test_blank_falls_back_to_untitled(self) -> None:
        self.assertEqual(ci.set_key(""), "untitled")
        self.assertEqual(ci.set_key(None), "untitled")


class PresetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.s: dict = {}

    def test_create_and_list(self) -> None:
        p = ci.create_preset(self.s, "Concise", "Keep it short.")
        listed = ci.list_presets(self.s)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["name"], "Concise")
        self.assertTrue(p["id"].startswith("ci-"))

    def test_update_changes_name_and_body(self) -> None:
        p = ci.create_preset(self.s, "A", "one")
        ci.update_preset(self.s, p["id"], name="B", body="two")
        got = ci.get_preset(self.s, p["id"])
        self.assertEqual((got["name"], got["body"]), ("B", "two"))

    def test_update_unknown_preset_raises(self) -> None:
        with self.assertRaises(ValueError):
            ci.update_preset(self.s, "nope", name="x")

    def test_blank_name_becomes_untitled(self) -> None:
        p = ci.create_preset(self.s, "   ")
        self.assertEqual(p["name"], "Untitled")

    def test_body_is_capped(self) -> None:
        p = ci.create_preset(self.s, "big", "x" * (ci.MAX_BODY_CHARS + 500))
        self.assertEqual(len(p["body"]), ci.MAX_BODY_CHARS)

    def test_preset_limit_is_enforced(self) -> None:
        for i in range(ci.MAX_PRESETS):
            ci.create_preset(self.s, f"p{i}")
        with self.assertRaises(ValueError):
            ci.create_preset(self.s, "one too many")


class BindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.s: dict = {}
        self.p = ci.create_preset(self.s, "House rules", "Be brief.")

    def test_binding_is_per_set(self) -> None:
        ci.bind(self.s, "Song A", self.p["id"])
        self.assertEqual(ci.active_preset_id(self.s, "Song A"), self.p["id"])
        # A different Set is untouched -- that is the whole point of per-Set.
        self.assertEqual(ci.active_preset_id(self.s, "Song B"), "")

    def test_binding_survives_the_als_suffix(self) -> None:
        ci.bind(self.s, "Song A", self.p["id"])
        self.assertEqual(ci.active_preset_id(self.s, "Song A.als"), self.p["id"])

    def test_empty_id_unbinds(self) -> None:
        ci.bind(self.s, "Song A", self.p["id"])
        ci.bind(self.s, "Song A", "")
        self.assertEqual(ci.active_preset_id(self.s, "Song A"), "")

    def test_binding_to_a_missing_preset_raises(self) -> None:
        with self.assertRaises(ValueError):
            ci.bind(self.s, "Song A", "ci-nope")

    def test_deleting_a_preset_clears_bindings_that_pointed_at_it(self) -> None:
        ci.bind(self.s, "Song A", self.p["id"])
        self.assertTrue(ci.delete_preset(self.s, self.p["id"]))
        # Must not dangle: a Set pointing at a deleted preset reads as unbound.
        self.assertEqual(ci.active_preset_id(self.s, "Song A"), "")
        self.assertIsNone(ci.active_preset(self.s, "Song A"))

    def test_deleting_an_unknown_preset_reports_false(self) -> None:
        self.assertFalse(ci.delete_preset(self.s, "ci-nope"))


class PromptBlockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.s: dict = {}
        self.p = ci.create_preset(self.s, "Concise", "Keep replies under 120 words.\nLead with the action.")

    def test_no_binding_means_no_block(self) -> None:
        self.assertEqual(ci.prompt_block(self.s, "Song A"), "")

    def test_bound_preset_is_rendered_as_directives(self) -> None:
        ci.bind(self.s, "Song A", self.p["id"])
        block = ci.prompt_block(self.s, "Song A")
        self.assertIn("Concise", block)
        self.assertIn("- Keep replies under 120 words.", block)
        self.assertIn("- Lead with the action.", block)
        # Framed so the model treats them as instructions that outrank defaults.
        self.assertIn("outrank", block)

    def test_empty_body_produces_no_block(self) -> None:
        empty = ci.create_preset(self.s, "Blank", "   \n  \n")
        ci.bind(self.s, "Song B", empty["id"])
        self.assertEqual(ci.prompt_block(self.s, "Song B"), "")

    def test_only_the_bound_set_gets_the_block(self) -> None:
        ci.bind(self.s, "Song A", self.p["id"])
        self.assertEqual(ci.prompt_block(self.s, "Song B"), "")


class AddInstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.s: dict = {}

    def test_add_creates_and_binds_a_preset_when_none_exists(self) -> None:
        # "Remember that..." has to work on a fresh project without the user
        # first creating a preset by hand.
        res = ci.add_instruction(self.s, "Song A", "Always suggest a reference track.")
        self.assertTrue(res["added"])
        self.assertTrue(res["created_preset"])
        self.assertEqual(ci.active_preset_id(self.s, "Song A"), res["preset_id"])
        self.assertIn("reference track", ci.prompt_block(self.s, "Song A"))

    def test_add_appends_to_the_existing_preset(self) -> None:
        p = ci.create_preset(self.s, "Rules", "Be brief.")
        ci.bind(self.s, "Song A", p["id"])
        res = ci.add_instruction(self.s, "Song A", "Use metric time.")
        self.assertTrue(res["added"])
        self.assertFalse(res["created_preset"])
        self.assertEqual(res["total"], 2)
        lines = ci.instruction_lines(ci.get_preset(self.s, p["id"])["body"])
        self.assertEqual(lines, ["Be brief.", "Use metric time."])

    def test_add_never_drops_an_existing_line_without_replaces(self) -> None:
        p = ci.create_preset(self.s, "Rules", "Be brief.\nNo emoji.")
        ci.bind(self.s, "Song A", p["id"])
        ci.add_instruction(self.s, "Song A", "Cite the manual.")
        lines = ci.instruction_lines(ci.get_preset(self.s, p["id"])["body"])
        self.assertEqual(lines, ["Be brief.", "No emoji.", "Cite the manual."])

    def test_duplicate_is_reported_not_appended_twice(self) -> None:
        ci.add_instruction(self.s, "Song A", "Be brief.")
        res = ci.add_instruction(self.s, "Song A", "be brief.")
        self.assertFalse(res["added"])
        self.assertTrue(res["duplicate"])
        self.assertEqual(res["total"], 1)

    def test_replaces_removes_exactly_the_conflicting_line(self) -> None:
        p = ci.create_preset(self.s, "Rules", "Keep replies under 120 words.\nNo emoji.")
        ci.bind(self.s, "Song A", p["id"])
        res = ci.add_instruction(
            self.s, "Song A", "Keep replies under 300 words.",
            replaces="Keep replies under 120 words.",
        )
        self.assertTrue(res["added"])
        self.assertEqual(res["removed"], "Keep replies under 120 words.")
        lines = ci.instruction_lines(ci.get_preset(self.s, p["id"])["body"])
        # The unrelated instruction must survive.
        self.assertEqual(lines, ["No emoji.", "Keep replies under 300 words."])

    def test_replaces_matches_a_near_quote(self) -> None:
        p = ci.create_preset(self.s, "Rules", "Keep replies under 120 words.")
        ci.bind(self.s, "Song A", p["id"])
        res = ci.add_instruction(
            self.s, "Song A", "Go long when it helps.", replaces="under 120 words",
        )
        self.assertEqual(res["removed"], "Keep replies under 120 words.")

    def test_replaces_that_matches_nothing_still_adds_and_says_so(self) -> None:
        # The model must not be able to claim a replacement that did not happen.
        p = ci.create_preset(self.s, "Rules", "No emoji.")
        ci.bind(self.s, "Song A", p["id"])
        res = ci.add_instruction(
            self.s, "Song A", "Cite the manual.", replaces="something never written",
        )
        self.assertTrue(res["added"])
        self.assertIsNone(res["removed"])
        self.assertEqual(res["replaces_requested"], "something never written")
        self.assertEqual(
            ci.instruction_lines(ci.get_preset(self.s, p["id"])["body"]),
            ["No emoji.", "Cite the manual."],
        )

    def test_empty_text_raises(self) -> None:
        with self.assertRaises(ValueError):
            ci.add_instruction(self.s, "Song A", "   ")

    def test_whitespace_is_collapsed(self) -> None:
        res = ci.add_instruction(self.s, "Song A", "  keep   it \n short  ")
        self.assertEqual(res["text"], "keep it short")


class GeniusFacingSurfaceTests(unittest.TestCase):
    """The narrow-schema guarantee: Genius cannot delete instructions."""

    def test_tool_exposes_only_read_and_add(self) -> None:
        import genius_client

        tool = next(t for t in genius_client.LIVE_TOOLS if t["name"] == "live_custom_instructions")
        actions = tool["parameters"]["properties"]["action"]["enum"]
        self.assertEqual(sorted(actions), ["add", "read"])
        self.assertNotIn("delete", actions)

    def test_unknown_action_is_refused(self) -> None:
        import genius_client

        out = genius_client.handle_custom_instructions({"action": "delete"}, {})
        self.assertTrue(out.startswith("ERROR"))

    def test_read_with_nothing_bound_explains_how_to_set_one(self) -> None:
        import genius_client

        out = genius_client.handle_custom_instructions({"action": "read"}, {})
        self.assertIn("No custom instructions", out)


if __name__ == "__main__":
    unittest.main()
