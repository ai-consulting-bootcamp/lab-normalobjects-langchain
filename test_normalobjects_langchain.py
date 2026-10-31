"""Unit tests for normalobjects_langchain.py using standard unittest.

All tests in this module run completely offline without OPENAI_API_KEY, without
reading any real .env file, and without external network calls. Any message
histories or stub objects used to test `extract_trace`, `ToolUsageTracker`, and
`handle_complaint_with_agent` are explicitly marked as SYNTHETIC TEST DATA and
are NOT proof of a live LLM agent execution.
"""

import os
import unittest
from typing import Any, Dict, Optional
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from normalobjects_langchain import (
    SAMPLE_COMPLAINTS,
    ToolUsageTracker,
    build_complaint_agent,
    cast_interdimensional_spell,
    check_hawkins_records,
    consult_demogorgon,
    extract_trace,
    gather_party_wisdom,
    handle_complaint_with_agent,
    structured_handler,
)


class TestCreativeTools(unittest.TestCase):
    """Verify the 4 themed tools and their specifications."""

    def test_sample_complaints_preserved(self) -> None:
        """Ensure the exact 4 complaints from the lab notebook are present."""
        expected = [
            "My Christmas lights keep flickering and I hear noises from the wall. What is going on?",
            "There is a weird portal in my basement. What's the plan?",
            "A Demodog ate my homework. I need a creative solution, creativity level high!",
            "My neighbor's cat is acting weird. Is it from the Upside Down?",
        ]
        self.assertEqual(SAMPLE_COMPLAINTS, expected)

    def test_consult_demogorgon_embeds_complaint(self) -> None:
        """consult_demogorgon should return a non-empty string mentioning the complaint."""
        complaint_text = "mysterious slime on my bicycle"
        result = consult_demogorgon.invoke({"complaint": complaint_text})
        self.assertIsInstance(result, str)
        self.assertIn(complaint_text, result)

    def test_check_hawkins_records_case_insensitive_matches(self) -> None:
        """check_hawkins_records should match all 4 keys case-insensitively."""
        for key in ["portal", "monsters", "psychics", "electricity"]:
            upper_query = f"Tell me about {key.upper()} in Hawkins"
            result = check_hawkins_records.invoke({"query": upper_query})
            self.assertNotIn("not found", result.lower())
            self.assertTrue(len(result) > 20)

    def test_check_hawkins_records_fallback_not_found(self) -> None:
        """check_hawkins_records should return a 'not found' message when no key matches."""
        query = "My neighbor's cat is acting weird. Is it from the Upside Down?"
        result = check_hawkins_records.invoke({"query": query})
        self.assertIn("not found", result.lower())

    def test_cast_interdimensional_spell_creativity_levels(self) -> None:
        """cast_interdimensional_spell should return 1, 2, or 3 newline-joined spells."""
        problem = "floating homework"

        low_res = cast_interdimensional_spell.invoke(
            {"problem": problem, "creativity_level": "low"}
        )
        self.assertEqual(len(low_res.splitlines()), 1)
        self.assertIn(problem, low_res)

        med_res = cast_interdimensional_spell.invoke({"problem": problem})
        self.assertEqual(len(med_res.splitlines()), 2)
        for line in med_res.splitlines():
            self.assertIn(problem, line)

        high_res = cast_interdimensional_spell.invoke(
            {"problem": problem, "creativity_level": "HIGH"}
        )
        self.assertEqual(len(high_res.splitlines()), 3)
        for line in high_res.splitlines():
            self.assertIn(problem, line)

        fallback_res = cast_interdimensional_spell.invoke(
            {"problem": problem, "creativity_level": "ultra_chaotic_unknown"}
        )
        self.assertEqual(len(fallback_res.splitlines()), 2)

    def test_gather_party_wisdom_matches_and_huddle_fallback(self) -> None:
        """gather_party_wisdom should match party topics or return the 'huddle' fallback."""
        portal_res = gather_party_wisdom.invoke(
            {"question": "What do we do about the PORTAL?"}
        )
        self.assertIn("Mike", portal_res)

        monster_res = gather_party_wisdom.invoke(
            {"question": "How do we trap a monster?"}
        )
        self.assertIn("Dustin", monster_res)

        lights_res = gather_party_wisdom.invoke(
            {"question": "Why are the lights flickering?"}
        )
        self.assertIn("Will", lights_res)

        defense_res = gather_party_wisdom.invoke(
            {"question": "What is our best defense?"}
        )
        self.assertIn("Lucas", defense_res)

        fallback_res = gather_party_wisdom.invoke(
            {"question": "My neighbor's cat is acting weird."}
        )
        self.assertIn("huddle", fallback_res.lower())


class TestStructuredHandler(unittest.TestCase):
    """Verify the fixed-order structured workflow without LLM."""

    def test_structured_handler_fixed_order_and_low_creativity(self) -> None:
        """structured_handler must call records -> wisdom -> spell(low) in fixed order."""
        complaint = "There is a weird portal in my basement. What's the plan?"
        result = structured_handler(complaint)

        self.assertEqual(
            result["tool_sequence"],
            [
                "check_hawkins_records",
                "gather_party_wisdom",
                "cast_interdimensional_spell",
            ],
        )
        self.assertEqual(len(result["steps"]), 3)
        self.assertEqual(
            result["steps"][2]["args"],
            {"problem": complaint, "creativity_level": "low"},
        )
        # Spell step with creativity_level='low' selects 1 spell line randomly
        spell_output = result["steps"][2]["output"]
        self.assertEqual(len(spell_output.splitlines()), 1)
        self.assertIn(complaint, spell_output)


class TestSyntheticTraceExtraction(unittest.TestCase):
    """Verify trace extraction using SYNTHETIC TEST DATA (not live agent proof)."""

    def test_extract_trace_matches_tool_call_id_and_distinguishes_parallel_turns(
        self,
    ) -> None:
        """Verify tool_call_id matching, parallel-in-turn flag, and sequential turn count."""
        # SYNTHETIC TEST DATA for unit-testing extract_trace
        synthetic_messages = [
            HumanMessage(content="Synthetic test complaint about flickering lights"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "synthetic_tc_01",
                        "name": "check_hawkins_records",
                        "args": {"query": "electricity"},
                    },
                    {
                        "id": "synthetic_tc_02",
                        "name": "gather_party_wisdom",
                        "args": {"question": "lights"},
                    },
                ],
            ),
            # Intentionally place ToolMessages in reverse order to prove matching by tool_call_id
            ToolMessage(
                content="Synthetic wisdom output for tc_02",
                tool_call_id="synthetic_tc_02",
            ),
            ToolMessage(
                content="Synthetic record output for tc_01",
                tool_call_id="synthetic_tc_01",
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "synthetic_tc_03",
                        "name": "cast_interdimensional_spell",
                        "args": {
                            "problem": "flickering lights",
                            "creativity_level": "medium",
                        },
                    }
                ],
            ),
            ToolMessage(
                content="Synthetic spell output for tc_03",
                tool_call_id="synthetic_tc_03",
            ),
            AIMessage(
                content="Synthetic final answer grounded in synthetic tool outputs."
            ),
        ]

        tracker = ToolUsageTracker()
        trace = tracker.record_run(synthetic_messages)

        self.assertEqual(trace["total_tool_calls"], 3)
        self.assertEqual(trace["total_ai_tool_turns"], 2)

        # Verify exact matching by tool_call_id despite reversed ToolMessage order
        step_1 = trace["trace_steps"][0]
        step_2 = trace["trace_steps"][1]
        step_3 = trace["trace_steps"][2]

        self.assertEqual(step_1["tool_call_id"], "synthetic_tc_01")
        self.assertEqual(step_1["output"], "Synthetic record output for tc_01")
        self.assertTrue(step_1["is_parallel_call_in_turn"])
        self.assertEqual(step_1["ai_turn_index"], 1)

        self.assertEqual(step_2["tool_call_id"], "synthetic_tc_02")
        self.assertEqual(step_2["output"], "Synthetic wisdom output for tc_02")
        self.assertTrue(step_2["is_parallel_call_in_turn"])
        self.assertEqual(step_2["ai_turn_index"], 1)

        self.assertEqual(step_3["tool_call_id"], "synthetic_tc_03")
        self.assertEqual(step_3["output"], "Synthetic spell output for tc_03")
        self.assertFalse(step_3["is_parallel_call_in_turn"])
        self.assertEqual(step_3["ai_turn_index"], 2)

        summary = tracker.summary()
        self.assertEqual(summary["total_runs"], 1)
        self.assertEqual(summary["aggregate_tool_counts"]["check_hawkins_records"], 1)
        self.assertEqual(summary["aggregate_tool_counts"]["gather_party_wisdom"], 1)
        self.assertEqual(
            summary["aggregate_tool_counts"]["cast_interdimensional_spell"], 1
        )
        self.assertEqual(summary["aggregate_tool_counts"]["consult_demogorgon"], 0)

    def test_extract_trace_missing_tool_message_for_tool_call_id(self) -> None:
        """Verify fallback placeholder when a tool_call_id has no matching ToolMessage."""
        # SYNTHETIC TEST DATA for missing ToolMessage edge case
        synthetic_messages = [
            HumanMessage(content="Synthetic complaint with missing ToolMessage"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "unmatched_tc_99",
                        "name": "consult_demogorgon",
                        "args": {"complaint": "missing tool message test"},
                    }
                ],
            ),
            AIMessage(content="Synthetic fallback final answer."),
        ]

        trace = extract_trace(synthetic_messages)
        self.assertEqual(trace["total_tool_calls"], 1)
        self.assertEqual(
            trace["trace_steps"][0]["output"],
            "<ToolMessage not found for tool_call_id>",
        )


class TestErrorHandlingAndRecursionLimit(unittest.TestCase):
    """Verify recursion_limit config propagation and error handling (offline, synthetic stubs)."""

    def test_handle_complaint_passes_recursion_limit_to_agent_invoke(self) -> None:
        """handle_complaint_with_agent must pass config={'recursion_limit': ...} to invoke."""
        # SYNTHETIC STUB AGENT for offline unit testing
        class SyntheticStubAgent:
            def __init__(self) -> None:
                self.last_input: Optional[Dict[str, Any]] = None
                self.last_config: Optional[Dict[str, Any]] = None

            def invoke(
                self, input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None
            ) -> Dict[str, Any]:
                self.last_input = input_data
                self.last_config = config
                return {
                    "messages": [
                        HumanMessage(content="Synthetic complaint"),
                        AIMessage(content="Synthetic stub response."),
                    ]
                }

        stub_agent = SyntheticStubAgent()
        tracker = ToolUsageTracker()

        # Check default recursion_limit=10
        result_default = handle_complaint_with_agent(
            agent=stub_agent,
            complaint="Synthetic complaint",
            tracker=tracker,
        )
        self.assertEqual(stub_agent.last_config, {"recursion_limit": 10})
        self.assertEqual(result_default["final_answer"], "Synthetic stub response.")
        self.assertEqual(tracker.summary()["total_runs"], 1)

        # Check custom recursion_limit=6
        handle_complaint_with_agent(
            agent=stub_agent,
            complaint="Synthetic complaint",
            recursion_limit=6,
        )
        self.assertEqual(stub_agent.last_config, {"recursion_limit": 6})

    def test_handle_complaint_catches_recursion_and_runtime_errors(self) -> None:
        """handle_complaint_with_agent must catch exceptions and return a structured error dict."""
        # SYNTHETIC FAILING STUB AGENT for offline error-handling test
        class SyntheticFailingStubAgent:
            def invoke(
                self, input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None
            ) -> Dict[str, Any]:
                raise RuntimeError(
                    "Recursion limit of 10 reached without hitting a stop condition."
                )

        failing_agent = SyntheticFailingStubAgent()
        result = handle_complaint_with_agent(
            agent=failing_agent,
            complaint="Looping synthetic complaint",
            recursion_limit=10,
        )

        self.assertIn("error", result)
        self.assertIn("RuntimeError", result["error"])
        self.assertIn("Recursion limit of 10 reached", result["error"])
        self.assertEqual(result["chaining_pattern"], "error")
        self.assertEqual(result["total_tool_calls"], 0)
        self.assertEqual(result["final_answer"], "")

    @patch("dotenv.load_dotenv")
    def test_build_complaint_agent_raises_when_api_key_missing(
        self, mock_load_dotenv: Any
    ) -> None:
        """build_complaint_agent must raise RuntimeError when OPENAI_API_KEY is empty."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "   "}, clear=False):
            with self.assertRaises(RuntimeError) as ctx:
                build_complaint_agent()
            self.assertIn("OPENAI_API_KEY is not set", str(ctx.exception))
            mock_load_dotenv.assert_called_once()


if __name__ == "__main__":
    unittest.main()
