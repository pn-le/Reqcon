# Reqcon — Product Requirements Document

**Repo:** https://github.com/pn-le/Reqcon (MIT, currently empty scaffold)
**Owner:** Phillips Le
**Version:** 1.1 — July 17, 2026 (v1.1: GitHub Actions is the primary runner; self-updating README added)
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
5. Run unattended, daily, with no machine of Phillips's involved: a scheduled GitHub Actions workflow in this repo runs the scan, commits updated state, and pushes. Complete in under 2 minutes for 10 boards.
6. The repo README is a live dashboard: each run rewrites a marked section of `README.md` with the newest listings, so visiting the repo (or its GitHub page on a phone) shows current postings without running anything.

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
├── README.md               # intro/setup docs + auto-updated listings section (§8.3)
├── pyproject.toml
├── boards.yaml             # tracked boards (checked in; see §6)
├── .github/workflows/scan.yml   # daily scheduled runner (§9)
├── src/reqcon/
│   ├── __init__.py
│   ├── cli.py              # argparse CLI: scan, list, init
│   ├── models.py           # Posting, BoardResult, Diff dataclasses
│   ├── state.py            # snapshot load/save, atomic writes
│   ├── diff.py             # diff engine
│   ├── report.py           # markdown + json report writers
│   ├── readme.py           # README marker-section updater (§8.3)
│   └── adapters/
│       ├── __init__.py     # adapter registry
│       ├── base.py         # Adapter protocol
│       ├── greenhouse.py
│       ├── workday.py
│       └── html_scrape.py  # Scrapling fallback
├── data/                   # COMMITTED: state snapshots (runners are ephemeral, state must live in git)
├── reports/                # COMMITTED: changes-latest.json + last 14 daily digests
└── tests/
```

> Note: `data/` and `reports/` are checked in, not gitignored — GitHub Actions runners are ephemeral, so the previous snapshot must be read from, and written back to, the repo itself. Every scheduled run that changes anything produces one commit.

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

- `reqcon scan` — run all enabled boards, write reports, print a one-line summary per board. Exit 0 on success (even with zero changes), exit 1 if any board errored, exit 2 on config errors. In CI, adapter errors on individual boards MUST NOT fail the job (the commit step still runs with the boards that succeeded) — exit 1 is reserved for reporting, and the workflow treats it as success via `continue-on-error` on that step or by having `scan` return 0 when `--ci` is passed with partial failures.
- `reqcon scan --update-readme` — additionally rewrite the README marker section (§8.3).
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

The daily AI internship scan will be updated (separately, not part of this repo) to read `changes-latest.json` from the repo's raw URL (`https://raw.githubusercontent.com/pn-le/Reqcon/main/reports/changes-latest.json`) instead of re-fetching these boards.

### 8.3 Self-updating README

`README.md` has a hand-written top (what Reqcon is, setup, how to add a board) and an auto-generated section delimited by HTML comment markers:

```
<!-- REQCON:START -->
... generated content, everything between markers is owned by the tool ...
<!-- REQCON:END -->
```

`readme.py` MUST replace only the content between markers, never touch anything outside them, and fail loudly if the markers are missing. Generated content:

1. A status line: `Last scan: 2026-07-17 07:04 ET · 8 boards · 2 new · 1 removed` plus a per-board ✅/⚠️ status row.
2. **New this week** — postings first seen in the last 7 days, newest first, as a Markdown table: Company | Role (linked) | Location | First seen. `student-role`-tagged rows listed first with a 🎓 prefix. Cap at 30 rows; if over cap, add "…and N more" linking to the latest daily digest.
3. **All tracked postings** — inside a collapsed `<details>` block, the full current posting list per board (title linked, location). Cap 400 rows total.

"First seen" requires persisting a `first_seen` date per posting ID in state — add it at snapshot-write time; baseline postings get the baseline run's date. Rendering MUST be deterministic (stable sort: first_seen desc, then board_id, then title) so re-running with no changes produces a byte-identical README and therefore no commit.

## 9. Scheduling — GitHub Actions (primary runner)

`.github/workflows/scan.yml`:

```yaml
name: daily-scan
on:
  schedule:
    - cron: "0 11 * * 1-5"    # ~7:00 AM ET during EDT (11:00 UTC); 6:00 AM ET in winter — acceptable
  workflow_dispatch: {}        # manual "Run workflow" button for testing
permissions:
  contents: write
concurrency:
  group: reqcon-scan
  cancel-in-progress: false
jobs:
  scan:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e .[scrape]
      - run: reqcon scan --update-readme
      - name: Commit if changed
        run: |
          git config user.name "reqcon-bot"
          git config user.email "actions@users.noreply.github.com"
          git add data reports README.md
          git diff --cached --quiet || git commit -m "scan: $(date -u +%F) [skip ci]" && git push
```

Requirements & caveats the implementation MUST respect:

- The built-in `GITHUB_TOKEN` with `permissions: contents: write` is sufficient — no PAT, no secrets to manage.
- **Commit only when something changed.** Deterministic outputs (§8.3) + the `git diff --cached --quiet` guard mean a no-change day produces no commit and the history stays meaningful.
- **Actions cron is best-effort**: runs can start minutes to ~an hour late, occasionally be skipped at busy times. Fine for this use case; do not build anything that assumes exact timing. The downstream AI scan should read whatever `changes-latest.json` is current, whenever it runs.
- **60-day auto-disable**: GitHub disables scheduled workflows in repos with no activity for 60 days. Reqcon's own commits count as activity, so this only bites after 60 straight no-change days across all boards — unlikely, but add it to the README troubleshooting section ("if the badge goes stale, re-enable the workflow in the Actions tab").
- Timestamps in reports/README MUST be computed in `America/New_York` (zoneinfo), since runners are UTC.
- Local runs remain fully supported (`reqcon scan` works anywhere the repo is cloned); a launchd plist is no longer shipped in v1. If HTML boards prove unreliable from CI (see §12), a local run can fill in — state merges cleanly because it's committed to the repo.

Log to stdout/stderr only (visible in the Actions run log); no log file needed in v1. SHOULD add a README badge: `![daily-scan](https://github.com/pn-le/Reqcon/actions/workflows/scan.yml/badge.svg)`.

## 10. Testing

- Unit tests for: diff engine (added/removed/changed/baseline/error-carry-forward), posting identity normalization, state atomic write, keyword tagging, each adapter's response mapping using **fixture JSON/HTML files** checked into `tests/fixtures/` (no network in tests).
- One `--board`-level integration test marked `@pytest.mark.network`, skipped by default.
- Acceptance: `pytest` green, plus a manual double-run check — `reqcon scan` twice in a row MUST report zero changes on the second run.

## 11. Milestones

**M1 — Core skeleton.** Models, config loading, state, diff engine, report writers, CLI wiring with a stub adapter. Tests for diff + state. *Accept: `reqcon scan` with a fake board produces correct md/json; double-run shows no changes.*

**M2 — Greenhouse + Workday adapters.** Verify real tokens/tenants for the 5 API boards; fixture-based tests. *Accept: `reqcon init` dry-run fetches non-zero postings from ≥4 of the 5 API boards.*

**M3 — Scrapling HTML adapter.** Resolve selectors for MERL, STR, Ubicept; disable any board that can't be made reliable, with a comment. *Accept: each enabled HTML board returns stable posting IDs across two consecutive fetches.*

**M4 — Ship: Actions + self-updating README.** `scan.yml` workflow, `readme.py` marker updater with `first_seen` tracking, badge, prune logic, `reqcon list`, README hand-written sections. *Accept: `workflow_dispatch` run on GitHub succeeds end-to-end and pushes a commit updating README/data/reports; a second dispatched run with no board changes pushes nothing; README renders correctly on the repo page with student-role rows first.*

## 12. Risks & mitigations

- **Workday endpoint is unofficial** and may change shape → defensive parsing, `AdapterError` on drift, board keeps last good snapshot.
- **HTML boards redesign** → Scrapling's adaptive re-location helps, but if extraction yields 0 postings where previous snapshot had >0, treat as `AdapterError` (suspicious drop), not as "all removed". This rule applies to ALL adapters: a drop to zero from a nonzero snapshot requires two consecutive zero runs before postings are marked removed.
- **ToS/politeness** → API-first design, 1 fetch/board/day, no aggregators, custom UA. This is personal-use monitoring at trivial volume.
- **Datacenter IP blocking**: GitHub Actions runners use cloud IPs that anti-bot systems treat with suspicion. The Greenhouse/Workday JSON endpoints are generally fine from CI; the Scrapling HTML boards (MERL, STR, Ubicept) are the risk. If an HTML board consistently fails from CI, set `enabled_ci: false` on it (adapter skips it when `--ci` is passed, board keeps last snapshot with status `skipped-ci`) rather than fighting the block — it can be covered by occasional local runs.
- **Public repo = public data**: state and reports are committed, so tracked boards and postings are visible to anyone. That's fine (it's all public job data and doubles as a portfolio piece) — but never commit anything personal: no application status, no notes, no resume material in this repo.

## 13. Future (explicitly not v1)

Push notification on `student-role` additions (GitHub already gives a free version: Watch → Custom → Releases/commits, or an RSS feed of commits); more adapters (Lever, Ashby, SmartRecruiters); `reqcon add <url>` with auto-detection of the hosting platform; GitHub Pages HTML dashboard rendered from `changes-latest.json`.
