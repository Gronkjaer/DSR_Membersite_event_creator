import sys
import pathlib
import subprocess

# import pytest


def run_all_tests() -> None:
    """Use a shell/terminal to run pytest from the working directory."""

    # Get working directory.
    wdir = pathlib.Path(__file__).parent.parent

    # Run pytest from the working directory.
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v"],
        cwd=wdir,
        check=True,
        capture_output=True,
        text=True,
    )

    # Print any outputs.
    print(result.stdout)
    print(result.stderr)

    return None


if __name__ == "__main__":
    run_all_tests()
