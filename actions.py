"""Action definitions and validation shared by SENTINEL components."""

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import PurePosixPath, PureWindowsPath


class ActionType(str, Enum):
    CREATE_FILE = "create_file"
    WRITE_FILE = "write_file"
    DISPLAY_TEXT = "display_text"


@dataclass(frozen=True)
class Action:
    action_type: ActionType
    filename: str | None = None
    text: str = ""


def validate_filename(filename: str | None) -> str:
    """Validate a workspace-relative text-file path and return normalized slashes."""
    if not isinstance(filename, str) or not filename or "\0" in filename:
        raise ValueError("A valid relative filename is required.")

    normalized = filename.replace("\\", "/")
    windows_path = PureWindowsPath(filename)
    posix_path = PurePosixPath(normalized)
    if windows_path.is_absolute() or windows_path.drive or posix_path.is_absolute():
        raise ValueError("Absolute paths are not allowed.")

    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("Path traversal and empty path components are not allowed.")

    reserved_names = {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
    }
    for part in parts:
        if part.endswith((" ", ".")):
            raise ValueError("Path components cannot end with a space or period.")
        if any(ord(character) < 32 or character in '<>:"|?*' for character in part):
            raise ValueError("The filename contains characters that are not allowed.")
        if part.split(".", 1)[0].upper() in reserved_names:
            raise ValueError("The filename uses a reserved Windows device name.")

    if not normalized.lower().endswith(".txt"):
        raise ValueError("Only .txt files are supported.")
    return normalized


def validate_action(action: Action) -> None:
    if not isinstance(action, Action):
        raise ValueError("A supported action is required.")
    if action.action_type == ActionType.CREATE_FILE:
        validate_filename(action.filename)
        if action.text:
            raise ValueError("Create-file actions cannot include file contents.")
    elif action.action_type == ActionType.WRITE_FILE:
        validate_filename(action.filename)
        if not isinstance(action.text, str):
            raise ValueError("File contents must be text.")
    elif action.action_type == ActionType.DISPLAY_TEXT:
        if action.filename is not None or not isinstance(action.text, str):
            raise ValueError("Display actions must contain text and no filename.")
    else:
        raise ValueError("Unsupported action type.")


def action_fingerprint(action: Action) -> str:
    validate_action(action)
    serialized = json.dumps(
        [action.action_type.value, action.filename, action.text],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
