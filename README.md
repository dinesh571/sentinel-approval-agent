# SENTINEL

SENTINEL is a Python command-line Approval-in-the-Loop agent prototype. It
turns a small set of supported requests into a reviewable action plan and
executes an action only after the user explicitly approves it.

SENTINEL is deliberately limited: it does not call an external AI service,
execute shell commands, or make unrestricted changes to the computer.

## Features

- Supports creating an empty text file, writing supplied text to a new text
  file, and displaying text in the terminal.
- Shows the requested action, target, intended changes, and consequences
  before asking for approval.
- Requires the exact response `yes` (case-insensitive; surrounding whitespace
  is ignored). Other responses do not approve the action.
- Binds approval to the exact action and allows each approval to be used only
  once.
- Restricts file operations to `.txt` paths inside the configured workspace.
- Rejects absolute paths, traversal, reserved Windows device names, invalid
  path components, and paths that resolve outside the workspace.
- Refuses to overwrite an existing file and creates missing parent folders
  only inside the workspace.

## Requirements

- Windows
- Python 3.10 or newer

The application and tests use only the Python standard library; no third-party
packages need to be installed. `requirements.txt` is retained as a project
dependency note.

## Setup on Windows

Open PowerShell or Command Prompt in the project directory:

```powershell
cd "D:\My projects\Sentinel"
py -m venv senenv
.\senenv\Scripts\Activate.ps1
```

If PowerShell does not allow activation, run the interpreter directly instead:

```powershell
.\senenv\Scripts\python.exe main.py
```

From Command Prompt, activate the same environment with:

```cmd
senenv\Scripts\activate.bat
```

## Usage

Start the interactive agent:

```powershell
python main.py
```

At the request prompt, supported examples include:

```text
create notes.txt
write notes.txt :: My approved note.
Create a file named notes.txt containing My approved note.
display Hello from SENTINEL
```

For file actions, paths are relative to the `workspace` directory next to
`main.py`. Nested relative paths are supported. Review the plan and type `yes`
to approve it. Any other response rejects the action. For example,
`write notes.txt :: My approved note.` creates a new
`workspace\notes.txt` only after approval; it will not replace an existing
file.

## Security protections and limitations

- Approval is required before every supported action. Rejected or invalid
  requests do not execute.
- The executor accepts only SENTINEL-issued approvals matching the exact
  action, and prevents reusing an approval.
- File paths are normalized and checked against the resolved workspace to
  block traversal and symlink escapes where the operating system supports
  directory symlinks.
- Files are created in exclusive mode, so an existing file is never
  overwritten.
- The agent has no shell-command action and does not access an external AI
  service.

These protections limit the prototype's supported file operations; they are
not a substitute for operating-system permissions or a security review before
using the project with sensitive data.

## Tests

Run the automated test suite from the project directory:

```powershell
python -m unittest discover -s tests -v
```

Tests use temporary directories for file operations. The directory-symlink
escape test is skipped when the current Windows environment does not allow
creating directory symlinks.

## Project structure

```text
actions.py              Supported actions and filename validation
action_planner.py       Request parsing and reviewable action plans
approval.py             Action-bound approval decisions
action_executor.py      Approved, workspace-confined execution
agent.py                Interactive approval workflow
main.py                 Application entry point
tests/                  unittest coverage
workspace/.gitkeep      Keeps the generated workspace directory in Git
```
