#!/usr/bin/env python
"""PreToolUse hook: block Claude from reading .env files directly.

Reads the hook payload (JSON) from stdin and emits a `deny` permission
decision when the tool call would expose the contents of a real dotenv
file (.env, .env.local, .env.production, ...). Covers two vectors:

  * Read tool     -> inspects tool_input.file_path
  * Bash/PowerShell -> inspects tool_input.command for a content-reading
                       command (cat/type/grep/Get-Content/source/< redirect/
                       git show|diff, ...) aimed at a .env file.

Template files (.env.example / .sample / .template / .dist) are allowed so
Claude can still read the documented example config. Non-reading shell ops
that merely mention a .env file (rm/cp/mv/ls/echo >> .env) are allowed.
"""
import json
import os
import re
import sys

ALLOW = {".env.example", ".env.sample", ".env.template", ".env.dist"}

# Matches a dotenv *basename*: .env or .env.<suffix>, not preceded by an
# alnum/underscore/dot (so `foo.env` and `.environment` don't match) and not
# followed by an alnum char (so `.environment` doesn't match as `.env`).
ENV_TOKEN = re.compile(r"(?<![A-Za-z0-9_.])\.env(?:\.[A-Za-z0-9_-]+)?(?![A-Za-z0-9])")

# Content-reading commands (bash + PowerShell). Word-bounded, case-insensitive.
READER = re.compile(
    r"\b(?:cat|tac|nl|head|tail|less|more|most|strings|xxd|od|hexdump|base64|"
    r"grep|egrep|fgrep|rg|ag|awk|gawk|sed|cut|printf|dd|vi|vim|view|nano|bat|"
    r"type|gc|Get-Content|Select-String|sls)\b",
    re.IGNORECASE,
)
# `source .env` / `. .env`, a `< .env` redirect, or git show/diff/log/blame.
SOURCE = re.compile(r"(?:\bsource\b|(?:^|[;&|]|\bthen\b|\bdo\b)\s*\.)\s+\S*\.env", re.IGNORECASE)
REDIRECT = re.compile(r"<\s*['\"]?\S*\.env", re.IGNORECASE)
GIT_READ = re.compile(r"\bgit\s+(?:show|diff|log|blame|cat-file)\b", re.IGNORECASE)


def _deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def _real_env_tokens(text: str):
    return [t for t in ENV_TOKEN.findall(text) if t not in ALLOW]


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return  # malformed payload -> don't block

    tool_input = data.get("tool_input") or {}

    # --- Bash / PowerShell vector -------------------------------------------
    command = tool_input.get("command")
    if isinstance(command, str) and command:
        tokens = _real_env_tokens(command)
        if tokens and (
            READER.search(command)
            or SOURCE.search(command)
            or REDIRECT.search(command)
            or GIT_READ.search(command)
        ):
            _deny(
                f"Blocked: this command reads '{tokens[0]}'. .env files hold "
                "secrets and are off-limits to Claude. Use .env.example for "
                "reference."
            )
        return

    # --- Read tool vector ---------------------------------------------------
    file_path = str(tool_input.get("file_path") or "")
    name = os.path.basename(file_path.replace("\\", "/"))
    if (name == ".env" or name.startswith(".env.")) and name not in ALLOW:
        _deny(
            f"Reading '{name}' is blocked: .env files hold secrets and are "
            "off-limits to Claude. Use .env.example for reference."
        )


if __name__ == "__main__":
    main()
