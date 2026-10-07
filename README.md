# Reqcon

![daily-scan](https://github.com/pn-le/Reqcon/actions/workflows/scan.yml/badge.svg)

Recon for job reqs. Reqcon snapshots a configured list of job boards daily, diffs against the previous snapshot, and reports postings **added**, **removed**, and **changed**. A scheduled GitHub Actions workflow runs the scan, commits updated state, and rewrites the dashboard below — no machine required. A daily AI internship scan reads [`reports/changes-latest.json`](reports/changes-latest.json) instead of re-fetching boards.

Design principle: **APIs before scraping.** Greenhouse and Workday boards use their JSON endpoints; only boards with no structured endpoint fall back to HTML scraping via [Scrapling](https://github.com/D4Vinci/Scrapling).

## How it runs

`.github/workflows/scan.yml` runs `reqcon scan --update-readme --ci` weekdays at 11:00 UTC (~7 AM ET) and on the manual **Run workflow** button. State (`data/`) and reports (`reports/`) are committed to this repo because Actions runners are ephemeral — each run that finds changes produces exactly one commit; a no-change day produces none. Timestamps are computed in `America/New_York`.

The machine contract for downstream consumers:
`https://raw.githubusercontent.com/pn-le/Reqcon/main/reports/changes-latest.json`

## Local usage

Fully supported anywhere the repo is cloned (state merges cleanly since it's in git):

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[scrape]"   # [scrape] enables the HTML adapter (MERL, Ubicept)
.venv/bin/reqcon init                  # validate boards.yaml, dry-run every board
.venv/bin/reqcon scan                  # fetch, diff, write reports
.venv/bin/reqcon scan --update-readme  # also refresh the dashboard section below
.venv/bin/reqcon list                  # boards + last fetch state
```

Exit codes: `0` success (even with zero changes), `1` any board errored (suppressed with `--ci`), `2` config error.

## Output

- **`reports/changes-latest.json`** — machine contract, refreshed each run: `run_at`, per-board `added`/`removed`/`changed` posting lists (+ `baseline` on a board's first run), and a `summary`. Errored boards appear as `{"board_id": ..., "status": "error", ...}` and keep their previous snapshot untouched.
- **`reports/reqcon-YYYY-MM-DD.md`** — human digest, written on days with changes. `student-role`-tagged postings (intern/co-op titles) are bolded and listed first. Last 14 days kept.
- **`data/state.json`** — current snapshot per board, including each posting's `first_seen` date (last 7 daily snapshots in `data/history/`).

## Adding a board

One entry in `boards.yaml` — no code changes:

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

Flags: `enabled: false` skips a board everywhere; `enabled_ci: false` skips it only in CI (status `skipped-ci`) — use when a site blocks datacenter IPs; occasional local runs cover it.

Tip: before writing selectors, check whether the site embeds Greenhouse/Workday links — STR looked like an HTML board but is Greenhouse-hosted, so it uses the API adapter.

## Behavior worth knowing

- **First run of a board** records a `baseline`, not hundreds of "new" postings.
- **Fetch errors** never look like removals: the board is marked `error` and its previous snapshot carries forward.
- **Suspicious drops**: a fetch returning 0 postings where the snapshot had >0 is treated as an error once; only a second consecutive zero run marks the postings removed.
- **Politeness**: custom User-Agent, 1 fetch per board per run, ≤2 retries with backoff, sequential fetching. No aggregators (LinkedIn, Indeed, …) — permanently out of scope.

## Troubleshooting

- **Badge/dashboard stale?** GitHub disables scheduled workflows after 60 days without repo activity. Re-enable under the **Actions** tab (daily-scan → Enable workflow). Reqcon's own commits normally count as activity, so this only happens after 60 straight no-change days.
- **An HTML board keeps failing in CI** (datacenter IP blocked): set `enabled_ci: false` on it and run `reqcon scan` locally now and then.
- Cron runs are best-effort — they can start late or occasionally skip; the dashboard just updates on the next run.

## Development

```bash
.venv/bin/pip install -e ".[scrape,dev]"
.venv/bin/pytest              # fixture-based, no network
.venv/bin/pytest -m network   # one live integration test
```

---

<!-- REQCON:START -->
**Last scan:** 2026-10-07 13:36 EDT · 8 boards · 79 new · 57 removed

✅ Lila Sciences · ✅ BillionToOne · ✅ Anduril · ✅ Formlabs · ✅ STR · ✅ Draper · ✅ MERL (Mitsubishi Electric Research Labs) · ✅ Ubicept

### New this week

| Company | Role | Location | First seen |
|---|---|---|---|
| 🎓 Anduril | [2027 Deployment Logistics Intern](https://boards.greenhouse.io/andurilindustries/jobs/5255866007?gh_jid=5255866007) | London, England, United Kingdom | 2026-10-07 |
| 🎓 Anduril | [2027 Software Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5255902007?gh_jid=5255902007) | London, England, United Kingdom | 2026-10-07 |
| 🎓 Draper | [Mechanical Engineering & System Packaging Co-Op (Spring 2027)](https://draper.wd5.myworkdayjobs.com/en-US/Draper_Careers/job/Cambridge-MA/Mechanical-Engineering---System-Packaging-Co-Op--Spring-2027-_JR003000) | Cambridge, MA | 2026-10-07 |
| 🎓 Draper | [Microsystems Integration Intern](https://draper.wd5.myworkdayjobs.com/en-US/Draper_Careers/job/Cambridge-MA/Microsystems-Integration-Intern_JR003002-1) | Cambridge, MA | 2026-10-07 |
| 🎓 Formlabs | [Software Engineer Intern (Full stack)](https://careers.formlabs.com/job/8260955/apply/?gh_jid=8260955) | Budapest, Hungary | 2026-10-07 |
| 🎓 Anduril | [2027 Quality & Test Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5257674007?gh_jid=5257674007) | Ashville, Ohio, United States; Costa Mesa, California, United States; Irvine, California, United States; Quonset, Rhode Island, United States; Santa Ana, California, United States | 2026-10-06 |
| 🎓 Anduril | [2027 Reliability Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5257682007?gh_jid=5257682007) | Costa Mesa, California, United States | 2026-10-06 |
| 🎓 Anduril | [2027 Systems Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5257690007?gh_jid=5257690007) | Boston, Massachusetts, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Reston, Virginia, United States; Seattle, Washington, United States | 2026-10-06 |
| 🎓 Anduril | [Winter 2027 Quality & Test Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5257571007?gh_jid=5257571007) | Ashville, Ohio, United States; Santa Ana, California, United States | 2026-10-06 |
| 🎓 Anduril | [Winter 2027 Reliability Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5257693007?gh_jid=5257693007) | Costa Mesa, California, United States | 2026-10-06 |
| 🎓 Formlabs | [Talent Acquisition Intern](https://careers.formlabs.com/job/8255650/apply/?gh_jid=8255650) | Budapest, Hungary | 2026-10-05 |
| 🎓 Anduril | [2027 Industrial Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5255593007?gh_jid=5255593007) | Ashville, Ohio, United States; Costa Mesa, California, United States | 2026-10-03 |
| 🎓 Anduril | [2027 Supply Chain Intern](https://boards.greenhouse.io/andurilindustries/jobs/5255827007?gh_jid=5255827007) | Costa Mesa, California, United States; Fort Collins, Colorado, United States; Quincy, Massachusetts, United States; Santa Ana, California, United States; Waltham, Massachusetts, United States | 2026-10-03 |
| 🎓 Draper | [Cable And Harnessing Intern (Summer 2027)](https://draper.wd5.myworkdayjobs.com/en-US/Draper_Careers/job/Cambridge-MA/Cable-And-Harnessing-Intern--Summer-2027-_JR002963) | Cambridge, MA | 2026-10-01 |
| Anduril | [ Senior Security Engineer, Identity](https://boards.greenhouse.io/andurilindustries/jobs/5259074007?gh_jid=5259074007) | Washington, District of Columbia, United States | 2026-10-07 |
| Anduril | [2027 Early Career Technical Operations Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5255914007?gh_jid=5255914007) | London, England, United Kingdom | 2026-10-07 |
| Anduril | [Demand & Supply Planning, Sentry](https://boards.greenhouse.io/andurilindustries/jobs/5259091007?gh_jid=5259091007) | Costa Mesa, California, United States | 2026-10-07 |
| Anduril | [Deputy Program Chief Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5100128007?gh_jid=5100128007) | Irvine, California, United States | 2026-10-07 |
| Anduril | [Division Talent, Planning & Strategy](https://boards.greenhouse.io/andurilindustries/jobs/5260092007?gh_jid=5260092007) | Seattle, Washington, United States | 2026-10-07 |
| Anduril | [Electrical Harness Design Engineer, Air Dominance and Strike](https://boards.greenhouse.io/andurilindustries/jobs/5260197007?gh_jid=5260197007) | Costa Mesa, California, United States | 2026-10-07 |
| Anduril | [Head of Program Management, EW](https://boards.greenhouse.io/andurilindustries/jobs/5259724007?gh_jid=5259724007) | Costa Mesa, California, United States | 2026-10-07 |
| Anduril | [Industrial Engineer, Maritime Manufacturing](https://boards.greenhouse.io/andurilindustries/jobs/5259842007?gh_jid=5259842007) | Santa Ana, California, United States | 2026-10-07 |
| Anduril | [Manager, Demand & Supply Planning, Sentry](https://boards.greenhouse.io/andurilindustries/jobs/5237833007?gh_jid=5237833007) | Costa Mesa, California, United States | 2026-10-07 |
| Anduril | [Manager, Manufacturing Operations - Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/4734420007?gh_jid=4734420007) | Santa Ana, California, United States | 2026-10-07 |
| Anduril | [Maritime - Technical Writer](https://boards.greenhouse.io/andurilindustries/jobs/5075515007?gh_jid=5075515007) | Quincy, Massachusetts, United States | 2026-10-07 |
| Anduril | [Material Planner III, Sentry](https://boards.greenhouse.io/andurilindustries/jobs/5007770007?gh_jid=5007770007) | Irvine, California, United States | 2026-10-07 |
| Anduril | [Metrology Lab Specialist](https://boards.greenhouse.io/andurilindustries/jobs/5257542007?gh_jid=5257542007) | Costa Mesa, California, United States | 2026-10-07 |
| Anduril | [Operations Engineer, Warehousing & Capacity](https://boards.greenhouse.io/andurilindustries/jobs/5259530007?gh_jid=5259530007) | Costa Mesa, California, United States | 2026-10-07 |
| Anduril | [Principal Construction Manager](https://boards.greenhouse.io/andurilindustries/jobs/5252331007?gh_jid=5252331007) | Phoenix, Arizona, United States | 2026-10-07 |
| Anduril | [Production Coordinator](https://boards.greenhouse.io/andurilindustries/jobs/5161935007?gh_jid=5161935007) | Morrisville, North Carolina, United States | 2026-10-07 |

…and 333 more — see the [latest digest](reports/reqcon-2026-10-07.md).

<details>
<summary>All tracked postings (3276)</summary>

**Lila Sciences** (107)
- [(Senior) Director, Portfolio Strategy, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4258093009) — Cambridge, MA USA
- [Associate Director / Director, Customer Program Management, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4184652009) — Cambridge, MA USA
- [Associate Director / Director, Customer Program Management, Physical Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4290011009) — Cambridge, MA USA
- [Associate Director / Director, Strategic Finance](https://job-boards.greenhouse.io/lilasciences/jobs/4353595009) — Cambridge, MA USA
- [Associate Director, App   ](https://job-boards.greenhouse.io/lilasciences/jobs/4371404009) — Cambridge, MA USA; San Francisco, CA USA
- [Associate Director/Director, Commercial Counsel ](https://job-boards.greenhouse.io/lilasciences/jobs/4174259009) — Cambridge, MA USA; San Francisco, CA USA
- [Associate Scientist/Scientist I, Protein Science Developability](https://job-boards.greenhouse.io/lilasciences/jobs/4299967009) — Cambridge, MA USA
- [Associate Scientist/Scientist I, Translational Biology](https://job-boards.greenhouse.io/lilasciences/jobs/4415281009) — Cambridge, MA USA
- [Chemistry Technical Program Manager](https://job-boards.greenhouse.io/lilasciences/jobs/4204188009) — Cambridge, MA USA
- [Chief of Staff to the CEO](https://job-boards.greenhouse.io/lilasciences/jobs/4285660009) — Cambridge, MA USA
- [Controls Engineer II, Sustaining Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4294210009) — Cambridge, MA USA
- [Director / Senior Director, Origins](https://job-boards.greenhouse.io/lilasciences/jobs/4314463009) — Cambridge, MA USA
- [Director of Product, Life Sciences (Chemistry)](https://job-boards.greenhouse.io/lilasciences/jobs/4048370009) — Cambridge, MA USA
- [Director, Enterprise Account Management, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4423498009) — Cambridge, MA USA
- [Director, Enterprise Account Management, Physical Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4423477009) — Cambridge, MA USA
- [Director, Materials AISF Program Lead](https://job-boards.greenhouse.io/lilasciences/jobs/4287216009) — Cambridge, MA USA
- [Director, Product Marketing, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4420035009) — Cambridge, MA USA
- [Director/ Senior Director, Product, Materials Chemistry](https://job-boards.greenhouse.io/lilasciences/jobs/4320806009) — Cambridge, MA USA
- [Director/Senior Director, Molecular Discovery](https://job-boards.greenhouse.io/lilasciences/jobs/4273680009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Engineer I, Research Operations (2nd Shift)](https://job-boards.greenhouse.io/lilasciences/jobs/4386306009) — Cambridge, MA USA
- [Engineer I, Research Operations, (1st shift)](https://job-boards.greenhouse.io/lilasciences/jobs/4277806009) — Cambridge, MA USA
- [Finance Business Partner, AI & Software](https://job-boards.greenhouse.io/lilasciences/jobs/4359832009) — Cambridge, MA USA
- [Global Security Operations Center Manager](https://job-boards.greenhouse.io/lilasciences/jobs/4331069009) — Cambridge, MA USA
- [Head of Software Product](https://job-boards.greenhouse.io/lilasciences/jobs/4205624009) — Cambridge, MA USA; San Francisco, CA USA
- [Join Our Talent Community](https://job-boards.greenhouse.io/lilasciences/jobs/4070054009) — Cambridge, MA USA; San Francisco, CA USA
- [Lab Operations Specialist](https://job-boards.greenhouse.io/lilasciences/jobs/4395906009) — Cambridge, MA USA
- [Machine Learning Scientist I / II, Protein Design](https://job-boards.greenhouse.io/lilasciences/jobs/4396760009) — San Francisco, CA USA
- [Manager / Senior Manager, Enterprise GTM, Chemicals](https://job-boards.greenhouse.io/lilasciences/jobs/4353659009) — Cambridge, MA USA
- [Manager / Senior Manager, Enterprise GTM, Materials](https://job-boards.greenhouse.io/lilasciences/jobs/4353656009) — Cambridge, MA USA
- [Manager / Senior Manager, Finance, Fixed Asset Accounting](https://job-boards.greenhouse.io/lilasciences/jobs/4195640009) — Cambridge, MA USA; San Francisco, CA USA
- [Manager / Senior Manager, Multimedia ](https://job-boards.greenhouse.io/lilasciences/jobs/4157130009) — Cambridge, MA USA
- [Manager, Revenue Accounting](https://job-boards.greenhouse.io/lilasciences/jobs/4195605009) — Cambridge, MA USA
- [Microfabrication Scientist I/II](https://job-boards.greenhouse.io/lilasciences/jobs/4400746009) — Cambridge, MA USA
- [ML Engineer, Applied AI](https://job-boards.greenhouse.io/lilasciences/jobs/4377936009) — Cambridge, MA USA; San Francisco, CA USA
- [ML Engineer, LS AI](https://job-boards.greenhouse.io/lilasciences/jobs/4222224009) — San Francisco, CA USA
- [ML Scientist I/II, AI for Protein Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4392245009) — San Francisco, CA USA
- [ML Scientist, Foundation Models for Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4222051009) — San Francisco, CA USA
- [ML Scientist, Nucleic Acid Design](https://job-boards.greenhouse.io/lilasciences/jobs/4324969009) — San Francisco, CA USA
- [Operations and Quality Engineer, Sustaining Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4277749009) — Cambridge, MA USA
- [Platform Scientist I/II, Functional Materials Instrumentation](https://job-boards.greenhouse.io/lilasciences/jobs/4423504009) — Cambridge, MA USA
- [Portfolio Manager, Government Partnerships (DARPA & ARPA-H)](https://job-boards.greenhouse.io/lilasciences/jobs/4297690009) — Cambridge, MA USA
- [Principal Engineer, AI Security](https://job-boards.greenhouse.io/lilasciences/jobs/4210497009) — Cambridge, MA USA
- [Principal Engineer, AI Security](https://job-boards.greenhouse.io/lilasciences/jobs/4403714009) — Cambridge, MA USA
- [Principal Engineer, Software (Enterprise Platform)](https://job-boards.greenhouse.io/lilasciences/jobs/4247103009) — San Francisco, CA USA
- [Principal Machine Learning Engineer, Applied AI ](https://job-boards.greenhouse.io/lilasciences/jobs/4400744009) — Cambridge, MA USA; San Francisco, CA USA
- [Principal Scientist / Associate Director, Agentic AI Research for Materials Science](https://job-boards.greenhouse.io/lilasciences/jobs/4273850009) — Cambridge, MA USA; San Francisco, CA USA
- [Principal Scientist / Associate Director, Soft Materials Experimentation](https://job-boards.greenhouse.io/lilasciences/jobs/4403708009) — Cambridge, MA USA
- [Principal Software Engineer, Data](https://job-boards.greenhouse.io/lilasciences/jobs/4250071009) — Cambridge, MA USA; San Francisco, CA USA
- [Principal Software Engineer, Instrument Simulations](https://job-boards.greenhouse.io/lilasciences/jobs/4186530009) — Cambridge, MA USA
- [Principal Technical Program Manager, App](https://job-boards.greenhouse.io/lilasciences/jobs/4087979009) — Cambridge, MA USA
- [Product Lead, Software/Applied AI](https://job-boards.greenhouse.io/lilasciences/jobs/4182437009) — Cambridge, MA USA; San Francisco, CA USA
- [Research Product Manager, Fine-tuning](https://job-boards.greenhouse.io/lilasciences/jobs/4339607009) — Cambridge, MA USA; San Francisco, CA USA
- [Research Product Manager, Post Training](https://job-boards.greenhouse.io/lilasciences/jobs/4310498009) — Cambridge, MA USA; San Francisco, CA USA
- [Research Scientist I/II, Computational Organic Electronics](https://job-boards.greenhouse.io/lilasciences/jobs/4376824009) — Cambridge, MA USA
- [Research Scientist, Computational Condensed Matter Physics](https://job-boards.greenhouse.io/lilasciences/jobs/4324886009) — Cambridge, MA USA
- [Robotics Operations Engineer I, First Shift](https://job-boards.greenhouse.io/lilasciences/jobs/4410043009) — Cambridge, MA USA
- [Scientist I/II, Characterization and Composition Analysis](https://job-boards.greenhouse.io/lilasciences/jobs/4384606009) — Cambridge, MA USA
- [Scientist I/II, X-ray Diffraction Characterization](https://job-boards.greenhouse.io/lilasciences/jobs/4378385009) — Cambridge, MA USA
- [Scientist II / Senior ML Scientist, Data-Efficient Learning for Drug Discovery](https://job-boards.greenhouse.io/lilasciences/jobs/4340147009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Scientist II / Senior Scientist, Electron Diffraction Characterization](https://job-boards.greenhouse.io/lilasciences/jobs/4378383009) — Cambridge, MA USA
- [Scientist II, Silicon Photonics](https://job-boards.greenhouse.io/lilasciences/jobs/4383465009) — Cambridge, MA USA
- [Scientist II/ Senior Scientist, BioML](https://job-boards.greenhouse.io/lilasciences/jobs/4395729009) — San Francisco, CA USA
- [Scientist II/Senior Characterization Scientist,  Condensed Matter](https://job-boards.greenhouse.io/lilasciences/jobs/4246305009) — Cambridge, MA USA
- [Scientist II/Senior Scientist, Computational Biophysics](https://job-boards.greenhouse.io/lilasciences/jobs/4340155009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Scientist II/Senior Scientist, Solid-State Materials](https://job-boards.greenhouse.io/lilasciences/jobs/4271809009) — Cambridge, MA USA
- [Scientist, Epitaxial Thin Film Synthesis](https://job-boards.greenhouse.io/lilasciences/jobs/4253548009) — Cambridge, MA USA
- [Senior / Engineer II, AI Lab Research Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4029507009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior / Principal Chemist, AI Safety](https://job-boards.greenhouse.io/lilasciences/jobs/4423500009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Senior / Principal ML Scientist, Foundation Models for Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4222034009) — San Francisco, CA USA
- [Senior / Staff Machine Learning Engineer, Applied AI](https://job-boards.greenhouse.io/lilasciences/jobs/4302917009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior / Staff Machine Learning Engineer, Applied AI](https://job-boards.greenhouse.io/lilasciences/jobs/4400741009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior Automated Systems Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4110339009) — Cambridge, MA USA
- [Senior Data Engineer, Bioinformatics, Cheminformatics, Materials](https://job-boards.greenhouse.io/lilasciences/jobs/4377096009) — San Francisco, CA USA
- [Senior Director / Vice President, Chemistry Experiment ](https://job-boards.greenhouse.io/lilasciences/jobs/4300718009) — Cambridge, MA USA
- [Senior Director, Data Platform Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4202443009) — San Francisco, CA USA
- [Senior Director, Software Development, Test Automation](https://job-boards.greenhouse.io/lilasciences/jobs/4294875009) — San Francisco, CA USA
- [Senior Human Factors Engineer I/II, Robotics](https://job-boards.greenhouse.io/lilasciences/jobs/4332442009) — Cambridge, MA USA
- [Senior II/ Staff Software Engineer, Platform Operations](https://job-boards.greenhouse.io/lilasciences/jobs/4212473009) — San Francisco, CA USA
- [Senior II/Staff Mechatronics Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4337828009) — Cambridge, MA USA
- [Senior Manager, Scientific Discovery Capacity Planning](https://job-boards.greenhouse.io/lilasciences/jobs/4359834009) — Cambridge, MA USA
- [Senior ML Scientist, AI for Protein Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4392247009) — San Francisco, CA USA
- [Senior ML Scientist, Biological Systems](https://job-boards.greenhouse.io/lilasciences/jobs/4395725009) — San Francisco, CA USA
- [Senior Product Designer II / Staff Product Designer](https://job-boards.greenhouse.io/lilasciences/jobs/4376188009) — Cambridge, MA USA
- [Senior Research Associate , Automated Chemistry](https://job-boards.greenhouse.io/lilasciences/jobs/4254693009) — Cambridge, MA USA
- [Senior Software Engineer I/II, Back-end/Data, Robotics](https://job-boards.greenhouse.io/lilasciences/jobs/4339324009) — Cambridge, MA USA
- [Senior Software Engineer I/II, Test Robotics](https://job-boards.greenhouse.io/lilasciences/jobs/4332043009) — Cambridge, MA USA
- [Senior Software Engineer II, Enterprise Platform](https://job-boards.greenhouse.io/lilasciences/jobs/4299652009) — San Francisco, CA USA
- [Senior Software Engineer, App](https://job-boards.greenhouse.io/lilasciences/jobs/4248042009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior Software Engineer, Applied AI](https://job-boards.greenhouse.io/lilasciences/jobs/4031455009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior Software Engineer, Data](https://job-boards.greenhouse.io/lilasciences/jobs/4250077009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior Software Engineer, Operations Research](https://job-boards.greenhouse.io/lilasciences/jobs/4246973009) — Cambridge, MA USA
- [Senior Software Engineer, Scientific System of Record](https://job-boards.greenhouse.io/lilasciences/jobs/4248049009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior/Principal ML Scientist, Translational Biology](https://job-boards.greenhouse.io/lilasciences/jobs/4395727009) — San Francisco, CA USA
- [Senior/Principal Scientist, Small Molecule Therapeutics](https://job-boards.greenhouse.io/lilasciences/jobs/4296054009) — Cambridge, MA USA
- [Shift Supervisor, Research Operations](https://job-boards.greenhouse.io/lilasciences/jobs/4277904009) — Cambridge, MA USA
- [Software Engineer, AI Platform](https://job-boards.greenhouse.io/lilasciences/jobs/4031328009) — Cambridge, MA USA
- [Sr Principal/ Principal Software Engineer, Scientific System of Record](https://job-boards.greenhouse.io/lilasciences/jobs/4193827009) — Cambridge, MA USA; San Francisco, CA USA
- [Sr Principal/Principal Software Engineer, App](https://job-boards.greenhouse.io/lilasciences/jobs/4248036009) — Cambridge, MA USA; San Francisco, CA USA
- [Staff / Principal Automated Systems Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4110350009) — Cambridge, MA USA
- [Staff Engineer, Data Platform](https://job-boards.greenhouse.io/lilasciences/jobs/4222065009) — Cambridge, MA USA; San Francisco, CA USA
- [Staff Engineer, Enterprise Externalization](https://job-boards.greenhouse.io/lilasciences/jobs/4390579009) — San Francisco, CA USA
- [Staff Forward Deployed Engineer, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4031282009) — Cambridge, MA USA; San Francisco, CA USA
- [Staff Forward Deployed Engineer, Physical Sciences (Level Flexible)](https://job-boards.greenhouse.io/lilasciences/jobs/4031303009) — Cambridge, MA USA; San Francisco, CA USA
- [Staff Software Engineer, Scientific System of Record](https://job-boards.greenhouse.io/lilasciences/jobs/4248045009) — Cambridge, MA USA; San Francisco, CA USA
- [Supply Chain Demand Planner](https://job-boards.greenhouse.io/lilasciences/jobs/4423502009) — Cambridge, MA USA
- [Technical Program Manager, AI Data](https://job-boards.greenhouse.io/lilasciences/jobs/4259557009) — Cambridge, MA USA; San Francisco, CA USA
- [Technical Program Manager, AISF](https://job-boards.greenhouse.io/lilasciences/jobs/4289723009) — Cambridge, MA USA

**BillionToOne** (84)
- 🎓 [Research Associate Intern](https://job-boards.greenhouse.io/billiontoone/jobs/4733845005) — Menlo Park, CA
- [Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4702967005) — Roanoke, VA
- [Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4741508005) — Connecticut South
- [Account Support Representative](https://job-boards.greenhouse.io/billiontoone/jobs/4731418005) — North Carolina
- [Account Support Representative](https://job-boards.greenhouse.io/billiontoone/jobs/4731421005) — South Carolina
- [Account Support Representative](https://job-boards.greenhouse.io/billiontoone/jobs/4731424005) — Maryland, Washington, D.C., Eastern Virginia
- [Account Support Representative](https://job-boards.greenhouse.io/billiontoone/jobs/4733008005) — Madison, WI
- [Account Support Representative](https://job-boards.greenhouse.io/billiontoone/jobs/4733233005) — Florida
- [Automation Service Engineer I/II, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4733813005) — Menlo Park, CA
- [Automation Service Engineering Associate I/II, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4736701005) — Menlo Park, CA
- [Client Services Associate I, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4716882005) — Union City, CA
- [Clinical Laboratory Associate, Prenatal (Overnight Shift)](https://job-boards.greenhouse.io/billiontoone/jobs/4678611005) — Union City, CA
- [Clinical Laboratory Scientist, Oncology (PM Shift) ](https://job-boards.greenhouse.io/billiontoone/jobs/4728398005) — Menlo Park, CA
- [Clinical Laboratory Scientist, Prenatal ](https://job-boards.greenhouse.io/billiontoone/jobs/4728399005) — Union City, CA
- [Clinical Laboratory Scientist, Prenatal (contractor)](https://job-boards.greenhouse.io/billiontoone/jobs/4728402005) — Union City, CA
- [Director of IT](https://job-boards.greenhouse.io/billiontoone/jobs/4683268005) — Menlo Park, CA or Union City, CA
- [Director of Office of the CEO, Founder in Residence ](https://job-boards.greenhouse.io/billiontoone/jobs/4707633005) — Menlo Park, CA
- [EMR Integration Specialist](https://job-boards.greenhouse.io/billiontoone/jobs/4726748005) — Remote
- [Environmental Health and Safety Specialist](https://job-boards.greenhouse.io/billiontoone/jobs/4723723005) — Union City, CA and Menlo Park, CA
- [General Supervisor, Prenatal](https://job-boards.greenhouse.io/billiontoone/jobs/4728403005) — Union City, CA
- [LIMS Associate, Prenatal ](https://job-boards.greenhouse.io/billiontoone/jobs/4729775005) — Union City, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4481121005) — Remote
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4663423005) — San Jose, CA 
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4689413005) — Roanoke, VA 
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4689420005) — Rochester, MN
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4689921005) — Chico, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4706194005) — Redwood City, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4706195005) — Santa Clara, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707158005) — Boston, MA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707162005) — North Columbus, OH
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707168005) — Fresno, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707185005) — Milwaukee, WI
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707191005) — Omaha, NE
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707194005) — Portland, OR
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707196005) — Philadelphia, PA 
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707198005) — Riverside, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707205005) — South Seattle, WA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707206005) — Macon, GA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707207005) — Virginia Beach, VA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707209005) — Washington D.C., DC
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4714793005) — South New Jersey, NJ
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4717249005) — Eugene, OR
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4727611005) — Asheville, NC
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4740036005) — Los Angeles, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4740520005) — Wilmington, NC
- [Oncology Regional Sales Manager, Southern California ](https://job-boards.greenhouse.io/billiontoone/jobs/4703269005) — Southern California 
- [Oncology Regional Sales Manager, Upper Midwest](https://job-boards.greenhouse.io/billiontoone/jobs/4667498005) — Minnesota, Wisconsin, North Dakota, South Dakota, Iowa, Nebraska, Missouri
- [Phlebotomy Operations Specialist](https://job-boards.greenhouse.io/billiontoone/jobs/4735176005) — Remote
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4668001005) — West Boston, MA
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4668094005) — Portland, OR
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4679893005) — Southeast San Antonio, TX
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707214005) — Colorado Springs, CO
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707221005) — Idaho Falls, ID
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707226005) — Albuquerque, NM
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707227005) — Eau Claire, WI
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707243005) — Springfield, MO
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707244005) — Albany, NY
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4716459005) — Oklahoma City, OK
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4718574005) — Frederick, MD
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4720160005) — Salt Lake City, UT
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4727656005) — North Chicago, IL
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4736856005) — South Tampa, FL
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4736865005) — Omaha, NE
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4736895005) — St. George, UT
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4740582005) — Westchester, NY
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4740697005) — Central, UT
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4740698005) — Tulsa, OK
- [Prenatal Regional Sales Manager, DMV](https://job-boards.greenhouse.io/billiontoone/jobs/4364573005) — Maryland, Washington, D.C., Eastern Virginia
- [Prenatal Regional Sales Manager, Great Plains](https://job-boards.greenhouse.io/billiontoone/jobs/4611958005) — Minnesota, Iowa, South Dakota, North Dakota
- [Prenatal Regional Sales Manager, Gulf Coast](https://job-boards.greenhouse.io/billiontoone/jobs/4738202005) — Louisiana, Mississippi, Arkansas
- [Prenatal Regional Sales Manager, North Atlantic](https://job-boards.greenhouse.io/billiontoone/jobs/4665574005) — Pennsylvania, New Jersey, Delaware
- [Prenatal Regional Sales Manager, Northern Los Angeles](https://job-boards.greenhouse.io/billiontoone/jobs/4707253005) — Northern California
- [Prenatal Senior Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4080962005) — Remote
- [Process Engineering Associate I/II, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4482409005) — Menlo Park, CA
- [Research Associate](https://job-boards.greenhouse.io/billiontoone/jobs/4733839005) — Menlo Park, CA
- [Sales Training Manager, Prenatal](https://job-boards.greenhouse.io/billiontoone/jobs/4711331005) — Remote
- [Senior Accounting Manager](https://job-boards.greenhouse.io/billiontoone/jobs/4730807005) — Menlo Park, CA
- [Senior Laboratory Director, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4729471005) — Menlo Park, CA
- [Senior Manager, Oncology Product Marketing](https://job-boards.greenhouse.io/billiontoone/jobs/4720536005) — Remote
- [Senior Marketing Specialist ](https://job-boards.greenhouse.io/billiontoone/jobs/4734273005) — Menlo Park, CA or Union City, CA
- [Senior Process Engineer, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4738692005) — Menlo Park, CA
- [Senior Software Engineer, Digital Experiences](https://job-boards.greenhouse.io/billiontoone/jobs/4683643005) — Menlo Park, CA
- [Senior Software Engineer, Prenatal](https://job-boards.greenhouse.io/billiontoone/jobs/4305991005) — Menlo Park, CA
- [Senior Stock Plan Administrator ](https://job-boards.greenhouse.io/billiontoone/jobs/4730826005) — Menlo Park, CA

**Anduril** (2473)
- 🎓 [2026 Guidance, Navigation & Control Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5252665007?gh_jid=5252665007) — Sydney, New South Wales, Australia
- 🎓 [2027 Deployment Logistics Intern](https://boards.greenhouse.io/andurilindustries/jobs/5255866007?gh_jid=5255866007) — London, England, United Kingdom
- 🎓 [2027 Electrical Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5148101007?gh_jid=5148101007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- 🎓 [2027 Flight Software Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5239083007?gh_jid=5239083007) — Costa Mesa, California, United States
- 🎓 [2027 Industrial Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5255593007?gh_jid=5255593007) — Ashville, Ohio, United States; Costa Mesa, California, United States
- 🎓 [2027 Manufacturing Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5153218007?gh_jid=5153218007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Seattle, Washington, United States
- 🎓 [2027 Manufacturing Optimization Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5236893007?gh_jid=5236893007) — Ashville, Ohio, United States
- 🎓 [2027 Mechanical Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5153187007?gh_jid=5153187007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- 🎓 [2027 Quality & Test Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5257674007?gh_jid=5257674007) — Ashville, Ohio, United States; Costa Mesa, California, United States; Irvine, California, United States; Quonset, Rhode Island, United States; Santa Ana, California, United States
- 🎓 [2027 Reliability Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5257682007?gh_jid=5257682007) — Costa Mesa, California, United States
- 🎓 [2027 Software Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5148079007?gh_jid=5148079007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- 🎓 [2027 Software Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5255902007?gh_jid=5255902007) — London, England, United Kingdom
- 🎓 [2027 Supply Chain Intern](https://boards.greenhouse.io/andurilindustries/jobs/5255827007?gh_jid=5255827007) — Costa Mesa, California, United States; Fort Collins, Colorado, United States; Quincy, Massachusetts, United States; Santa Ana, California, United States; Waltham, Massachusetts, United States
- 🎓 [2027 Systems Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5257690007?gh_jid=5257690007) — Boston, Massachusetts, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Reston, Virginia, United States; Seattle, Washington, United States
- 🎓 [Winter 2027 Electrical Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236565007?gh_jid=5236565007) — Costa Mesa, California, United States; Quincy, Massachusetts, United States
- 🎓 [Winter 2027 EWIS Harness Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236577007?gh_jid=5236577007) — Costa Mesa, California, United States
- 🎓 [Winter 2027 Manufacturing Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236589007?gh_jid=5236589007) — Ashville, Ohio, United States; Lexington, Massachusetts, United States; Quincy, Massachusetts, United States
- 🎓 [Winter 2027 Mechanical Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236601007?gh_jid=5236601007) — Ashville, Ohio, United States; Quincy, Massachusetts, United States
- 🎓 [Winter 2027 Propulsion Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236587007?gh_jid=5236587007) — Costa Mesa, California, United States
- 🎓 [Winter 2027 Quality & Test Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5257571007?gh_jid=5257571007) — Ashville, Ohio, United States; Santa Ana, California, United States
- 🎓 [Winter 2027 Reliability Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5257693007?gh_jid=5257693007) — Costa Mesa, California, United States
- 🎓 [Winter 2027 Software Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236563007?gh_jid=5236563007) — Quincy, Massachusetts, United States
- 🎓 [Winter 2027 Supply Chain Analyst Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236592007?gh_jid=5236592007) — Quincy, Massachusetts, United States
- 🎓 [Winter 2027 Systems Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236599007?gh_jid=5236599007) — Quincy, Massachusetts, United States
- 🎓 [Winter 2027 Technical Program Management Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236571007?gh_jid=5236571007) — Washington, District of Columbia, United States
- 🎓 [Winter 2027 Test & Evaluation Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236583007?gh_jid=5236583007) — Costa Mesa, California, United States
- 🎓 [Winter 2027 Warhead Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236585007?gh_jid=5236585007) — Costa Mesa, California, United States
- [  Senior Advanced Research Scientist ](https://boards.greenhouse.io/andurilindustries/jobs/5206561007?gh_jid=5206561007) — Broomfield, Colorado, United States; Fort Collins, Colorado, United States
- [ CW Production Recruiting Lead](https://boards.greenhouse.io/andurilindustries/jobs/5230544007?gh_jid=5230544007) — Denver, Colorado, United States
- [ Development Test Engineer](https://boards.greenhouse.io/andurilindustries/jobs/4676612007?gh_jid=4676612007) — Costa Mesa, California, United States
- [ FPGA Engineer, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/5147059007?gh_jid=5147059007) — Reston, Virginia, United States
- [ Head of Maintenance Repair & Overhaul](https://boards.greenhouse.io/andurilindustries/jobs/5148720007?gh_jid=5148720007) — Costa Mesa, California, United States
- [ Integration Technician - Structures, Omen](https://boards.greenhouse.io/andurilindustries/jobs/5219410007?gh_jid=5219410007) — Costa Mesa, California, United States
- [ Lead Manufacturing Engineer, Missiles](https://boards.greenhouse.io/andurilindustries/jobs/5137065007?gh_jid=5137065007) — Costa Mesa, California, United States
- [ Low Observables Engineer, RCS](https://boards.greenhouse.io/andurilindustries/jobs/4418353007?gh_jid=4418353007) — Costa Mesa, California, United States
- [ Manufacturing Engineer, Production, Sentry](https://boards.greenhouse.io/andurilindustries/jobs/5085941007?gh_jid=5085941007) — Irvine, California, United States
- [ Manufacturing Test Engineer, Missiles](https://boards.greenhouse.io/andurilindustries/jobs/5254383007?gh_jid=5254383007) — Costa Mesa, California, United States
- [ Manufacturing Test Engineer, Missiles](https://boards.greenhouse.io/andurilindustries/jobs/5254434007?gh_jid=5254434007) — Ashville, Ohio, United States
- [ Propulsion Manufacturing Test Engineer, Missiles](https://boards.greenhouse.io/andurilindustries/jobs/5254363007?gh_jid=5254363007) — Costa Mesa, California, United States
- [ Senior Aerodynamics Engineer, Air Vehicles](https://boards.greenhouse.io/andurilindustries/jobs/4629832007?gh_jid=4629832007) — Costa Mesa, California, United States
- [ Senior Discovery Engineer (Modeling & Simulation) ](https://boards.greenhouse.io/andurilindustries/jobs/5252658007?gh_jid=5252658007) — Boston, Massachusetts, United States; Waltham, Massachusetts, United States
- [ Senior FPGA Engineer, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/4591133007?gh_jid=4591133007) — Reston, Virginia, United States
- [ Senior Security Engineer, Identity](https://boards.greenhouse.io/andurilindustries/jobs/5259074007?gh_jid=5259074007) — Washington, District of Columbia, United States
- [ Senior Supplier Quality Engineer, Mechanical Subassembly / Composites](https://boards.greenhouse.io/andurilindustries/jobs/5134865007?gh_jid=5134865007) — Costa Mesa, California, United States
- [ Senior Technical Recruiter, Contractor Mission Systems](https://boards.greenhouse.io/andurilindustries/jobs/5014749007?gh_jid=5014749007) — Costa Mesa, California, United States; Waltham, Massachusetts, United States
- [ Software Engineer, Discovery](https://boards.greenhouse.io/andurilindustries/jobs/5242907007?gh_jid=5242907007) — Boston, Massachusetts, United States; Costa Mesa, California, United States; Washington, District of Columbia, United States
- [ VP Production, Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5173257007?gh_jid=5173257007) — Costa Mesa, California, United States
- [(HVAC Specialist) Technical Operations Engineer - Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5200126007?gh_jid=5200126007) — Costa Mesa, California, United States
- [(Pipeline) Structural Analyst, Space Emerging Talent](https://boards.greenhouse.io/andurilindustries/jobs/5239598007?gh_jid=5239598007) — Costa Mesa, California, United States
- [2026 Early Career Electrical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/4802172007?gh_jid=4802172007) — Costa Mesa, California, United States; Fort Collins, Colorado, United States
- [2026 Early Career Manufacturing Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5176254007?gh_jid=5176254007) — Costa Mesa, California, United States; Irvine, California, United States; Santa Ana, California, United States
- [2026 Early Career Mechanical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/4802167007?gh_jid=4802167007) — Costa Mesa, California, United States
- [2026 Early Career Software Engineer](https://boards.greenhouse.io/andurilindustries/jobs/4802146007?gh_jid=4802146007) — Atlanta, Georgia, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Seattle, Washington, United States
- [2026 Financial Analyst I, AD&S](https://boards.greenhouse.io/andurilindustries/jobs/5213031007?gh_jid=5213031007) — Costa Mesa, California, United States
- [2026 Junior Analyst, Threat Intelligence](https://boards.greenhouse.io/andurilindustries/jobs/5233074007?gh_jid=5233074007) — Costa Mesa, California, United States
- [2027 Early Career Electrical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5136925007?gh_jid=5136925007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- [2027 Early Career Firmware Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5246141007?gh_jid=5246141007) — Costa Mesa, California, United States
- [2027 Early Career Flight Software Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5228868007?gh_jid=5228868007) — Costa Mesa, California, United States
- [2027 Early Career Flight Test Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5246225007?gh_jid=5246225007) — Costa Mesa, California, United States
- [2027 Early Career Industrial Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5236921007?gh_jid=5236921007) — Ashville, Ohio, United States
- [2027 Early Career Manufacturing Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5136970007?gh_jid=5136970007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Seattle, Washington, United States
- [2027 Early Career Mechanical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5136984007?gh_jid=5136984007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- [2027 Early Career Software Engineer ](https://boards.greenhouse.io/andurilindustries/jobs/5162263007?gh_jid=5162263007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- [2027 Early Career Technical Operations Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5255914007?gh_jid=5255914007) — London, England, United Kingdom
- [2nd Shift Quality Inspector](https://boards.greenhouse.io/andurilindustries/jobs/5201654007?gh_jid=5201654007) — Atlanta, Georgia, United States
- [Acceptance Test Procedure Technician, Roadrunner](https://boards.greenhouse.io/andurilindustries/jobs/5116801007?gh_jid=5116801007) — Ashville, Ohio, United States
- [Account Director, Maritime](https://boards.greenhouse.io/andurilindustries/jobs/5210043007?gh_jid=5210043007) — Sydney, New South Wales, Australia
- [Account Director, Maritime](https://boards.greenhouse.io/andurilindustries/jobs/5210045007?gh_jid=5210045007) — Canberra, Australian Capital Territory, Australia
- [Actuation Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5217256007?gh_jid=5217256007) — Costa Mesa, California, United States
- [AD&S, Air Vehicle Software Systems Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5131822007?gh_jid=5131822007) — Costa Mesa, California, United States
- [Additive Manufacturing Tech, FDM (3D Print)](https://boards.greenhouse.io/andurilindustries/jobs/5200196007?gh_jid=5200196007) — Costa Mesa, California, United States
- [Aerodynamics Engineer, Air Vehicles](https://boards.greenhouse.io/andurilindustries/jobs/5000486007?gh_jid=5000486007) — Costa Mesa, California, United States
- [Aerodynamics Engineer, Hypersonic Air Vehicles](https://boards.greenhouse.io/andurilindustries/jobs/5032351007?gh_jid=5032351007) — Costa Mesa, California, United States
- [AFSIM Operations Analyst, Mission Engineering, Air Dominance & Strike, Active Clearance](https://boards.greenhouse.io/andurilindustries/jobs/5103907007?gh_jid=5103907007) — Ashville, Ohio, United States; Costa Mesa, California, United States
- [Agentic AI Engineer, Automation](https://boards.greenhouse.io/andurilindustries/jobs/5219383007?gh_jid=5219383007) — Costa Mesa, California, United States
- [AI Solutions Engineer, Talent Acquisition](https://boards.greenhouse.io/andurilindustries/jobs/5171942007?gh_jid=5171942007) — Costa Mesa, California, United States
- [AI Solutions Engineer, Talent Acquisition](https://boards.greenhouse.io/andurilindustries/jobs/5173388007?gh_jid=5173388007) — Boston, Massachusetts, United States
- [AI Solutions Engineer, Talent Acquisition](https://boards.greenhouse.io/andurilindustries/jobs/5173534007?gh_jid=5173534007) — Seattle, Washington, United States
- [AI Systems Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5225164007?gh_jid=5225164007) — Santa Ana, California, United States
- [Air Vehicle Lead](https://boards.greenhouse.io/andurilindustries/jobs/5221660007?gh_jid=5221660007) — Costa Mesa, California, United States
- [Air Vehicle Lead, High Speed Missiles](https://boards.greenhouse.io/andurilindustries/jobs/5211965007?gh_jid=5211965007) — Costa Mesa, California, United States
- [Air Vehicle Systems Engineer, Hardware Verification, Integration & Validation](https://boards.greenhouse.io/andurilindustries/jobs/5131979007?gh_jid=5131979007) — Costa Mesa, California, United States
- [Air Vehicle Systems Verification Lead](https://boards.greenhouse.io/andurilindustries/jobs/5131984007?gh_jid=5131984007) — Costa Mesa, California, United States
- [Air-Vehicle Multidisciplinary Design Analysis and Optimization (MDAO) Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5132442007?gh_jid=5132442007) — Costa Mesa, California, United States
- [Algorithm Developer, Tracking Systems](https://boards.greenhouse.io/andurilindustries/jobs/5226940007?gh_jid=5226940007) — Broomfield, Colorado, United States; Fort Collins, Colorado, United States
- [Algorithm Engineer, Tracking Systems](https://boards.greenhouse.io/andurilindustries/jobs/5226941007?gh_jid=5226941007) — Broomfield, Colorado, United States; Fort Collins, Colorado, United States
- [Altius - Product Sourcing Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5140464007?gh_jid=5140464007) — Atlanta, Georgia, United States
- [Altius - Product Sourcing Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5223799007?gh_jid=5223799007) — Costa Mesa, California, United States
- [Altius - Senior Product Sourcing Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5205961007?gh_jid=5205961007) — Costa Mesa, California, United States
- [Analytics Engineer, Hardware Test](https://boards.greenhouse.io/andurilindustries/jobs/4768437007?gh_jid=4768437007) — Costa Mesa, California, United States
- [Analytics Engineer, Sentry](https://boards.greenhouse.io/andurilindustries/jobs/5226536007?gh_jid=5226536007) — Irvine, California, United States
- [Antenna RF Engineer, EW](https://boards.greenhouse.io/andurilindustries/jobs/5231092007?gh_jid=5231092007) — Costa Mesa, California, United States
- [Applied LLM Systems Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5197253007?gh_jid=5197253007) — Costa Mesa, California, United States
- [Asset Improvement Lead](https://boards.greenhouse.io/andurilindustries/jobs/5156362007?gh_jid=5156362007) — Costa Mesa, California, United States
- [Associate Director, Business Development, Air Defense](https://boards.greenhouse.io/andurilindustries/jobs/5176542007?gh_jid=5176542007) — Washington, District of Columbia, United States
- [Associate Director, Business Development, Air Defense](https://boards.greenhouse.io/andurilindustries/jobs/5178152007?gh_jid=5178152007) — Costa Mesa, California, United States
- [Associate Director, Corporate Planning & Operations](https://boards.greenhouse.io/andurilindustries/jobs/4964602007?gh_jid=4964602007) — Costa Mesa, California, United States
- [Associate Director, Kitchen Operations - West Coast](https://boards.greenhouse.io/andurilindustries/jobs/5256115007?gh_jid=5256115007) — Costa Mesa, California, United States
- [Associate Director, Space Growth](https://boards.greenhouse.io/andurilindustries/jobs/5133374007?gh_jid=5133374007) — Chantilly, Virginia, United States
- [Associate Director, Strategic Execution - TRS](https://boards.greenhouse.io/andurilindustries/jobs/5222624007?gh_jid=5222624007) — Costa Mesa, California, United States
- [Associate Facilities Manager](https://boards.greenhouse.io/andurilindustries/jobs/5156676007?gh_jid=5156676007) — Costa Mesa, California, United States
- [Associate People Business Partner](https://boards.greenhouse.io/andurilindustries/jobs/4855853007?gh_jid=4855853007) — Costa Mesa, California, United States
- [Associate Workplace Manager](https://boards.greenhouse.io/andurilindustries/jobs/5235397007?gh_jid=5235397007) — Costa Mesa, California, United States
- [Associate Workplace Manager](https://boards.greenhouse.io/andurilindustries/jobs/5256121007?gh_jid=5256121007) — Ashville, Ohio, United States
- [Associate, Business & Revenue Operations, Air Defense](https://boards.greenhouse.io/andurilindustries/jobs/5214320007?gh_jid=5214320007) — Irvine, California, United States
- [Automation & Torque Tooling Technician](https://boards.greenhouse.io/andurilindustries/jobs/5227022007?gh_jid=5227022007) — Costa Mesa, California, United States
- [Automation Engineer, General](https://boards.greenhouse.io/andurilindustries/jobs/5239028007?gh_jid=5239028007) — Costa Mesa, California, United States
- [Automation Engineer, Manufacturing Automation](https://boards.greenhouse.io/andurilindustries/jobs/5234628007?gh_jid=5234628007) — Costa Mesa, California, United States
- [Automation Technician 2nd Shift, Manufacturing Automation  ](https://boards.greenhouse.io/andurilindustries/jobs/5234683007?gh_jid=5234683007) — Costa Mesa, California, United States
- [Automation Technician, Manufacturing Automation  ](https://boards.greenhouse.io/andurilindustries/jobs/5234680007?gh_jid=5234680007) — Costa Mesa, California, United States
- [Automation Test Software Engineer, Manufacturing ](https://boards.greenhouse.io/andurilindustries/jobs/5250595007?gh_jid=5250595007) — Irvine, California, United States
- [AV Systems Administrator](https://boards.greenhouse.io/andurilindustries/jobs/5134986007?gh_jid=5134986007) — Costa Mesa, California, United States
- [Aviation Maintenance Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5115028007?gh_jid=5115028007) — Phoenix, Arizona, United States
- [Battery Test Technician](https://boards.greenhouse.io/andurilindustries/jobs/5130695007?gh_jid=5130695007) — Costa Mesa, California, United States
- [BOM Sourcing Engineer, Intelligence Systems & Space (Active Clearance)](https://boards.greenhouse.io/andurilindustries/jobs/5029722007?gh_jid=5029722007) — Costa Mesa, California, United States
- [BOM Sourcing Engineer, Supply Chain](https://boards.greenhouse.io/andurilindustries/jobs/5174509007?gh_jid=5174509007) — Costa Mesa, California, United States
- [Business Operations Associate](https://boards.greenhouse.io/andurilindustries/jobs/4951316007?gh_jid=4951316007) — Costa Mesa, California, United States
- [Business Operations Associate - Technical Projects](https://boards.greenhouse.io/andurilindustries/jobs/4951318007?gh_jid=4951318007) — Costa Mesa, California, United States
- [Business Operations Associate, Factory Systems](https://boards.greenhouse.io/andurilindustries/jobs/5227806007?gh_jid=5227806007) — Costa Mesa, California, United States
- [Business Operations Associate, Production](https://boards.greenhouse.io/andurilindustries/jobs/4619191007?gh_jid=4619191007) — Costa Mesa, California, United States
- [Business Operations Engineer, Air Dominance & Strike ](https://boards.greenhouse.io/andurilindustries/jobs/5111193007?gh_jid=5111193007) — Costa Mesa, California, United States
- [Business Operations Lead](https://boards.greenhouse.io/andurilindustries/jobs/4951325007?gh_jid=4951325007) — Costa Mesa, California, United States
- [Business Operations Lead - Technical Projects](https://boards.greenhouse.io/andurilindustries/jobs/5117374007?gh_jid=5117374007) — Costa Mesa, California, United States
- [Business Operations, Air Dominance & Strike](https://boards.greenhouse.io/andurilindustries/jobs/4790841007?gh_jid=4790841007) — Costa Mesa, California, United States
- [Business Operations, Air Dominance & Strike](https://boards.greenhouse.io/andurilindustries/jobs/5155193007?gh_jid=5155193007) — Costa Mesa, California, United States
- [Business Operations, Anduril](https://boards.greenhouse.io/andurilindustries/jobs/5219004007?gh_jid=5219004007) — Costa Mesa, California, United States
- [Business Operations, Production](https://boards.greenhouse.io/andurilindustries/jobs/5195711007?gh_jid=5195711007) — Costa Mesa, California, United States
- [Business Operations, Production](https://boards.greenhouse.io/andurilindustries/jobs/5236241007?gh_jid=5236241007) — Washington, District of Columbia, United States
- [Business Operations, Strategic Supply Chain](https://boards.greenhouse.io/andurilindustries/jobs/5165934007?gh_jid=5165934007) — Costa Mesa, California, United States
- [Business Process Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5206039007?gh_jid=5206039007) — Atlanta, Georgia, United States
- [Buyer](https://boards.greenhouse.io/andurilindustries/jobs/5163565007?gh_jid=5163565007) — Quonset, Rhode Island, United States
- [Buyer, Advanced Effects](https://boards.greenhouse.io/andurilindustries/jobs/5219013007?gh_jid=5219013007) — Costa Mesa, California, United States
- [Buyer, Autonomous Airpower Hardware Procurement](https://boards.greenhouse.io/andurilindustries/jobs/4802276007?gh_jid=4802276007) — Costa Mesa, California, United States
- [Buyer, Core Tech](https://boards.greenhouse.io/andurilindustries/jobs/5233232007?gh_jid=5233232007) — Costa Mesa, California, United States
- [Buyer, Dive-XL](https://boards.greenhouse.io/andurilindustries/jobs/5245718007?gh_jid=5245718007) — Quonset, Rhode Island, United States
- [Buyer, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/5252055007?gh_jid=5252055007) — Costa Mesa, California, United States
- [Buyer, Mission Systems](https://boards.greenhouse.io/andurilindustries/jobs/5222695007?gh_jid=5222695007) — Costa Mesa, California, United States
- [Buyer/Planner](https://boards.greenhouse.io/andurilindustries/jobs/5243263007?gh_jid=5243263007) — Quincy, Massachusetts, United States
- [Buyer/Planner](https://boards.greenhouse.io/andurilindustries/jobs/5248570007?gh_jid=5248570007) — Quonset, Rhode Island, United States
- [C++ Engineer, High-Performance Systems](https://boards.greenhouse.io/andurilindustries/jobs/5226945007?gh_jid=5226945007) — Broomfield, Colorado, United States; Fort Collins, Colorado, United States
- [C++ Mission Software Engineer, Mission Autonomy](https://boards.greenhouse.io/andurilindustries/jobs/5125189007?gh_jid=5125189007) — Costa Mesa, California, United States; Seattle, Washington, United States; Washington, District of Columbia, United States
- [C2 Mission Operations Manager, JIATF](https://boards.greenhouse.io/andurilindustries/jobs/5216132007?gh_jid=5216132007) — Irvine, California, United States
- [CAD Administrator](https://boards.greenhouse.io/andurilindustries/jobs/5256520007?gh_jid=5256520007) — Costa Mesa, California, United States
- [CAD Administrator](https://boards.greenhouse.io/andurilindustries/jobs/5256522007?gh_jid=5256522007) — Seattle, Washington, United States
- [CAD Administrator](https://boards.greenhouse.io/andurilindustries/jobs/5256524007?gh_jid=5256524007) — Mountain View, California, United States
- [CAD Designer, Maritime Production](https://boards.greenhouse.io/andurilindustries/jobs/5231433007?gh_jid=5231433007) — Santa Ana, California, United States
- [CAD Drafter](https://boards.greenhouse.io/andurilindustries/jobs/5247471007?gh_jid=5247471007) — Costa Mesa, California, United States
- [Calibration Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5201431007?gh_jid=5201431007) — Costa Mesa, California, United States
- [Camera Test Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5196583007?gh_jid=5196583007) — Lexington, Massachusetts, United States
- [Chief Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5159733007?gh_jid=5159733007) — Costa Mesa, California, United States
- [Chief Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5194664007?gh_jid=5194664007) — Costa Mesa, California, United States
- [Chief Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5252765007?gh_jid=5252765007) — Hudson, New Hampshire, United States
- [Chief Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5252767007?gh_jid=5252767007) — Goleta, California, United States
- [Chief Engineer - Tactical Effects](https://boards.greenhouse.io/andurilindustries/jobs/5254633007?gh_jid=5254633007) — Costa Mesa, California, United States
- [Chief Engineer, Advanced Effects (Hypersonics) ](https://boards.greenhouse.io/andurilindustries/jobs/5252457007?gh_jid=5252457007) — Costa Mesa, California, United States
- [Chief Engineer, Advanced Effects (Missiles) ](https://boards.greenhouse.io/andurilindustries/jobs/5226623007?gh_jid=5226623007) — Costa Mesa, California, United States
- [Chief Engineer, Air Defense, Middle East Programs](https://boards.greenhouse.io/andurilindustries/jobs/5248044007?gh_jid=5248044007) — Huntsville, Alabama, United States; Irvine, California, United States; Seattle, Washington, United States; Washington, District of Columbia, United States
- [Chief Engineer, Autonomous Flight](https://boards.greenhouse.io/andurilindustries/jobs/5158222007?gh_jid=5158222007) — Costa Mesa, California, United States; Seattle, Washington, United States; Washington, District of Columbia, United States
- [Chief Engineer, Conventional ISR](https://boards.greenhouse.io/andurilindustries/jobs/5172075007?gh_jid=5172075007) — Costa Mesa, California, United States
- [Chief Engineer, Copperhead](https://boards.greenhouse.io/andurilindustries/jobs/5251222007?gh_jid=5251222007) — Quincy, Massachusetts, United States
- [Chief Engineer, Dive-LD](https://boards.greenhouse.io/andurilindustries/jobs/5251191007?gh_jid=5251191007) — Quincy, Massachusetts, United States
- [Chief Engineer, EW](https://boards.greenhouse.io/andurilindustries/jobs/5155026007?gh_jid=5155026007) — Costa Mesa, California, United States
- [Chief Engineer, FQ-44 Fury](https://boards.greenhouse.io/andurilindustries/jobs/5081020007?gh_jid=5081020007) — Costa Mesa, California, United States
- [Chief Engineer, Fury Advanced Concepts](https://boards.greenhouse.io/andurilindustries/jobs/5218065007?gh_jid=5218065007) — Costa Mesa, California, United States
- [Chief Engineer, Fury Advanced Development & Prototyping](https://boards.greenhouse.io/andurilindustries/jobs/5060066007?gh_jid=5060066007) — Costa Mesa, California, United States
- [Chief Engineer, Intel Systems](https://boards.greenhouse.io/andurilindustries/jobs/5032221007?gh_jid=5032221007) — Reston, Virginia, United States
- [Chief Engineer, Maritime Integrated Systems](https://boards.greenhouse.io/andurilindustries/jobs/5103884007?gh_jid=5103884007) — Quincy, Massachusetts, United States
- [Chief Engineer, Maritime Integrated Systems](https://boards.greenhouse.io/andurilindustries/jobs/5199934007?gh_jid=5199934007) — Boston, Massachusetts, United States
- [Chief Engineer, Navy Airpower](https://boards.greenhouse.io/andurilindustries/jobs/5172083007?gh_jid=5172083007) — Costa Mesa, California, United States
- [Chief Engineer, Next Generation ISR](https://boards.greenhouse.io/andurilindustries/jobs/5173600007?gh_jid=5173600007) — Costa Mesa, California, United States
- [Chief Engineer, Radar](https://boards.greenhouse.io/andurilindustries/jobs/5226654007?gh_jid=5226654007) — Broomfield, Colorado, United States; Fort Collins, Colorado, United States
- [Chief Engineer, Radar](https://boards.greenhouse.io/andurilindustries/jobs/5226685007?gh_jid=5226685007) — Costa Mesa, California, United States
- [Chief Engineer, Software-Defined Vehicle Platform](https://boards.greenhouse.io/andurilindustries/jobs/5149344007?gh_jid=5149344007) — Costa Mesa, California, United States
- [Chief Engineers, Advanced Aircraft Programs](https://boards.greenhouse.io/andurilindustries/jobs/5087403007?gh_jid=5087403007) — Costa Mesa, California, United States
- [Chief Information Security Officer](https://boards.greenhouse.io/andurilindustries/jobs/5241292007?gh_jid=5241292007) — Costa Mesa, California, United States
- [Chief of Staff, Production](https://boards.greenhouse.io/andurilindustries/jobs/5251746007?gh_jid=5251746007) — Costa Mesa, California, United States
- [Circuit Designer, Space Special Programs](https://boards.greenhouse.io/andurilindustries/jobs/5208572007?gh_jid=5208572007) — Chantilly, Virginia, United States; Herndon, Virginia, United States
- [Classified System Administrator (Active Clearance), Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/5160343007?gh_jid=5160343007) — Reston, Virginia, United States
- [Cloud Deployment Engineer, Space ](https://boards.greenhouse.io/andurilindustries/jobs/5016027007?gh_jid=5016027007) — Costa Mesa, California, United States
- [CNC Oxy/Plasma Programmer, Maritime](https://boards.greenhouse.io/andurilindustries/jobs/5256802007?gh_jid=5256802007) — Santa Ana, California, United States
- [CNC Plasma Cutting Technician, Maritime](https://boards.greenhouse.io/andurilindustries/jobs/5253204007?gh_jid=5253204007) — Santa Ana, California, United States
- [CNC Programmer/Operator](https://boards.greenhouse.io/andurilindustries/jobs/5179736007?gh_jid=5179736007) — Morrisville, North Carolina, United States
- [Commercial HVAC/R & Mechanical Systems Technician, Maritime](https://boards.greenhouse.io/andurilindustries/jobs/5166928007?gh_jid=5166928007) — Santa Ana, California, United States
- [Communications Manager, Maneuver Dominance](https://boards.greenhouse.io/andurilindustries/jobs/5221700007?gh_jid=5221700007) — Washington, District of Columbia, United States
- [Compliance Project Manager](https://boards.greenhouse.io/andurilindustries/jobs/5223373007?gh_jid=5223373007) — Costa Mesa, California, United States
- [Composite Technician, Second Shift](https://boards.greenhouse.io/andurilindustries/jobs/5175477007?gh_jid=5175477007) — Morrisville, North Carolina, United States
- [Compute Systems Architect - Expeditionary AI/HPC Data Centers](https://boards.greenhouse.io/andurilindustries/jobs/5183431007?gh_jid=5183431007) — Costa Mesa, California, United States
- [Computer Vision Engineer, Space](https://boards.greenhouse.io/andurilindustries/jobs/5016001007?gh_jid=5016001007) — Costa Mesa, California, United States
- [Computer Vision Engineer, Space](https://boards.greenhouse.io/andurilindustries/jobs/5016334007?gh_jid=5016334007) — Washington, District of Columbia, United States
- [Configuration Design Engineer ](https://boards.greenhouse.io/andurilindustries/jobs/5208194007?gh_jid=5208194007) — Costa Mesa, California, United States
- [Configuration Manager](https://boards.greenhouse.io/andurilindustries/jobs/5197650007?gh_jid=5197650007) — Dublin, Dublin, Ireland
- [Configuration Manager ](https://boards.greenhouse.io/andurilindustries/jobs/5187511007?gh_jid=5187511007) — Costa Mesa, California, United States
- [Configuration Manager ](https://boards.greenhouse.io/andurilindustries/jobs/5188290007?gh_jid=5188290007) — Ashville, Ohio, United States
- [Connectivity Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5107257007?gh_jid=5107257007) — Costa Mesa, California, United States
- [Construction Project Manager](https://boards.greenhouse.io/andurilindustries/jobs/5225224007?gh_jid=5225224007) — Ashville, Ohio, United States
- [Construction Project Manager, Asset Improvements ](https://boards.greenhouse.io/andurilindustries/jobs/5183350007?gh_jid=5183350007) — Boston, Massachusetts, United States
- [Construction Systems Specialist](https://boards.greenhouse.io/andurilindustries/jobs/5124525007?gh_jid=5124525007) — Costa Mesa, California, United States
- [Contract Recruiter, Production (Technicians)](https://boards.greenhouse.io/andurilindustries/jobs/5236226007?gh_jid=5236226007) — Ashville, Ohio, United States
- [Contracts Manager](https://boards.greenhouse.io/andurilindustries/jobs/5185207007?gh_jid=5185207007) — Washington, District of Columbia, United States
- [Contracts Manager](https://boards.greenhouse.io/andurilindustries/jobs/5200578007?gh_jid=5200578007) — Reston, Virginia, United States
- [Contracts Manager](https://boards.greenhouse.io/andurilindustries/jobs/5219857007?gh_jid=5219857007) — Fort Collins, Colorado, United States
- [Contracts Manager ](https://boards.greenhouse.io/andurilindustries/jobs/5184594007?gh_jid=5184594007) — Costa Mesa, California, United States
- [Controls Engineer 2nd shift, Manufacturing Automation ](https://boards.greenhouse.io/andurilindustries/jobs/5234541007?gh_jid=5234541007) — Costa Mesa, California, United States
- [Controls Engineer, Manufacturing Automation](https://boards.greenhouse.io/andurilindustries/jobs/5234565007?gh_jid=5234565007) — Ashville, Ohio, United States
- [Controls Engineer, Manufacturing Automation ](https://boards.greenhouse.io/andurilindustries/jobs/5234512007?gh_jid=5234512007) — Costa Mesa, California, United States
- [Controls Engineer, Manufacturing Automation ](https://boards.greenhouse.io/andurilindustries/jobs/5234556007?gh_jid=5234556007) — Costa Mesa, California, United States
- [Controls Engineer, Rocket Motor Systems](https://boards.greenhouse.io/andurilindustries/jobs/5234582007?gh_jid=5234582007) — McHenry, Mississippi, United States
- [Controls SCADA Engineer, Rocket Motor Systems](https://boards.greenhouse.io/andurilindustries/jobs/5234589007?gh_jid=5234589007) — McHenry, Mississippi, United States
- [Corporate Facility Security Officer](https://boards.greenhouse.io/andurilindustries/jobs/5231329007?gh_jid=5231329007) — Costa Mesa, California, United States

_…truncated at 400 rows (3276 total)._

</details>
<!-- REQCON:END -->
