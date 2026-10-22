import unittest

from actions import Action, ActionType
from approval import request_approval


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.action = Action(ActionType.DISPLAY_TEXT, text="hello")

    def test_only_explicit_yes_approves(self):
        self.assertTrue(request_approval(self.action, "yes").approved)
        for response in ("", "y", "YES please", "maybe", "no"):
            with self.subTest(response=response):
                self.assertFalse(request_approval(self.action, response).approved)

    def test_approval_is_bound_to_exact_action(self):
        decision = request_approval(self.action, "yes")
        different_action = Action(ActionType.DISPLAY_TEXT, text="different")
        self.assertTrue(decision.is_valid_for(self.action))
        self.assertFalse(decision.is_valid_for(different_action))


if __name__ == "__main__":
    unittest.main()
