"""User-facing SENTINEL task flow."""

from pathlib import Path
from typing import Callable, TextIO
import sys

from action_executor import ActionExecutor
from action_planner import plan_action
from approval import request_approval


class SentinelAgent:
    def __init__(
        self,
        workspace: Path,
        input_fn: Callable[[str], str] = input,
        output: TextIO | None = None,
    ):
        self.workspace = workspace.resolve()
        self.input_fn = input_fn
        self.output = output if output is not None else sys.stdout
        self.executor = ActionExecutor(self.workspace, self.output)

    def run_task(self) -> None:
        try:
            request = self.input_fn("Submit an action request: ")
            plan = plan_action(request, self.workspace)
        except ValueError as error:
            print(f"Request not accepted: {error}", file=self.output)
            return
        except EOFError:
            print("Input ended; no action was performed.", file=self.output)
            return

        print(plan.render(), file=self.output)
        try:
            response = self.input_fn("Do you approve this action? (yes/no): ")
        except EOFError:
            print("Input ended; no action was performed.", file=self.output)
            return

        decision = request_approval(plan.action, response)
        if not decision.approved:
            print("Action rejected. No action was performed.", file=self.output)
            return

        result = self.executor.execute(plan.action, decision)
        if result.success:
            print(f"Action succeeded: {result.message}", file=self.output)
        else:
            print(f"Action failed: {result.message}", file=self.output)
