"""Offline tests; constructed messages are fixtures, not live agent evidence."""
import os
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import normalobjects_langchain as lab


class ToolTests(unittest.TestCase):
    def test_keywords_and_multiple_records(self):
        result = lab.check_hawkins_records.invoke({"query": "PORTAL and flickering LIGHTS"})
        self.assertIn("HK-001", result)
        self.assertIn("HK-004", result)
        self.assertNotIn("HK-002", result)

    def test_unknown_and_word_boundaries(self):
        for query in ["refund for my toaster", "portalicious", "empowerment"]:
            self.assertIn("[NOT_FOUND]", lab.check_hawkins_records.invoke({"query": query}))

    def test_all_records(self):
        for topic, (record_id, sentence) in lab.RECORDS.items():
            result = lab.check_hawkins_records.invoke({"query": topic.upper()})
            self.assertIn(record_id, result)
            self.assertIn(sentence, result)

    def test_creativity_levels(self):
        for level, count in [("low", 1), ("medium", 2), ("high", 3)]:
            lines = lab.cast_interdimensional_spell.invoke({"problem": "lost socks", "creativity_level": level}).splitlines()
            self.assertEqual(len(lines), count)
            self.assertEqual(len(set(lines)), count)
            self.assertTrue(all("lost socks" in line and "[IMPROVISATION]" in line for line in lines))
        self.assertEqual(len(lab.cast_interdimensional_spell.invoke({"problem": "socks"}).splitlines()), 2)

    def test_invalid_creativity(self):
        for level in ["extreme", "", "HIGH"]:
            with self.assertRaises(ValueError):
                lab.cast_interdimensional_spell.invoke({"problem": "socks", "creativity_level": level})

    def test_random_seed_and_formats(self):
        random.seed(42)
        first = lab.consult_demogorgon.invoke({"complaint": "late parcel"})
        random.seed(42)
        self.assertEqual(first, lab.consult_demogorgon.invoke({"complaint": "late parcel"}))
        self.assertIn("[IMPROVISATION]", first)
        for query, person in [("portal", "Mike"), ("lights", "Dustin"), ("monster", "Lucas"), ("psychic", "Will")]:
            self.assertIn(person, lab.gather_party_wisdom.invoke({"question": query}))
        self.assertIn("Party huddle", lab.gather_party_wisdom.invoke({"question": "toaster"}))


class TraceTests(unittest.TestCase):
    def fixture(self):
        query = "portal"
        evidence = lab.check_hawkins_records.invoke({"query": query})
        return query, [HumanMessage(content=query),
                       AIMessage(content="", tool_calls=[{"name": "check_hawkins_records", "args": {"query": query}, "id": "call_fixture"}]),
                       ToolMessage(content=evidence, tool_call_id="call_fixture", name="check_hawkins_records"),
                       AIMessage(content=evidence)]

    def test_extraction_and_verification(self):
        query, messages = self.fixture()
        trace = lab.extract_trace(query, messages)
        self.assertEqual(trace["tool_calls"][0]["arguments"], {"query": "portal"})
        self.assertEqual(trace["tool_calls"][0]["id"], trace["tool_results"][0]["tool_call_id"])
        self.assertEqual(trace["tool_calls"][0]["results"][0]["content"], messages[2].content)
        checks = lab.verify_grounding(trace)
        self.assertTrue(checks["automated_checks_passed"])
        self.assertEqual(checks["answer_supported_by_tool_evidence"], "pending_human_review")

    def test_unsupported_id_and_missing_results(self):
        query, messages = self.fixture()
        messages[-1] = AIMessage(content="HK-999 says the portal is safe.")
        trace = lab.extract_trace(query, messages)
        checks = lab.verify_grounding(trace)
        self.assertFalse(checks["automated_checks_passed"])
        self.assertEqual(checks["unsupported_record_ids"], ["HK-999"])
        trace = lab.extract_trace(query, messages[:2])
        self.assertFalse(lab.verify_grounding(trace)["automated_checks"]["all_tool_results_captured"])
        self.assertIsNone(trace["final_response"])

    def test_irrelevant_tool(self):
        query, messages = self.fixture()
        trace = lab.extract_trace("psychic interference", messages)
        self.assertFalse(lab.verify_grounding(trace)["automated_checks"]["relevant_tool_called"])

    def test_partial_failure_saved(self):
        query, messages = self.fixture()
        class FailingAgent:
            def stream(self, *args, **kwargs):
                yield {"messages": messages[:3]}
                raise RuntimeError("sensitive error details")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeError):
                lab.run_query(FailingAgent(), query, Path(directory))
            text = next(Path(directory).glob("*.json")).read_text()
            self.assertIn('"status": "failed"', text)
            self.assertIn("call_fixture", text)
            self.assertNotIn("sensitive error details", text)

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(lab, "load_dotenv")
    @patch.object(lab, "ChatOpenAI")
    def test_missing_api_key(self, model, load_env):
        with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY is missing"):
            lab.build_agent()
        model.assert_not_called()


if __name__ == "__main__":
    unittest.main()
