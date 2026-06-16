# Final Lean Pass — Codex/Claude-Code-Style Coding Agent

Follow-up to `2026-06-16-lean-down-remaining.md`. That session completed the
clean/bounded subsystems (terminal→local-only, dead `execute_code`/
`delegate_task` branches, optional-skills drop, OpenClaw + `website/` removal,
partial dep pruning, docs refresh). This plan covers (A) the three deferred
subsystems that are deeply coupled to the Telegram gateway / `cli.py` monolith,
(B) the rest of the dependency pruning, and (C) simple wins that push the agent
toward a Codex / Claude-Code shape: a small fixed tool core, terse prompts,
Telegram + CLI only, no feature sprawl.

**Goal posture (Codex / Claude Code):** one fixed ~15-tool core sent every call
(files + `terminal`/`process` + web research + skills + `memory` +
`session_search` + `todo` + `clarify`), a local execution backend, a single
default profile, an approval/permission model, and the learning loop. Anything
that doesn't serve "edit code on a local machine, talk over Telegram/CLU" is a
candidate for removal.

**Guardrails (unchanged):**
- One subsystem per commit; run `scripts/run_tests.sh` for the touched area and
  `python scripts/measure_context.py` (must hold ≤5,000) after each.
- Never break the Telegram gateway (`gateway/platforms/telegram*.py`,
  `gateway/run.py`, `gateway/session.py`, `gateway/delivery.py`) or the CLI.
- Keep the learning loop: `memory`, `session_search`, skills, and the curator.
- After each subsystem, the stale-name grep for that subsystem returns clean.

---

## Part A — Deferred subsystems (high coupling)

### A1. Multi-profile removal (largest)
Collapse to a single default profile. Keep the default-path resolution every
caller depends on; remove non-default profile support, the `hermes profile*`
commands, and the cross-profile write guard.
- `hermes_cli/profiles.py` (1,817 lines) → reduce to default-path helpers.
- Cross-profile guard in `agent/file_safety.py`
  (`_resolve_active_profile_name`, `classify_cross_profile_target`,
  `get_cross_profile_warning`) and callers in `tools/file_tools.py`
  (`_check_cross_profile_path`) and `tools/skill_manager_tool.py`.
- Profile consumers to simplify: `tools/session_search_tool.py`
  (`_resolve_profile_db`, `_locate_session_db`, the `profile` arg),
  `hermes_cli/{kanban*,backup,doctor,uninstall,service_manager,banner,
  profile_describer,profile_distribution,web_server}.py`, `cli.py`,
  `gateway/{run,slash_commands}.py`, `tools/skills_sync.py`,
  `agent/agent_init.py`.
- ~22 importing files. Go module-by-module, test between each. Keep
  `~/.hermes/profiles/default/...` path resolution working — many callers build
  paths through it even in single-profile mode.
- **Risk:** touches `cli.py` (638 KB). Land the `profiles.py` reduction +
  `file_safety` guard first (self-contained), then sweep consumers.
- **Then prune** `tests/hermes_cli/test_profiles.py` and the cross-profile
  guard tests, and drop `test_hermes_home_profile_warning.py` if it only
  asserts multi-profile behavior.

### A2. Cron / scheduled automations
- Remove `hermes_cli/cron.py`, the `/cron` slash command, the cron config
  block, and the gateway scheduler **ticker** (`_start_cron_ticker` in
  `gateway/run.py`, ~L15914/L16390). Remove the `croniter` core dep
  (`pyproject.toml` L64) and the empty `cron` extra (L135) + `[all]` ref.
- **Decouple the curator first.** The curator piggy-backs on the cron ticker
  (`gateway/run.py` ~L15978). The curator is part of the learning loop and must
  survive — give it its own lightweight interval thread (or fold it into an
  existing gateway background loop) before deleting the ticker.
- **Keep delivery routing of agent responses.** `gateway/delivery.py` routes
  both cron output *and* normal agent responses to Telegram. Only remove the
  cron-job-output paths (`get_hermes_home()/cron/output`, job-id plumbing);
  leave response routing intact.
- Trim `gateway/{config,session,session_context,platform_registry,mirror}.py`
  cron references (home-channel/`deliver=` wiring) and the `display.py` cron
  display branch (the `⏰ cron` lines).
- Prune `tests/hermes_cli/test_gateway_restart_loop.py` cron bits and any
  `tests/**/test_cron*` files.

### A3. Non-Telegram platform references (deep)
Adapters are already gone; references remain across the gateway. **Do not
remove `gateway/whatsapp_identity.py` outright** — its
`canonical_whatsapp_identifier` / `normalize_whatsapp_identifier` /
`expand_whatsapp_aliases` feed `gateway.session.build_session_key` for *general*
Telegram DM/group session keying. Options, in order of safety:
  1. Keep `whatsapp_identity.py` as-is (it's a stable identifier helper); just
     drop the `if platform == "whatsapp"` branches in `gateway/pairing.py` and
     `gateway/authz_mixin.py`, and rename the module's helpers to
     platform-neutral names (`canonical_identifier`, …) so the grep is clean
     without changing session-key behavior. **Verify session keys are
     byte-identical for Telegram IDs before/after.**
- Trim the remaining ~16 gateway files with discord/slack/whatsapp/signal/
  matrix/feishu/qqbot/teams/google_chat references
  (`gateway/{run,config,slash_commands,pairing,authz_mixin,hooks,
  display_config}.py`, `gateway/platforms/{base,helpers}.py`) — most are
  dead dispatch branches and platform-name lists/dicts.
- Prune those platforms from `gateway/platform_registry.py`.
- Delete the platform-specific CLI auth/setup commands and their wiring (see
  C3 below) — these are the user-facing half of the same cleanup.

---

## Part B — Finish dependency pruning (`pyproject.toml` + `tools/lazy_deps.py`)

Removed-tool / removed-platform extras that are now opt-in-but-unused. Prune the
extra, its `lazy_deps.py` key, and any `[all]`/install-hint reference; verify
nothing in `toolset_distributions.py` / `hermes_cli/nous_subscription.py` still
advertises them before deleting:
- **Removed tools:** `fal` (image_generate), `edge-tts` / `tts-premium` /
  `voice` / `mistral` STT-TTS, `honcho` (`memory.honcho`). The TTS/STT/image
  tools were trimmed in an earlier phase — confirm with a grep for the tool
  names, then drop the extras + lazy keys (`image.fal`, `tts.*`, `stt.*`,
  `memory.honcho`).
- **Non-Telegram platforms:** `slack`, `matrix`, `wecom`, `dingtalk`,
  `feishu`, `sms`, `homeassistant`, `nemo-relay` extras (do this with A3).
- **`croniter`** — remove with A2.
- Keep: `messaging` (telegram), `mcp`, `cli`, `pty`, `youtube`, `google`,
  `acp`, `bedrock`/`anthropic`/provider extras, `exa`/`firecrawl`/`parallel-web`
  (web research), `dev`.
- Re-run `tests/test_project_metadata.py` (the `lazy_covered_extras` contract)
  and `tests/test_packaging_metadata.py`; update their hard-coded lists.

---

## Part C — Simple Codex/Claude-Code-style wins (low risk, high signal)

### C1. Slim the config examples
- `.env.example` (23 KB) and `cli-config.yaml.example` (59 KB) still document
  every removed platform/backend/feature. Cut to the lean surface: provider/
  model, Telegram, local terminal, approvals, agent loop, web-research keys.
  These are docs-only — no runtime risk.

### C2. Drop README translations
- Remove `README.ur-pk.md` and `README.zh-CN.md` (and their badge links in
  `README.md`). They describe the full upstream product and will rot.

### C3. Remove platform/feature CLI commands not in the lean surface
Delete the command module + its `main.py` parser wiring + tests, one per
commit. Verify each isn't imported by a kept path first:
- Platform auth/setup: `hermes_cli/{slack_cli,dingtalk_auth,setup_whatsapp_cloud}.py`
  and `hermes_cli/voice.py` (TTS/STT removed).
- Project-management sprawl (not coding-core): `hermes_cli/{kanban,kanban_db,
  kanban_decompose,kanban_diagnostics,kanban_specify,kanban_swarm,blueprint_cmd,
  goals}.py` and their `"kanban"`/`"blueprint"`/`"goals"` subcommands. **Decide
  with owner** — these are agent-facing planning features; if any are wired into
  a kept skill, keep them. Default: drop (Codex/Claude Code have no kanban).
- Re-trim `_BUILTIN_SUBCOMMANDS` / the help text in `hermes_cli/main.py` after
  each removal.

### C4. Stale doc-pointer comments
- 8 `.py` files still carry `# See website/docs/...` comments pointing at the
  deleted docs site. Replace with a short inline note or drop the pointer.

### C5. optional-mcps audit
- `optional-mcps/{linear,n8n}` are integration catalogs, not core. Drop unless
  the MCP picker hard-depends on them (it shouldn't — MCP servers are
  user-configured). Confirm `hermes_cli/mcp_catalog.py` degrades to empty.

### C6. System-prompt / tool-schema final polish (the Codex/Claude-Code core)
- Re-run `python scripts/measure_context.py` and eyeball the per-tool schema
  table. Trim any remaining verbose tool descriptions toward Claude-Code
  terseness (the biggest are `skill_manage`, `terminal`, `session_search`,
  `patch`). Target: keep COMBINED comfortably under 5,000 with headroom.
- Confirm the default posture is the lean coding toolset (`agent/coding_context.py`)
  and that CLI + Telegram both resolve to `_HERMES_CORE_TOOLS`.

### C7. Pre-existing test debt surfaced this session (quick fixes)
- `tests/test_toolset_distributions.py` expects a removed `vision` toolset
  (fails on base). Update the expected-toolset list to the lean set
  (`web`, `terminal`, `file`).
- Sweep `tests/` for other orphans referencing removed toolsets/tools
  (`vision`, `browser_*`, `image_generate`, `text_to_speech`) and prune.

---

## Suggested order (each its own commit, test between)
1. C2, C4 (docs-only, trivial) → C1 (config examples) → C7 (test debt).
2. Part B dep pruning that's independent of A2/A3 (fal/honcho/TTS/image).
3. C3 platform auth commands (slack/dingtalk/whatsapp/voice) — pairs with A3.
4. A2 cron (decouple curator first) → remove `croniter`.
5. A3 platform references (rename whatsapp_identity helpers, drop branches) →
   remove non-Telegram platform extras.
6. C5 optional-mcps, C3 kanban/blueprint/goals (owner decision).
7. A1 multi-profile last — largest, touches `cli.py`; land `profiles.py` +
   `file_safety` first, then sweep the ~22 consumers.
8. C6 final prompt/schema polish + a full `scripts/run_tests.sh` pass.

## Verification (per subsystem)
1. `python -c "import <touched modules>"` — import cleanliness.
2. Targeted tests, then `scripts/run_tests.sh` for the area.
3. `python scripts/measure_context.py` — ≤5,000 holds.
4. Stale-name grep for that subsystem returns clean.
5. Smoke: `hermes --help`, gateway imports, a local terminal task.
