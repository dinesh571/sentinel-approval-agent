"""Convert supported user requests into explicit, reviewable action plans."""

from dataclasses import dataclass
from pathlib import Path
import re

from actions import Action, ActionType, validate_action


@dataclass(frozen=True)
class ActionPlan:
    action: Action
    workspace: Path

    def render(self) -> str:
        action = self.action
        if action.action_type == ActionType.CREATE_FILE:
            action_name = "Create text file"
            changes = f"Create an empty file at {action.filename}."
            consequences = "A new file will be added; existing files will not be overwritten."
        elif action.action_type == ActionType.WRITE_FILE:
            action_name = "Write text to file"
            changes = f"Create {action.filename} containing the exact text shown below:\n{action.text!r}"
            consequences = (
                "A new file will be added. SENTINEL refuses to overwrite an existing file; "
                "missing parent directories may be created inside the workspace."
            )
        else:
            action_name = "Display text"
            changes = f"Display the following text in the terminal:\n{action.text!r}"
            consequences = "The text will be visible in this terminal session."

        target = action.filename if action.filename is not None else "Not applicable"
        return "\n".join(
            (
                "Action plan",
                f"Action type: {action_name}",
                f"Target filename: {target}",
                f"Target workspace: {self.workspace}",
                f"Intended changes: {changes}",
                f"Potential consequences: {consequences}",
            )
        )


def plan_action(request: str, workspace: Path) -> ActionPlan:
    if not isinstance(request, str):
        raise ValueError("The action request must be text.")

    request = request.strip()
    natural_file_request = re.fullmatch(
        r"create\s+(?:a\s+)?(?:text\s+)?file\s+named\s+"
        r"(?P<details>.+)",
        request,
        flags=re.IGNORECASE,
    )
    if natural_file_request:
        details = natural_file_request.group("details")
        content_separator = re.search(r"\s+containing\s+", details, re.IGNORECASE)
        if content_separator:
            filename = details[:content_separator.start()].strip()
            text = details[content_separator.end():]
        else:
            filename = details.strip()
            text = None
        if filename.endswith("."):
            filename = filename[:-1].rstrip()
        if text is None:
            action = Action(ActionType.CREATE_FILE, filename=filename)
        else:
            action = Action(
                ActionType.WRITE_FILE,
                filename=filename,
                text=text,
            )
        validate_action(action)
        return ActionPlan(action, workspace.resolve())

    command, separator, remainder = request.partition(" ")
    command = command.casefold()
    remainder = remainder.strip() if separator else ""

    if command == "create" and remainder:
        action = Action(ActionType.CREATE_FILE, filename=remainder)
    elif command == "write" and remainder:
        filename, delimiter, text = remainder.partition("::")
        if not delimiter:
            raise ValueError("Use: write <filename.txt> :: <text>")
        action = Action(
            ActionType.WRITE_FILE,
            filename=filename.strip(),
            text=text.lstrip(),
        )
    elif command == "display" and remainder:
        action = Action(ActionType.DISPLAY_TEXT, text=remainder)
    else:
        raise ValueError(
            "Unsupported request. Use 'create <filename.txt>', "
            "'write <filename.txt> :: <text>', or 'display <text>'."
        )

    validate_action(action)
    return ActionPlan(action, workspace.resolve())
