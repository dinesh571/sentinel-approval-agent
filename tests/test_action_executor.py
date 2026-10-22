import io
from pathlib import Path
import tempfile
import unittest

from action_executor import ActionExecutor
from actions import Action, ActionType
from approval import request_approval
from action_planner import plan_action


class ActionExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_directory.name) / "workspace"
        self.workspace.mkdir()
        self.output = io.StringIO()
        self.executor = ActionExecutor(self.workspace, self.output)

    def tearDown(self):
        self.temp_directory.cleanup()

    def approve(self, action):
        return request_approval(action, "yes")

    def test_approved_create_and_write_execute(self):
        create_action = Action(ActionType.CREATE_FILE, filename="new.txt")
        result = self.executor.execute(create_action, self.approve(create_action))
        self.assertTrue(result.success)
        self.assertEqual((self.workspace / "new.txt").read_text(encoding="utf-8"), "")

        write_action = Action(
            ActionType.WRITE_FILE, filename="nested/note.txt", text="safe text"
        )
        result = self.executor.execute(write_action, self.approve(write_action))
        self.assertTrue(result.success)
        self.assertEqual(
            (self.workspace / "nested" / "note.txt").read_text(encoding="utf-8"),
            "safe text",
        )

    def test_approved_display_executes(self):
        action = Action(ActionType.DISPLAY_TEXT, text="hello")
        result = self.executor.execute(action, self.approve(action))
        self.assertTrue(result.success)
        self.assertEqual(self.output.getvalue(), "hello\n")

    def test_rejected_and_missing_approval_do_not_execute(self):
        action = Action(ActionType.WRITE_FILE, filename="no.txt", text="no")
        rejected = request_approval(action, "no")
        self.assertFalse(self.executor.execute(action, rejected).success)
        self.assertFalse(self.executor.execute(action, None).success)
        self.assertFalse((self.workspace / "no.txt").exists())

    def test_approval_cannot_be_reused_or_applied_to_another_action(self):
        action = Action(ActionType.WRITE_FILE, filename="one.txt", text="one")
        different = Action(ActionType.WRITE_FILE, filename="two.txt", text="two")
        decision = self.approve(action)
        self.assertFalse(self.executor.execute(different, decision).success)
        self.assertTrue(self.executor.execute(action, decision).success)
        self.assertFalse(self.executor.execute(action, decision).success)

    def test_paths_outside_workspace_and_unsafe_names_are_rejected(self):
        for filename in (
            "..\\outside.txt",
            "../outside.txt",
            "C:\\outside.txt",
            "\\\\server\\share\\outside.txt",
            "folder/../../outside.txt",
        ):
            with self.subTest(filename=filename):
                with self.assertRaises(ValueError):
                    plan_action(f"create {filename}", self.workspace)
        self.assertEqual(list(self.workspace.iterdir()), [])

    def test_filename_validation_accepts_txt_case_insensitively(self):
        for filename in ("notes.txt", "NOTES.TXT", "nested/note.TxT"):
            with self.subTest(filename=filename):
                plan = plan_action(f"create {filename}", self.workspace)
                self.assertEqual(plan.action.filename, filename)

    def test_filename_validation_rejects_invalid_names_and_extensions(self):
        for filename in ("", "notes.md", "notes.txt.exe", "bad?.txt", "bad<name>.txt"):
            with self.subTest(filename=filename):
                with self.assertRaises(ValueError):
                    plan_action(f"create {filename}", self.workspace)

    def test_executor_rejects_an_invalid_action_without_crashing(self):
        action = Action(ActionType.CREATE_FILE, filename="../outside.txt")
        result = self.executor.execute(action, None)
        self.assertFalse(result.success)
        self.assertIn("approval is required", result.message)

    def test_symlink_escape_is_rejected_when_supported(self):
        outside = Path(self.temp_directory.name) / "outside"
        outside.mkdir()
        link = self.workspace / "link"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Directory symlinks are unavailable in this environment.")

        action = Action(ActionType.CREATE_FILE, filename="link/escape.txt")
        result = self.executor.execute(action, self.approve(action))
        self.assertFalse(result.success)
        self.assertFalse((outside / "escape.txt").exists())

    def test_existing_file_is_never_overwritten(self):
        existing = self.workspace / "existing.txt"
        existing.write_text("original", encoding="utf-8")
        action = Action(ActionType.WRITE_FILE, filename="existing.txt", text="replacement")
        result = self.executor.execute(action, self.approve(action))
        self.assertFalse(result.success)
        self.assertEqual(existing.read_text(encoding="utf-8"), "original")

    def test_filesystem_errors_are_returned_safely(self):
        obstacle = self.workspace / "obstacle"
        obstacle.write_text("file", encoding="utf-8")
        action = Action(
            ActionType.WRITE_FILE, filename="obstacle/child.txt", text="text"
        )
        result = self.executor.execute(action, self.approve(action))
        self.assertFalse(result.success)
        self.assertIn("Action failed safely:", result.message)


if __name__ == "__main__":
    unittest.main()
