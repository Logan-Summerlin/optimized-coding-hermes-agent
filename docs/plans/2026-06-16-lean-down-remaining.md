# Lean-Down: Remaining Work (Phase 4 & 5)

Tracks the outstanding tasks for slimming this Hermes fork into a lean
coding agent with a Telegram gateway. Phases 0–3 (recurring-context trim to
~5k, system-prompt consolidation, tool-schema trim, developer-doc stale-ref
purge) and a safe-wins cleanup pass are already merged on branch
`claude/nice-lovelace-c1h97m` (PR #2).

**Guardrails for everything below**
- Do each subsystem in its own commit; run `scripts/run_tests.sh` and
  `python scripts/measure_context.py` after each.
- Never break the Telegram gateway (`gateway/platforms/telegram.py`,
  `telegram_network.py`) or the CLI.
- Keep the learning loop: `memory`, `session_search`, skills.
- After each subsystem, the stale-name grep for that subsystem should come
  back clean.

---

## Phase 4 — Subsystem teardown (remaining)

### 4.1 Multi-profile removal (largest)
Collapse to a single default profile. Keep the default-path resolution every
caller depends on; remove non-default profile support, the `hermes profile*`
management commands, and the cross-profile write guard.
- `hermes_cli/profiles.py` (1,817 lines) — reduce to default-path helpers.
- Cross-profile guard: `agent/file_safety.py`
  (`_resolve_active_profile_name`, `classify_cross_profile_target`,
  `get_cross_profile_warning`) and its callers in `tools/file_tools.py`
  (`_check_cross_profile_path`) and `tools/skill_manager_tool.py`. (The
  `cross_profile` tool-schema params and the per-call profile prompt hint are
  already removed.)
- Profile consumers to simplify: `tools/session_search_tool.py`
  (`_resolve_profile_db`, `_locate_session_db`, the `profile` arg),
  `hermes_cli/{kanban*,backup,doctor,uninstall,service_manager,banner,
  profile_describer,profile_distribution,web_server}.py`, `cli.py`,
  `gateway/{run,slash_commands}.py`, `tools/environments/docker.py`,
  `tools/skills_sync.py`, `agent/agent_init.py`.
- ~22 importing files total — go module-by-module, test between each.

### 4.2 Non-Telegram platforms (reference cleanup, adapters already gone)
Adapter files are already deleted; only references remain.
- Delete leftover `gateway/whatsapp_identity.py`.
- Remove discord/slack/whatsapp/signal/matrix/feishu/qqbot/teams/google_chat
  references in `gateway/{run,config,slash_commands,pairing,authz_mixin,hooks,
  display_config}.py` and `gateway/platforms/{base,helpers}.py`.
- Prune those platforms from `gateway/platform_registry.py` and from
  `toolsets.py` if any per-platform toolset aliases remain. (`PLATFORM_HINTS`
  already trimmed to telegram + cli.)

### 4.3 Cron / scheduled automations
- `hermes_cli/cron.py`, the `/cron` slash command, any cron config block, and
  the gateway delivery scheduler. Remove the `croniter` dependency.

### 4.4 Multi-backend terminals
- In `tools/environments/`: keep `base.py` + `local.py`; remove `docker.py`,
  `ssh.py`, `singularity.py`, `modal.py`, `managed_modal.py`, `daytona.py`,
  `modal_utils.py`, `file_sync.py`.
- Simplify `_REMOTE_TERMINAL_BACKENDS` (`agent/prompt_builder.py`) and the
  backend selection in `tools/terminal_tool.py`.

### 4.5 Web dashboard / Node / OpenClaw
- Remove `package.json`, `website/`, `hermes_cli/web_server.py`, and OpenClaw
  migration (`claw.py` / `hermes claw migrate`) if present.

### 4.6 Live dead-code branches for removed tools
Remove the `execute_code` / `delegate_task` branches (these tools can no longer
be invoked) and their helpers, testing after each file:
- `agent/{agent_runtime_helpers,tool_executor,context_compressor,
  iteration_budget,conversation_loop,background_review,memory_manager,
  tool_guardrails,display,agent_init}.py`
- `gateway/run.py` (27 refs), `tools/approval.py`, `hermes_cli/config.py`.

### 4.7 Dependency pruning
- After the above, prune now-unused extras in `pyproject.toml` and
  `tools/lazy_deps.py` (TTS, FAL, honcho, browser-use, croniter, cloud
  terminal SDKs, etc.).

### 4.8 optional-skills stale prose
- Many `optional-skills/*/SKILL.md` reference removed tools (`execute_code`,
  `browser_*`, `image_generate`, `text_to_speech`, `vision_analyze`). Decide:
  drop `optional-skills/` wholesale, or fix the prose to native tools. (Bundled
  `skills/` should be audited too.)

---

## Phase 5 — Docs refresh
- Rewrite `README.md` and the top of `AGENTS.md` to describe the lean agent:
  16 tools, Telegram + CLI only, learning loop retained. Remove feature rows
  for deleted subsystems (extra platforms, six terminal backends, cron,
  web dashboard, research/trajectory tooling).
- Update or remove `website/` docs if the site is kept.

---

## Verification (per subsystem)
1. `python -c "import <touched modules>"` — import cleanliness.
2. Targeted tests for the area, then `scripts/run_tests.sh`.
3. `python scripts/measure_context.py` — confirm the ~5k budget holds.
4. Stale-name grep for that subsystem returns clean.
5. Smoke test the Telegram gateway + CLI still start and run a task.
