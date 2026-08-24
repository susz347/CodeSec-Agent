"""Temporary non-sensitive probe for the gated DeepSeek CI validation.

This file deliberately contains a static-analysis pattern that must remain
unmerged. It is not imported or executed by the project; the validation PR is
closed and its branch deleted after collecting the CI evidence.
"""

import subprocess


def validate_gate_candidate(untrusted_input: str) -> None:
    """Deliberately trigger B602 and the Semgrep shell=True rule."""
    subprocess.run(untrusted_input, shell=True, check=False)
