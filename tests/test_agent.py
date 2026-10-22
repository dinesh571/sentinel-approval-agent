import io
from pathlib import Path
import tempfile
import unittest

from agent import SentinelAgent
from action_planner import plan_action
from actions import ActionType


class SentinelAgentTests(unittest.TestCase):
    def run_agent(self, responses, workspace):
        values = iter(responses)
        output = io.StringIO()
        prompts = []

        def input_fn(prompt):
            prompts.append(prompt)
            return next(values)

        agent = SentinelAgent(
            workspace,
            input_fn=input_fn,
            output=output,
        )
        agent.run_task()
        return output.getvalue(), prompts

    def test_approved_request_shows_plan_and_executes(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            output, prompts = self.run_agent(
                ["write note.txt :: hello", "yes"], workspace
            )
            self.assertIn("Action plan", output)
            self.assertIn("Target filename: note.txt", output)
            self.assertEqual(
                prompts[1], "Do you approve this action? (yes/no): "
            )
            self.assertIn("Action succeeded:", output)
            self.assertEqual(
                (workspace / "note.txt").read_text(encoding="utf-8"), "hello"
            )

    def test_rejected_or_invalid_approval_performs_no_action(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            for response in ("no", "maybe", ""):
                with self.subTest(response=response):
                    output, _prompts = self.run_agent(
                        ["create note.txt", response], workspace
                    )
                    self.assertIn("Action rejected. No action was performed.", output)
                    self.assertFalse((workspace / "note.txt").exists())

    def test_unsupported_request_is_handled_without_crashing(self):
        with tempfile.TemporaryDirectory() as directory:
            output, _prompts = self.run_agent(["run something"], Path(directory))
            self.assertIn("Request not accepted:", output)

    def test_natural_language_create_request_writes_requested_text(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            output, _prompts = self.run_agent(
                [
                    "Create a file named test.txt containing Hello from SENTINEL.",
                    "yes",
                ],
                workspace,
            )
            self.assertIn("Action succeeded:", output)
            self.assertEqual(
                (workspace / "test.txt").read_text(encoding="utf-8"),
                "Hello from SENTINEL.",
            )

    def test_natural_language_requests_extract_filename_and_preserve_content(self):
        requests = (
            "Create a file named test.txt containing Hello from SENTINEL.",
            "Create a file named test.txt containing Hello from SENTINEL",
            "Create a file named notes.txt containing My first note.",
        )
        expected = (
            ("test.txt", "Hello from SENTINEL."),
            ("test.txt", "Hello from SENTINEL"),
            ("notes.txt", "My first note."),
        )
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            for request, (filename, text) in zip(requests, expected):
                with self.subTest(request=request):
                    plan = plan_action(request, workspace)
                    self.assertEqual(plan.action.filename, filename)
                    self.assertEqual(plan.action.text, text)

    def test_natural_language_create_without_contents_creates_empty_file(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = plan_action("Create a file named test.txt.", Path(directory))
            self.assertEqual(plan.action.action_type, ActionType.CREATE_FILE)
            self.assertEqual(plan.action.filename, "test.txt")


if __name__ == "__main__":
    unittest.main()
