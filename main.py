"""SENTINEL command-line application entry point."""

from pathlib import Path

from agent import SentinelAgent


def main() -> None:
    workspace = Path(__file__).resolve().parent / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    print("SENTINEL AI AGENT")
    print("Approval-in-the-Loop System")
    agent = SentinelAgent(workspace)

    while True:
        agent.run_task()
        try:
            response = input("Would you like to submit another task? (yes/no): ")
        except EOFError:
            print("\nExiting SENTINEL.")
            return
        if response.strip().casefold() != "yes":
            print("Exiting SENTINEL.")
            return


if __name__ == "__main__":
    main()
