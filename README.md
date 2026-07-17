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

<!-- reqcon:openings -->
## Current openings

_Student roles (intern / co-op) spotted on tracked boards. Auto-updated by `reqcon scan` on 2026-07-17 15:04 EDT._

### Lila Sciences — 12 of 116 postings
- [Co-Op, AI Security](https://job-boards.greenhouse.io/lilasciences/jobs/4280945009) — Cambridge, MA USA
- [Co-Op, Automation](https://job-boards.greenhouse.io/lilasciences/jobs/4287004009) — Cambridge, MA USA
- [Co-Op, Autonomous SEM](https://job-boards.greenhouse.io/lilasciences/jobs/4300246009) — Cambridge, MA USA
- [Co-Op, Data Extraction](https://job-boards.greenhouse.io/lilasciences/jobs/4280811009) — Cambridge, MA USA
- [Co-Op, Finance](https://job-boards.greenhouse.io/lilasciences/jobs/4278444009) — Cambridge, MA USA; San Francisco, CA USA
- [Co-Op, LS AI, ML Scientist for Protein Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4289387009) — San Francisco, CA USA
- [Co-op, Machine Learning for Digital Twins](https://job-boards.greenhouse.io/lilasciences/jobs/4280809009) — Cambridge, MA USA
- [Co-op, Materials Science, Electrosynthesis](https://job-boards.greenhouse.io/lilasciences/jobs/4288399009) — Cambridge, MA USA
- [Co-op, Mechanical Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4284223009) — Cambridge, MA USA
- [Co-Op, ML Scientist for Biology](https://job-boards.greenhouse.io/lilasciences/jobs/4294212009) — San Francisco, CA USA
- [Co-Op, Next Gen Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4289960009) — Cambridge, MA USA
- [Co-Op, Software Product Management](https://job-boards.greenhouse.io/lilasciences/jobs/4286512009) — Cambridge, MA USA

### BillionToOne — 0 of 101 postings
- _no intern/co-op postings right now_

### Anduril — 5 of 2165 postings
- [2027 Electrical Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5148101007?gh_jid=5148101007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Costa Mesa, California, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- [2027 Manufacturing Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5153218007?gh_jid=5153218007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Costa Mesa, California, United States; Irvine, California, United States; Seattle, Washington, United States
- [2027 Mechanical Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5153187007?gh_jid=5153187007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Costa Mesa, California, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- [2027 Software Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5148079007?gh_jid=5148079007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Costa Mesa, California, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- [Naval Architect Co-op - Winter 2027](https://boards.greenhouse.io/andurilindustries/jobs/5170844007?gh_jid=5170844007) — Costa Mesa, California, United States

### Formlabs — 12 of 170 postings
- [AI Software Intern (Fall 2026)](https://careers.formlabs.com/job/8067641/apply/?gh_jid=8067641) — Somerville, MA
- [Algorithms Software Intern (Fall 2026)](https://careers.formlabs.com/job/8060759/apply/?gh_jid=8060759) — Somerville, MA
- [Event Logistics Intern (Fall 2026)](https://careers.formlabs.com/job/7985796/apply/?gh_jid=7985796) — Somerville, MA
- [Global Sourcing Intern (Fall 2026)](https://careers.formlabs.com/job/7747228/apply/?gh_jid=7747228) — Somerville, MA
- [Hardware R&D Engineering Intern (Fall 2026)](https://careers.formlabs.com/job/7890746/apply/?gh_jid=7890746) — Somerville, MA
- [Hardware Systems Integration Intern (Fall 2026)](https://careers.formlabs.com/job/7927471/apply/?gh_jid=7927471) — Somerville, MA
- [Manufacturing Test Software Intern (Fall 2026)](https://careers.formlabs.com/job/8021679/apply/?gh_jid=8021679) — Somerville, MA
- [Print Production Intern (Fall 2026)](https://careers.formlabs.com/job/7997509/apply/?gh_jid=7997509) — Somerville, MA
- [Program Management - Global Sourcing Intern (Fall 2026)](https://careers.formlabs.com/job/8001882/apply/?gh_jid=8001882) — Somerville, MA
- [Software Engineer Intern (Full stack)](https://careers.formlabs.com/job/8059424/apply/?gh_jid=8059424) — Budapest, Hungary
- [Supply Chain Operations Software Intern (Fall 2026)](https://careers.formlabs.com/job/8069676/apply/?gh_jid=8069676) — Somerville, MA
- [Test Software - Manufacturing Intern (Fall 2026)](https://careers.formlabs.com/job/8065543/apply/?gh_jid=8065543) — Boston, MA

### STR — 1 of 148 postings
- [Sensors Fall/Spring Co-op – RF Systems Engineer ](https://job-boards.greenhouse.io/systemstechnologyresearch/jobs/4693331006) — Woburn, MA

### Draper — 1 of 186 postings
- [Laboratory Research Co-Op](https://draper.wd5.myworkdayjobs.com/en-US/Draper_Careers/job/Cambridge-MA/Microsystems-Integration-Intern_JR002599) — Cambridge, MA

### MERL (Mitsubishi Electric Research Labs) — 18 of 18 postings
- [CA0153: Internship - High-Fidelity Visualization and Simulation for Space Applications](https://www.merl.com/employment/internship-openings#CA0153)
- [CA0283: Internship - Active SLAM for Aerial Robots](https://www.merl.com/employment/internship-openings#CA0283)
- [CI0213: Internship - Efficient Foundation Models for Edge Intelligence](https://www.merl.com/employment/internship-openings#CI0213)
- [CV0075: Internship - Multimodal Embodied AI](https://www.merl.com/employment/internship-openings#CV0075)
- [CV0101: Internship - Multimodal Algorithmic Reasoning](https://www.merl.com/employment/internship-openings#CV0101)
- [EA0234: Internship - Multi-modal sensor fusion for predictive maintenance](https://www.merl.com/employment/internship-openings#EA0234)
- [EA0237: Internship - Condition Monitoring and Fault Diagnosis](https://www.merl.com/employment/internship-openings#EA0237)
- [EA0241: Internship - Process Modeling for Factory Automation](https://www.merl.com/employment/internship-openings#EA0241)
- [MS0098: Internship - Control and Estimation for Large-Scale Thermofluid Systems](https://www.merl.com/employment/internship-openings#MS0098)
- [MS0254: Internship - Decentralized Data Assimilation for Large Scale Systems](https://www.merl.com/employment/internship-openings#MS0254)
- [MS0259: Internship - Multi-Fidelity Dynamic Models for Energy Systems](https://www.merl.com/employment/internship-openings#MS0259)
- [MS0260: Internship - Experimental Thermofluid Systems](https://www.merl.com/employment/internship-openings#MS0260)
- [OR0298: Internship - Robotic Disassembly](https://www.merl.com/employment/internship-openings#OR0298)
- [OR0299: Internship - Human-Robot Interaction](https://www.merl.com/employment/internship-openings#OR0299)
- [SA0191: Internship - Human-Robot Interaction Based on Multimodal Scene Understanding](https://www.merl.com/employment/internship-openings#SA0191)
- [SA0302: Internship - Audio Processing for Moving Sounds](https://www.merl.com/employment/internship-openings#SA0302)
- [SA0307: Internship - Neural Spatial Audio Processing](https://www.merl.com/employment/internship-openings#SA0307)
- [ST0238: Internship - Multi-Modal Sensing and Understanding](https://www.merl.com/employment/internship-openings#ST0238)

### Ubicept — 2 of 3 postings
- [Fall Co-op / Internship](https://www.ubicept.com/careers/fall-co-op-internship) — Boston, MA
- [Spring Co-op / Internship](https://www.ubicept.com/careers/spring-co-op-internship) — Boston, MA

<!-- /reqcon:openings -->
