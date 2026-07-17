# Reqcon

Recon for job reqs. A local Python CLI that snapshots a configured list of job boards once a day, diffs against the previous snapshot, and emits a change report (postings **added**, **removed**, **changed**). Built so a daily AI internship scan can read one JSON file instead of re-fetching the same boards.

Design principle: **APIs before scraping.** Greenhouse and Workday boards use their JSON endpoints; only boards with no structured endpoint fall back to HTML scraping via [Scrapling](https://github.com/D4Vinci/Scrapling).

## Setup

```bash
git clone https://github.com/pn-le/Reqcon.git && cd Reqcon
python3 -m venv .venv
.venv/bin/pip install -e ".[scrape]"   # [scrape] enables the HTML adapter (MERL, Ubicept)
.venv/bin/reqcon init                  # create dirs, validate boards.yaml, dry-run every board
```

`init` fetches each enabled board without writing state. If every line says `ok (N postings)`, you're set.

## Usage

```bash
reqcon scan                    # fetch all boards, diff, write reports
reqcon scan --board draper     # single board
reqcon list                    # configured boards + last fetch state
```

Exit codes: `0` success (even with zero changes), `1` any board errored, `2` config error.

`reqcon` looks for `boards.yaml` in the current directory (override with `--config path`).

## Output

Written to `output_dir` (default `~/Desktop/Admin/reqcon`) every scan:

- **`changes-latest.json`** — machine contract, overwritten each run: `run_at`, per-board `added`/`removed`/`changed` posting lists (+ `baseline` on a board's first run), and a `summary`. Errored boards appear as `{"board_id": ..., "status": "error", "error": ...}` and keep their previous snapshot untouched.
- **`reqcon-YYYY-MM-DD.md`** — human digest. `student-role`-tagged postings (title matches intern/co-op/etc.) are bolded and listed first. Last 14 days kept.

State lives in `data/state.json` (atomic writes; last 7 daily snapshots in `data/history/`).

## Adding a board

Add one entry to `boards.yaml` — no code changes for supported adapters:

```yaml
  - id: acme                      # unique slug
    name: Acme Corp
    adapter: greenhouse           # greenhouse | workday | html
    board_token: acmecorp         # greenhouse: token from boards-api.greenhouse.io URL
```

Workday boards need `tenant`, `wd_host`, `site` (from the careers URL, e.g. `acme.wd5.myworkdayjobs.com/Acme_Careers` → tenant `acme`, site `Acme_Careers`). HTML boards need `url` + CSS selectors:

```yaml
  - id: example
    adapter: html
    url: https://example.com/careers
    item_selector: ".job-card"        # one element per posting
    title_selector: "h3"              # inside the item (default: a)
    url_selector: "a"                 # inside the item (default: a)
    location_selector: ".loc"         # optional
    stealth: true                     # optional: headless-browser fetch for bot-walled sites
```

Set `enabled: false` to keep a board configured but skipped.

Tip: before writing selectors, check whether the site embeds Greenhouse/Workday links — STR looked like an HTML board but is Greenhouse-hosted (`job-boards.greenhouse.io/systemstechnologyresearch`), so it uses the API adapter.

## Scheduling (launchd)

Runs `reqcon scan` weekdays at 07:00 local time; launchd fires missed runs on wake (cron doesn't):

```bash
cp launchd/com.pnle.reqcon.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.pnle.reqcon.plist
```

Logs append to `reports/reqcon.log`. If your clone or venv lives elsewhere, edit the two paths in the plist first. To stop: `launchctl unload ~/Library/LaunchAgents/com.pnle.reqcon.plist`.

## Behavior worth knowing

- **First run of a board** records a `baseline`, not 200 "new" postings.
- **Fetch errors** never look like removals: the board is marked `error` and its previous snapshot carries forward.
- **Suspicious drops**: a fetch returning 0 postings where the snapshot had >0 is treated as an error once; only a second consecutive zero run marks the postings removed.
- **Politeness**: custom User-Agent (`reqcon/x.y.z (personal job-board monitor)`), 1 fetch per board per run, ≤2 retries with backoff, sequential fetching. No aggregators (LinkedIn, Indeed, …) — permanently out of scope.

## Development

```bash
.venv/bin/pip install -e ".[scrape,dev]"
.venv/bin/pytest              # fixture-based, no network
.venv/bin/pytest -m network   # one live integration test
```
