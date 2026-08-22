"""Local CWE/OWASP knowledge subset used by the deterministic reviewer.

This module is the single source of truth for mapping normalized findings to a
curated vulnerability class plus defensive remediation guidance. It never calls
a model or reads source files.

``signature`` normalizes every tool's rule identifier into a small set of
"concept" strings so that free-form Semgrep rule IDs, opaque Bandit test IDs,
and dependency advisories all resolve against the same knowledge table.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuleKnowledge:
    cwe: str
    owasp: str
    title: str
    cause: str
    impact: str
    remediation: str


def _rule(
    cwe: str, owasp: str, title: str, cause: str, impact: str, remediation: str
) -> RuleKnowledge:
    return RuleKnowledge(cwe, owasp, title, cause, impact, remediation)


# Order matters: first keyword match wins.
_CONCEPT_KEYWORDS = (
    ("exec", "exec-used"),
    ("eval", "eval-used"),
    ("subprocess", "subprocess-shell"),
    ("shell", "subprocess-shell"),
    ("command-injection", "command-injection"),
    ("command_injection", "command-injection"),
    ("sql", "sql-injection"),
    ("hardcoded", "hardcoded-secret"),
    ("xss", "xss"),
    ("path-traversal", "path-traversal"),
    ("path_traversal", "path-traversal"),
    ("jwt", "jwt"),
    ("pickle", "deserialization"),
    ("yaml", "deserialization"),
    ("deserialize", "deserialization"),
    ("assert", "assert-used"),
)

# Bandit test IDs are opaque codes; map them to the same concepts.
_BANDIT_SIGNATURES = {
    "b102": "exec-used",
    "b602": "subprocess-shell",
    "b605": "subprocess-shell",
    "b608": "sql-injection",
    "b105": "hardcoded-secret",
    "b106": "hardcoded-secret",
    "b107": "hardcoded-secret",
    "b307": "eval-used",
    "b506": "deserialization",
    "b101": "assert-used",
    "b110": "assert-used",
}

# Concepts that force a "confirmed" classification when a code snippet is
# present and the path is not a test path.
HIGH_CONFIDENCE = (
    "exec-used",
    "eval-used",
    "subprocess-shell",
    "command-injection",
    "sql-injection",
    "hardcoded-secret",
    "deserialization",
)

_KNOWLEDGE: dict[str, RuleKnowledge] = {
    "exec-used": _rule(
        "CWE-78",
        "A03:2021 Injection",
        "OS command injection",
        "User-controllable input reaches a process-execution call.",
        "Attackers may execute arbitrary operating-system commands.",
        "Avoid exec/eval of untrusted input; use fixed argument lists without a shell.",
    ),
    "eval-used": _rule(
        "CWE-95",
        "A03:2021 Injection",
        "Eval injection",
        "Dynamic code is evaluated from an input-influenced expression.",
        "Arbitrary code execution within the application.",
        "Replace eval with a safe parser or explicit dispatch.",
    ),
    "subprocess-shell": _rule(
        "CWE-78",
        "A03:2021 Injection",
        "Command injection via shell",
        "A subprocess is started with shell interpretation enabled.",
        "Shell metacharacters in input can chain additional commands.",
        "Pass shell=False and a fixed argument list; validate inputs.",
    ),
    "command-injection": _rule(
        "CWE-77",
        "A03:2021 Injection",
        "Command injection",
        "Input is concatenated into a command string.",
        "Attackers can alter the executed command.",
        "Avoid string-built commands; use parameterized APIs.",
    ),
    "sql-injection": _rule(
        "CWE-89",
        "A03:2021 Injection",
        "SQL injection",
        "Query text is built by string concatenation with input.",
        "Attackers can read or modify the database.",
        "Use parameterized queries or an ORM with bound parameters.",
    ),
    "hardcoded-secret": _rule(
        "CWE-798",
        "A07:2021 Identification and Authentication Failures",
        "Hard-coded credential",
        "A password or secret is embedded in source code.",
        "The credential is exposed to anyone with repository access.",
        "Move secrets to a vault or environment variable and rotate the value.",
    ),
    "xss": _rule(
        "CWE-79",
        "A03:2021 Injection",
        "Cross-site scripting",
        "Untrusted data is rendered without output encoding.",
        "Script can execute in a victim's browser session.",
        "Encode output contextually and use a safe templating layer.",
    ),
    "path-traversal": _rule(
        "CWE-22",
        "A01:2021 Broken Access Control",
        "Path traversal",
        "A filesystem path is built from user input.",
        "Attackers can read or write files outside the intended root.",
        "Resolve and confine paths to an allow-listed root directory.",
    ),
    "jwt": _rule(
        "CWE-347",
        "A07:2021 Identification and Authentication Failures",
        "Improper signature verification",
        "A token is decoded or accepted without verifying its signature.",
        "Attackers can forge or tamper with tokens.",
        "Always verify signatures and algorithms before trusting claims.",
    ),
    "deserialization": _rule(
        "CWE-502",
        "A08:2021 Software and Data Integrity Failures",
        "Deserialization of untrusted data",
        "Untrusted data is deserialized into executable objects.",
        "Deserialization can trigger arbitrary code execution.",
        "Avoid deserializing untrusted data; use safe loaders or signed payloads.",
    ),
    "assert-used": _rule(
        "CWE-703",
        "A09:2021 Security Logging and Monitoring Failures",
        "Assert-based validation",
        "Security checks rely on assert statements.",
        "Asserts are stripped under optimization, disabling the check.",
        "Replace assert with explicit validation that raises a real error.",
    ),
}

_DEPENDENCY = _rule(
    "CWE-937",
    "A06:2021 Vulnerable and Outdated Components",
    "Vulnerable dependency",
    "A dependency resolves to a version with a known advisory.",
    "The known vulnerability is exploitable through the affected component.",
    "Upgrade to a patched version and re-run the dependency audit.",
)

_FALLBACK = _rule(
    "CWE-unknown",
    "—",
    "Security finding",
    "The scanner reported a security-relevant pattern.",
    "Potential security exposure depends on context and reachability.",
    "Review the finding and apply the scanner's remediation guidance.",
)


def signature(finding: dict[str, Any]) -> str:
    """Return a normalized concept string for a finding's rule identifier."""
    tool = str(finding.get("tool", "")).lower()
    rule_id = str(finding.get("rule_id", "")).lower()
    if tool == "npm-audit":
        return "dependency"
    if tool == "bandit":
        return _BANDIT_SIGNATURES.get(rule_id, rule_id)
    for keyword, concept in _CONCEPT_KEYWORDS:
        if keyword in rule_id:
            return concept
    return rule_id


def lookup(finding: dict[str, Any]) -> RuleKnowledge:
    """Return curated knowledge for a finding, with a safe fallback."""
    tool = str(finding.get("tool", "")).lower()
    if tool == "npm-audit":
        cwes = [
            value
            for value in (finding.get("metadata") or {}).get("cwe", [])
            if isinstance(value, str)
        ]
        cwe = cwes[0] if cwes else "CWE-937"
        return _rule(
            cwe,
            _DEPENDENCY.owasp,
            _DEPENDENCY.title,
            _DEPENDENCY.cause,
            _DEPENDENCY.impact,
            _DEPENDENCY.remediation,
        )
    return _KNOWLEDGE.get(signature(finding), _FALLBACK)
