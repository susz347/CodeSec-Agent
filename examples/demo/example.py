"""Non-sensitive synthetic demo target.

This file deliberately contains code patterns that static analyzers flag, so it
can act as reproducible acceptance evidence for the scan -> analyze -> report
loop. It is a teaching fixture only: no real secret, no real vulnerability, and
no exploit instructions. Do not copy these patterns into production code.
"""

import os
import subprocess

# A placeholder credential that scanners flag as hardcoded. Not a real secret.
DEMO_PASSWORD = "demo-not-a-real-secret"


def run_unsafe_command(user_input):
    # exec() of untrusted input: flagged by Semgrep (exec-used) and Bandit (B102).
    exec(user_input)


def run_shell_command(user_input):
    # shell=True with a string command: flagged by Bandit (B602) and Semgrep.
    subprocess.call(user_input, shell=True)


def guarded_by_assert(value):
    # assert used for a security-relevant check: flagged by Bandit (B101).
    assert value is not None
    return value


def main():
    guarded_by_assert(os.getenv("PATH"))
    run_shell_command("echo demo")
    run_unsafe_command("print('demo')")


if __name__ == "__main__":
    main()
