# Final Lean Pass — Low-Risk Hygiene Only

Follow-up to `2026-06-16-lean-down-remaining.md`. That plan assumed a full
teardown of every heavy subsystem. This session re-scoped it: **the part that
actually makes the agent "lean" — the recurring per-call context (system prompt
+ tool schemas) — is already won** (4,928 / 5,000 tokens, with the right ~15-tool
core). Everything left is *codebase hygiene*, not functional leanness. A cron
ticker that is never scheduled or a dashboard command nobody calls costs the
model zero tokens.

So this pass does **only the low-risk hygiene items** and **deliberately leaves
the deeply-coupled subsystems alone**. The valuable, battle-tested asset in this
fork is the **Telegram gateway**; the juice from ripping cron / multi-profile /
the dashboard out of the 638 KB `cli.py` monolith is not worth the risk of
breaking a working gateway.

**Decision rule for anything not on the DO list below:** leave it. Dead-but-
unreachable code is acceptable. Only revisit a coupled subsystem if it actively
costs you (a real bug, a real merge conflict, a real per-call token cost) —
i.e., when maintainability *genuinely* hurts, not on principle.

**Guardrails (unchanged):**
- One item per commit; run `scripts/run_tests.sh` for the touched area and
  `python scripts/measure_context.py` (must hold ≤5,000) after each.
- Never touch the Telegram gateway (`gateway/`) or the agent runtime in this
  pass. These items are docs/config/CLI-surface only.
- Keep the learning loop: `memory`, `session_search`, skills, curator.

---

## ✅ Already done — declare victory
- Recurring context is lean: ~15-tool core (files, `terminal`/`process`, web
  research, skills, `memory`, `session_search`, `todo`, `clarify`), terse
  system prompt, **4,928 / 5,000** per call.
- Local-only terminal backend; `execute_code` / `delegate_task` /image/TTS/
  browser tools gone from the live toolset.
- OpenClaw migration, `website/` docs site, and the `optional-skills/` catalog
  removed; model-catalog seed relocated to `assets/`.

No further tool-schema or system-prompt surgery is required. If
`measure_context.py` ever regresses above ~4,950, trim the largest tool
descriptions (`skill_manage`, `terminal`, `session_search`, `patch`) — but
that's maintenance, not a planned task.

---

## DO — low-risk hygiene (each its own commit)

### H1. Slim the config examples (docs-only, no runtime risk)
- `.env.example` (23 KB) and `cli-config.yaml.example` (59 KB) still document
  every removed platform/backend/feature. Cut to the lean surface: provider /
  model, Telegram, local terminal, approvals, agent loop, web-research keys.
- These files are read by humans, not at runtime — verify with a grep that no
  loader parses them as fixtures, then trim freely.

### H2. Drop README translations
- Remove `README.ur-pk.md` and `README.zh-CN.md` and their badge/links in
  `README.md`. They describe the full upstream product and will rot.

### H3. Remove dead platform / feature CLI commands
Delete the command module + its `hermes_cli/main.py` parser wiring + tests, one
per commit. **Only commands whose backing subsystem is already gone or never
used** — confirm each isn't imported by a kept path first:
- Platform auth/setup whose adapters are already deleted:
  `hermes_cli/{slack_cli,dingtalk_auth,setup_whatsapp_cloud}.py` and
  `hermes_cli/voice.py` (TTS/STT removed).
- After each, re-trim `_BUILTIN_SUBCOMMANDS` + the help text in `main.py`.
- **Do NOT** chase the deeper platform references inside `gateway/` — those are
  dead dispatch branches that cost nothing and live next to gateway code we are
  not touching this pass.

### H4. Stale doc-pointer comments
- ~8 `.py` files carry `# See website/docs/...` comments pointing at the
  deleted docs site. Replace with a short inline note or drop the pointer.
  Pure comment edits.

### H5. Pre-existing test debt (keep CI green)
- `tests/test_toolset_distributions.py` expects a removed `vision` toolset and
  fails on the base branch — update the expected list to the lean set
  (`web`, `terminal`, `file`).
- Sweep `tests/` for other orphans referencing removed toolsets/tools
  (`vision`, `browser_*`, `image_generate`, `text_to_speech`) and prune.

### H6. Independent dependency pruning (only the safe extras)
Prune extras whose tools are already gone and that **no kept code imports** —
verify with a grep + the `tests/test_project_metadata.py` contract, update its
hard-coded lists, and stop there:
- `fal` (image_generate), TTS/STT extras, `honcho` (`memory.honcho`) if unused.
- Leave `croniter` and the non-Telegram platform extras in place — removing
  them means touching the coupled cron / platform subsystems we are skipping.

---

## DON'T — leave these alone (coupled to the gateway / `cli.py`)
These are out of scope for the lean *agent* and only matter for codebase purity.
Skipping them is the explicit decision of this pass.
- **Multi-profile collapse** — ~22 files, including the 638 KB `cli.py` and the
  `file_safety` cross-profile guard. High blast radius, zero token cost.
- **Cron teardown** — the ticker is woven into `gateway/run.py` and the curator
  (learning loop) piggy-backs on it; `delivery.py` routes agent responses
  through the same paths. Touching it risks the gateway.
- **Web dashboard backend** — `web_server.py` (11.9 KB lines) is woven into
  core `config.py` / `plugins.py`. (Artifacts + docs already removed.)
- **Deep non-Telegram platform references in `gateway/`** — dead branches that
  cost nothing; not worth editing gateway files.

If one of these ever causes a real bug or a real upstream merge conflict, lift
it out *then* — not preemptively.

---

## Verification (per item)
1. `python -c "import <touched modules>"` — import cleanliness.
2. Targeted tests, then `scripts/run_tests.sh` for the area.
3. `python scripts/measure_context.py` — ≤5,000 holds (should be unchanged;
   none of these items touch the prompt or schemas).
4. Smoke: `hermes --help` still builds its parser; gateway imports unchanged.
