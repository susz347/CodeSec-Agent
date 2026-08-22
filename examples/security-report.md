# Security Report

Generated: 2026-08-22T10:28:20.608649Z

## Scan Sources

| Tool | Version | Ruleset | Target |
| --- | --- | --- | --- |
| semgrep | 1.163.0 | p/security-audit | example.py |
| bandit | 1.9.4 | bandit-default | example.py |
| npm-audit | 10.8.2 | npm-advisory-database | . |

## Summary

Total findings: 3

| Severity | Count |
| --- | ---: |
| error | 1 |
| warning | 2 |
| info | 0 |
| unknown | 0 |

## Findings

### [error] npm-audit/lodash

- Tool: npm-audit
- Location: package-lock.json:1
- ID: 943f24ac7b6c1630
- Message: Prototype Pollution
- Classification: confirmed

Metadata: `{"category": "dependency", "cwe": ["CWE-1321"], "npm_audit_severity": "high", "references": ["https://github.com/advisories/GHSA-test"]}`

- Cause: A dependency resolves to a version with a known advisory.
- Impact: The known vulnerability is exploitable through the affected component.
- Remediation: Upgrade to a patched version and re-run the dependency audit.
- References: CWE-1321, A06:2021 Vulnerable and Outdated Components

### [warning] B101

- Tool: bandit
- Location: example.py:1
- ID: f99a6989b62078a6
- Message: Use of assert detected.
- Classification: suspicious

```text
1 assert value

```

Metadata: `{"bandit_severity": "MEDIUM", "references": ["https://bandit.readthedocs.io/en/latest/plugins/b101_assert_used.html"]}`

- Cause: Security checks rely on assert statements.
- Impact: Asserts are stripped under optimization, disabling the check.
- Remediation: Replace assert with explicit validation that raises a real error.
- References: CWE-703, A09:2021 Security Logging and Monitoring Failures

### [warning] python.lang.security.audit.exec-used

- Tool: semgrep
- Location: example.py:3
- ID: b33371361cc71b7a
- Message: Avoid exec.
- Classification: confirmed

```text
exec(user_input)
```

Metadata: `{"cwe": ["CWE-78"], "owasp": ["A03:2021 - Injection"]}`

- Cause: User-controllable input reaches a process-execution call.
- Impact: Attackers may execute arbitrary operating-system commands.
- Remediation: Avoid exec/eval of untrusted input; use fixed argument lists without a shell.
- References: CWE-78, A03:2021 Injection
