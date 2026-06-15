#!/usr/bin/env python3
"""Measure the recurring per-call context: system prompt + tool schemas.

Read-only diagnostic. Builds the system prompt for a representative Telegram
coding session and the tool-definition JSON sent on every API call, then prints
a per-block token table and the combined total against the ~5,000-token budget.

Run before/after each lean-down phase to track progress and catch regressions:

    python scripts/measure_context.py
    python scripts/measure_context.py --toolset coding --model anthropic/claude-haiku-4.5

Token counts are estimates. If ``tiktoken`` is installed it is used; otherwise a
~4-chars-per-token heuristic is applied (clearly labelled in the output).

Note: the skills-index block reflects the skills installed under the active
HERMES_HOME at run time. On a machine with no installed skills the index is
near-empty — the header cost is still measured, but per-skill description cost
will be understated relative to a populated install.
"""

from __future__ import annotations

import argparse
import json
from types import SimpleNamespace


def _make_counter():
    """Return (count_fn, label) — tiktoken when available, else len//4."""
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return (lambda s: len(enc.encode(s or ""))), "tiktoken cl100k_base"
    except Exception:
        return (lambda s: len(s or "") // 4), "heuristic (chars/4)"


def _tool_schema_rows(toolset: str, count):
    """Per-tool schema token counts for the given toolset (sorted desc)."""
    from model_tools import get_tool_definitions

    defs = get_tool_definitions(enabled_toolsets=[toolset], quiet_mode=True)
    rows = []
    for d in defs:
        fn = d.get("function", d)
        name = fn.get("name", "?")
        rows.append((name, count(json.dumps(d))))
    rows.sort(key=lambda r: -r[1])
    return rows


def _make_agent(model: str, platform: str, toolset_tools):
    """A representative agent stub mirroring the attrs build_system_prompt reads."""
    return SimpleNamespace(
        load_soul_identity=False,
        skip_context_files=False,
        valid_tool_names=list(toolset_tools),
        _task_completion_guidance=True,
        _tool_use_enforcement="auto",
        _environment_probe=True,
        _memory_store=None,
        _memory_manager=None,
        _memory_enabled=False,
        _user_profile_enabled=False,
        model=model,
        provider=model.split("/")[0] if "/" in model else "",
        platform=platform,
        pass_session_id=False,
        session_id="",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--toolset", default="coding",
                    help="Toolset to measure (default: coding)")
    ap.add_argument("--model", default="anthropic/claude-haiku-4.5",
                    help="Model id (steers per-model guidance; default: a weak model)")
    ap.add_argument("--platform", default="telegram",
                    help="Platform hint (default: telegram)")
    ap.add_argument("--budget", type=int, default=5000,
                    help="Combined token budget to compare against (default: 5000)")
    args = ap.parse_args()

    count, counter_label = _make_counter()
    print(f"# Recurring context measurement  (counter: {counter_label})")
    print(f"# toolset={args.toolset}  model={args.model}  platform={args.platform}\n")

    # ── Tool schemas ────────────────────────────────────────────────────
    from toolsets import resolve_toolset
    from agent.system_prompt import build_system_prompt_parts

    rows = _tool_schema_rows(args.toolset, count)
    tool_total = sum(t for _, t in rows)
    print("## Tool schemas (JSON sent every call)")
    for name, tok in rows:
        print(f"  {name:18s} {tok:6d}")
    print(f"  {'TOTAL':18s} {tool_total:6d}\n")

    # ── System prompt ───────────────────────────────────────────────────
    # ``stable`` is framework overhead (identity + guidance + skills index) and
    # is what the budget targets. ``context`` (project AGENTS.md/etc.) and
    # ``volatile`` (memory/profile/timestamp) are user/session content that
    # varies per workspace — reported separately, not budgeted.
    tools = resolve_toolset(args.toolset)
    agent = _make_agent(args.model, args.platform, tools)
    parts = build_system_prompt_parts(agent)
    stable = count(parts["stable"])
    context = count(parts["context"])
    volatile = count(parts["volatile"])
    print("## System prompt")
    print(f"  {'stable (framework)':24s} {stable:6d}   <- budgeted")
    print(f"  {'context (project files)':24s} {context:6d}   (user content, not budgeted)")
    print(f"  {'volatile (memory/time)':24s} {volatile:6d}   (session content, not budgeted)\n")

    # ── Combined framework overhead ─────────────────────────────────────
    combined = tool_total + stable
    status = "OK" if combined <= args.budget else "OVER"
    print("## Framework overhead = tool schemas + stable system prompt")
    print(f"  tool schemas          {tool_total:6d}")
    print(f"  stable system prompt  {stable:6d}")
    print(f"  {'-'*24}")
    print(f"  COMBINED              {combined:6d}   budget {args.budget}  [{status}]")
    return 0 if combined <= args.budget else 1


if __name__ == "__main__":
    raise SystemExit(main())
