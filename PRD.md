# Reqcon — Product Requirements Document

**Repo:** https://github.com/pn-le/Reqcon (MIT, currently empty scaffold)
**Owner:** Phillips Le
**Version:** 1.0 — July 17, 2026
**Audience:** This PRD is written for Claude Code to implement. Requirements use MUST / SHOULD / MAY. Build milestone by milestone; each has acceptance criteria.

---

## 1. Problem

Phillips runs a daily AI-driven internship scan that compiles a digest of SWE / AI-ML / biomedical internship and co-op postings. Every day, that scan burns most of its effort re-checking the same ~8–10 company job boards (Lila Sciences, BillionToOne, Anduril, Formlabs, Draper, MERL, STR, Ubicept, …) only to report "unchanged since last scan." Board re-checking is mechanical and deterministic; it doesn't need an AI. What the AI scan should spend effort on is discovery of new sources and judgment (eligibility, fit, dedup).

## 2. Solution

Reqcon (recon for job reqs) is a local Python CLI that snapshots a configured list of job boards once a day, diffs against the previous snapshot, and emits a change report: postings **added**, **removed**, and **changed**. The daily AI scan then reads Reqcon's output instead of re-fetching boards.

Design principle: **APIs before scraping, scraping only as a fallback.** Most tracked boards are hosted on Greenhouse or Workday, which expose JSON endpoints — no HTML parsing needed. Only boards with no structured endpoint fall back to HTML scraping via Scrapling.

## 3. Goals / Non-Goals

**Goals**

1. Detect new, removed, and changed postings on a configured set of boards within one daily run.
2. Zero false "new" postings across consecutive runs when nothing changed (stable posting identity).
3. Machine-readable output (JSON) for the AI scan + human-readable output (Markdown) for Phillips.
4. Adding a new board = editing one YAML entry, no code changes (for supported adapter types).
5. Run unattended on macOS via launchd, complete in under 2 minutes for 10 boards.

**Non-Goals (v1)**

- NO scraping of aggregators or auth-walled sites: LinkedIn, Indeed, Glassdoor, Handshake, ZipRecruiter. Out of scope permanently for ToS reasons.
- NO eligibility/fit judgment (undergrad vs PhD, tech-stack match). Reqcon reports raw changes; the AI scan judges. Light keyword *tagging* is in scope (§7.4), filtering is not.
- NO auto-apply, no notifications/email/Slack (MAY come later), no web UI, no database — flat files only.
- NO scholarship sites.

## 4. Tech Stack

- Python 3.10+ (developed against 3.12), packaged with `pyproject.toml`, installable as `pip install -e .`, entry point `reqcon`.
- Dependencies: `httpx` (HTTP + JSON adapters), `pyyaml` (config), `scrapling` (HTML fallback adapter ONLY — keep it an optional extra: `pip install reqcon[scrape]`).
- No pandas, no database. State is JSON on disk.
- `pytest` for tests. Type hints throughout; `dataclasses` or `pydantic` for models (implementer's choice — prefer stdlib dataclasses to keep deps small).

## 5. Repo Layout

```
Reqcon/
├── PRD.md                  # this file
├── README.md               # usage docs (write at Milestone 4)
├── pyproject.toml
├── boards.yaml             # tracked boards (checked in; see §6)
├── src/reqcon/
│   ├── __init__.py
│   ├── cli.py              # argparse CLI: scan, list, init
│   ├── models.py           # Posting, BoardResult, Diff dataclasses
│   ├── state.py            # snapshot load/save, atomic writes
│   ├── diff.py             # diff engine
│   ├── report.py           # markdown + json report writers
│   └── adapters/
│       ├── __init__.py     # adapter registry
│       ├── base.py         # Adapter protocol
│       ├── greenhouse.py
│       ├── workday.py
│       └── html_scrape.py  # Scrapling fallback
├── data/                   # gitignored: state snapshots
├── reports/                # gitignored: daily outputs
├── launchd/com.pnle.reqcon.plist
└── tests/
```

## 6. Configuration — `boards.yaml`

One entry per board. Schema:

```yaml
defaults:
  output_dir: ~/Desktop/Admin/reqcon      # reports land here (see §8)
  state_dir: ./data
  keywords_tag: [intern, co-op, coop, undergraduate, "co op"]

boards:
  - id: lila-sciences
    name: Lila Sciences
    adapter: greenhouse
    board_token: lilasciences            # boards-api.greenhouse.io token
  - id: billiontoone
    name: BillionToOne
    adapter: greenhouse
    board_token: billiontoone
  - id: anduril
    name: Anduril
    adapter: greenhouse
    board_token: andurilindustries
  - id: formlabs
    name: Formlabs
    adapter: greenhouse
    board_token: formlabs
  - id: draper
    name: Draper
    adapter: workday
    tenant: draper
    wd_host: draper.wd5.myworkdayjobs.com
    site: Draper_Careers
  - id: merl
    name: MERL (Mitsubishi Electric Research Labs)
    adapter: html
    url: https://www.merl.com/internship/openings
    item_selector: null                   # resolve at build time (§7.3)
  - id: str
    name: STR
    adapter: html
    url: https://str.us/internships/
    item_selector: null
  - id: ubicept
    name: Ubicept
    adapter: html
    url: https://www.ubicept.com/careers
    item_selector: null
```

> **Build-time task:** the `board_token`, Workday tenant/site values, and HTML selectors above are best guesses from posting URLs. VERIFY each one during Milestone 2/3 by hitting the endpoint and confirming non-empty results; correct any that 404. If a board can't be resolved, leave it in `boards.yaml` with `enabled: false` and a comment, and note it in the README.

## 7. Functional Requirements

### 7.1 Data model

`Posting` MUST have: `board_id`, `posting_id` (stable identity — see below), `title`, `url`, `location` (nullable), `raw_updated_at` (nullable, from API if present), `tags` (list, from keyword tagging).

**Posting identity** (critical for zero-false-positive diffing): use the source's native job ID when available (Greenhouse `id`, Workday `bulletFields`/req ID). For HTML boards, use the posting's absolute URL; if no per-posting URL exists, use `sha256(normalized_title + location)[:16]`. Normalization: strip whitespace, casefold. Identity MUST NOT include fields that churn (posted date, ordering).

### 7.2 Adapters

Common protocol: `fetch(board_config) -> list[Posting]`. Each adapter MUST raise `AdapterError` on failure (never return an empty list on error — an empty list means "board really has zero postings"; this distinction prevents a network blip from reporting every posting as removed).

- **greenhouse**: GET `https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs` (public, no auth). Map `jobs[].id`, `title`, `absolute_url`, `location.name`, `updated_at`.
- **workday**: POST `https://{wd_host}/wday/cxs/{tenant}/{site}/jobs` with JSON body `{"limit": 20, "offset": 0, "searchText": ""}`; paginate via `offset` until `total` reached. Map `jobPostings[].title`, `externalPath` (→ absolute URL), `locationsText`, `bulletFields[0]` as req ID. This is an unofficial endpoint — wrap it defensively and treat schema drift as `AdapterError`.
- **html** (Scrapling fallback): use `scrapling` StealthyFetcher to fetch the page and CSS selectors from config to extract postings. If `item_selector` is null, the adapter MUST fail with a clear "selector not configured" error. Import scrapling lazily so the base install works without it.

Politeness rules (all adapters): identify with a custom User-Agent `reqcon/{version} (personal job-board monitor)` on API endpoints; 10s timeout; max 1 fetch per board per run; no retries beyond 2 with backoff; boards run sequentially or with concurrency ≤ 4.

### 7.3 Diff engine

Given previous snapshot and current fetch for a board: `added` = IDs in current not in previous; `removed` = IDs in previous not in current; `changed` = same ID but different `title`, `url`, or `location`. First-ever run of a board MUST report postings as `baseline` (not `added`) so the first run doesn't spam 200 "new" postings. If a board's fetch raised `AdapterError`, its previous snapshot MUST be carried forward untouched and the board marked `error` in the report.

### 7.4 Keyword tagging

Tag (not filter) each posting: if title matches any `keywords_tag` term (case-insensitive), add tag `student-role`. Reports show tagged postings first. All postings still appear in JSON output.

### 7.5 State

`data/state.json`: one snapshot per board — `{board_id: {fetched_at, postings: [...]}}`. Writes MUST be atomic (write temp file, `os.replace`). Keep the last 7 daily snapshots in `data/history/` for debugging (prune older).

### 7.6 CLI

- `reqcon scan` — run all enabled boards, write reports, print a one-line summary per board. Exit 0 on success (even with zero changes), exit 1 if any board errored, exit 2 on config errors.
- `reqcon scan --board lila-sciences` — single board.
- `reqcon list` — table of configured boards, adapter, enabled, last fetch time, posting count.
- `reqcon init` — create data/report dirs, validate boards.yaml, dry-run each enabled board (fetch, report count, don't write state).

## 8. Output (contract with the AI scan)

Written to `output_dir` every run:

1. **`changes-latest.json`** (overwritten each run; the machine contract):
```json
{
  "run_at": "2026-07-17T07:00:12-04:00",
  "boards": [
    {"board_id": "lila-sciences", "status": "ok", "added": [Posting...], "removed": [Posting...], "changed": [...], "total_postings": 41},
    {"board_id": "merl", "status": "error", "error": "timeout"}
  ],
  "summary": {"added": 2, "removed": 1, "changed": 0, "boards_ok": 7, "boards_error": 1}
}
```
2. **`reqcon-YYYY-MM-DD.md`** — human digest: summary line, then per-board sections listing added (with links), removed, changed; `student-role`-tagged items bolded and listed first; errored boards flagged at top. If nothing changed anywhere: a single line "No changes across N boards." Keep last 14 days, prune older.

The daily AI internship scan will be updated (separately, not part of this repo) to read `changes-latest.json` instead of re-fetching these boards.

## 9. Scheduling

Provide `launchd/com.pnle.reqcon.plist` running `reqcon scan` weekdays at 07:00 America/New_York, plus README instructions (`launchctl load`). launchd, not cron, so missed runs fire on wake. Log stdout/stderr to `reports/reqcon.log` (append, no rotation needed in v1).

## 10. Testing

- Unit tests for: diff engine (added/removed/changed/baseline/error-carry-forward), posting identity normalization, state atomic write, keyword tagging, each adapter's response mapping using **fixture JSON/HTML files** checked into `tests/fixtures/` (no network in tests).
- One `--board`-level integration test marked `@pytest.mark.network`, skipped by default.
- Acceptance: `pytest` green, plus a manual double-run check — `reqcon scan` twice in a row MUST report zero changes on the second run.

## 11. Milestones

**M1 — Core skeleton.** Models, config loading, state, diff engine, report writers, CLI wiring with a stub adapter. Tests for diff + state. *Accept: `reqcon scan` with a fake board produces correct md/json; double-run shows no changes.*

**M2 — Greenhouse + Workday adapters.** Verify real tokens/tenants for the 5 API boards; fixture-based tests. *Accept: `reqcon init` dry-run fetches non-zero postings from ≥4 of the 5 API boards.*

**M3 — Scrapling HTML adapter.** Resolve selectors for MERL, STR, Ubicept; disable any board that can't be made reliable, with a comment. *Accept: each enabled HTML board returns stable posting IDs across two consecutive fetches.*

**M4 — Ship.** launchd plist, README (setup, adding a board, output contract), prune logic, `reqcon list`. *Accept: full `reqcon scan` completes < 2 min; second run reports "No changes"; README lets a stranger set it up.*

## 12. Risks & mitigations

- **Workday endpoint is unofficial** and may change shape → defensive parsing, `AdapterError` on drift, board keeps last good snapshot.
- **HTML boards redesign** → Scrapling's adaptive re-location helps, but if extraction yields 0 postings where previous snapshot had >0, treat as `AdapterError` (suspicious drop), not as "all removed". This rule applies to ALL adapters: a drop to zero from a nonzero snapshot requires two consecutive zero runs before postings are marked removed.
- **ToS/politeness** → API-first design, 1 fetch/board/day, no aggregators, custom UA. This is personal-use monitoring at trivial volume.

## 13. Future (explicitly not v1)

Push notification on `student-role` additions; more adapters (Lever, Ashby, SmartRecruiters); `reqcon add <url>` with auto-detection of the hosting platform; GitHub Actions runner instead of launchd.
