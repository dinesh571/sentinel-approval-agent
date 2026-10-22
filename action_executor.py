"""Execute only supported actions with a valid, matching approval decision."""

from dataclasses import dataclass
from pathlib import Path
from typing import TextIO
import sys

from actions import Action, ActionType, validate_action, validate_filename
from approval import ApprovalDecision


@dataclass(frozen=True)
class ExecutionResult:
    success: bool
    message: str


class ActionExecutor:
    def __init__(self, workspace: Path, output: TextIO | None = None):
        self.workspace = workspace.resolve()
        self.output = output if output is not None else sys.stdout
        self._used_approvals: list[ApprovalDecision] = []

    def execute(
        self, action: Action, decision: ApprovalDecision | None
    ) -> ExecutionResult:
        if decision is None or not isinstance(decision, ApprovalDecision):
            return ExecutionResult(False, "Execution blocked: valid approval is required.")
        try:
            validate_action(action)
            matches_action = decision.is_valid_for(action)
        except (AttributeError, TypeError, ValueError):
            return ExecutionResult(False, "Execution blocked: the action is invalid.")
        if not matches_action:
            return ExecutionResult(
                False,
                "Execution blocked: approval is missing, invalid, or for a different action.",
            )
        if any(used is decision for used in self._used_approvals):
            return ExecutionResult(False, "Execution blocked: this approval was already used.")
        self._used_approvals.append(decision)

        try:
            if action.action_type == ActionType.DISPLAY_TEXT:
                print(action.text, file=self.output)
                return ExecutionResult(True, "Text displayed successfully.")

            target = self._target_path(action.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("x", encoding="utf-8", newline="") as file:
                if action.action_type == ActionType.WRITE_FILE:
                    file.write(action.text)
            verb = "created" if action.action_type == ActionType.CREATE_FILE else "written"
            return ExecutionResult(True, f"File {verb} successfully: {target}")
        except (OSError, UnicodeError, ValueError) as error:
            return ExecutionResult(False, f"Action failed safely: {error}")

    def _target_path(self, filename: str | None) -> Path:
        relative_name = validate_filename(filename)
        target = (self.workspace / relative_name).resolve()
        try:
            target.relative_to(self.workspace)
        except ValueError as error:
            raise ValueError("The target path escapes the designated workspace.") from error
        return target
