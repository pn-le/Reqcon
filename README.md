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
**Last scan:** 2026-08-12 07:39 EDT · 8 boards · 70 new · 56 removed

✅ Lila Sciences · ✅ BillionToOne · ✅ Anduril · ✅ Formlabs · ✅ STR · ✅ Draper · ✅ MERL (Mitsubishi Electric Research Labs) · ✅ Ubicept

### New this week

| Company | Role | Location | First seen |
|---|---|---|---|
| 🎓 Formlabs | [Social Media Content Intern (Fall 2026)](https://careers.formlabs.com/job/8114569/apply/?gh_jid=8114569) | Somerville, MA | 2026-08-10 |
| 🎓 MERL (Mitsubishi Electric Research Labs) | [OR0313: Internship - Foundation Models for Humanoid Robots](https://www.merl.com/employment/internship-openings#OR0313) | — | 2026-08-10 |
| 🎓 MERL (Mitsubishi Electric Research Labs) | [CI0314: Internship - Embodied AI & Humanoid Robotics](https://www.merl.com/employment/internship-openings#CI0314) | — | 2026-08-07 |
| 🎓 MERL (Mitsubishi Electric Research Labs) | [MS0315: Internship - Embedded Systems and Control](https://www.merl.com/employment/internship-openings#MS0315) | — | 2026-08-07 |
| 🎓 Draper | [Embedded Quality & Fielded Systems Intern](https://draper.wd5.myworkdayjobs.com/en-US/Draper_Careers/job/Cambridge-MA/Embedded-Quality---Fielded-Systems-Intern_JR002718) | Cambridge, MA | 2026-08-06 |
| 🎓 Draper | [Mechanical Engineering & System Packaging Intern](https://draper.wd5.myworkdayjobs.com/en-US/Draper_Careers/job/Cambridge-MA/Mechanical-Engineering---System-Packaging-Intern_JR002767) | 2 Locations | 2026-08-06 |
| 🎓 Draper | [Threat Management Co-Op (Fall 2026)](https://draper.wd5.myworkdayjobs.com/en-US/Draper_Careers/job/Reston-VA/Threat-Management-Co-Op--Fall-2026-_JR002768) | Reston, VA | 2026-08-06 |
| 🎓 Formlabs | [Social Media Engineering Intern (Fall 2026)](https://careers.formlabs.com/job/8108754/apply/?gh_jid=8108754) | Somerville, MA | 2026-08-06 |
| Anduril | [2nd Shift Quality Inspector](https://boards.greenhouse.io/andurilindustries/jobs/5201654007?gh_jid=5201654007) | Atlanta, Georgia, United States | 2026-08-12 |
| Anduril | [Customer Success Manager - AIRS](https://boards.greenhouse.io/andurilindustries/jobs/5209733007?gh_jid=5209733007) | Hudson, New Hampshire, United States | 2026-08-12 |
| Anduril | [Director of Advanced Design ](https://boards.greenhouse.io/andurilindustries/jobs/5209103007?gh_jid=5209103007) | Costa Mesa, California, United States | 2026-08-12 |
| Anduril | [Director, Manufacturing Maintenance](https://boards.greenhouse.io/andurilindustries/jobs/5173437007?gh_jid=5173437007) | Ashville, Ohio, United States; Costa Mesa, California, United States | 2026-08-12 |
| Anduril | [Director, Supply Chain](https://boards.greenhouse.io/andurilindustries/jobs/5200299007?gh_jid=5200299007) | Ashville, Ohio, United States | 2026-08-12 |
| Anduril | [Division Operations, Tactical Recon & Strike ](https://boards.greenhouse.io/andurilindustries/jobs/5187833007?gh_jid=5187833007) | Costa Mesa, California, United States | 2026-08-12 |
| Anduril | [Electronics Test Technician](https://boards.greenhouse.io/andurilindustries/jobs/5209239007?gh_jid=5209239007) | Lexington, Massachusetts, United States | 2026-08-12 |
| Anduril | [Flight Test Engineering Lead](https://boards.greenhouse.io/andurilindustries/jobs/5198230007?gh_jid=5198230007) | Sydney, New South Wales, Australia | 2026-08-12 |
| Anduril | [Integration and Test Technician](https://boards.greenhouse.io/andurilindustries/jobs/5160388007?gh_jid=5160388007) | Costa Mesa, California, United States | 2026-08-12 |
| Anduril | [Lead Manufacturing Engineer, Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5209883007?gh_jid=5209883007) | Santa Ana, California, United States | 2026-08-12 |
| Anduril | [Low Observables Technician](https://boards.greenhouse.io/andurilindustries/jobs/5198610007?gh_jid=5198610007) | Ashville, Ohio, United States | 2026-08-12 |
| Anduril | [Mechanical Engineer, Support System](https://boards.greenhouse.io/andurilindustries/jobs/5182025007?gh_jid=5182025007) | Costa Mesa, California, United States | 2026-08-12 |
| Anduril | [Micro-electronics Technician](https://boards.greenhouse.io/andurilindustries/jobs/5209236007?gh_jid=5209236007) | Lexington, Massachusetts, United States | 2026-08-12 |
| Anduril | [Mission Operations Manager, Europe](https://boards.greenhouse.io/andurilindustries/jobs/5207809007?gh_jid=5207809007) | London, England, United Kingdom | 2026-08-12 |
| Anduril | [Principal Design Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5208966007?gh_jid=5208966007) | Chantilly, Virginia, United States; Herndon, Virginia, United States | 2026-08-12 |
| Anduril | [Production Lead](https://boards.greenhouse.io/andurilindustries/jobs/5194924007?gh_jid=5194924007) | Costa Mesa, California, United States | 2026-08-12 |
| Anduril | [Production Test Technician](https://boards.greenhouse.io/andurilindustries/jobs/5209238007?gh_jid=5209238007) | Lexington, Massachusetts, United States | 2026-08-12 |
| Anduril | [SCADA Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5155901007?gh_jid=5155901007) | Costa Mesa, California, United States | 2026-08-12 |
| Anduril | [SCADA Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5192601007?gh_jid=5192601007) | Ashville, Ohio, United States | 2026-08-12 |
| Anduril | [Senior Deployed Software Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5209208007?gh_jid=5209208007) | Lexington, Massachusetts, United States | 2026-08-12 |
| Anduril | [Senior Engineer, Integration & Test ](https://boards.greenhouse.io/andurilindustries/jobs/5095158007?gh_jid=5095158007) | Llanbedr, Wales, United Kingdom | 2026-08-12 |
| Anduril | [Senior Maintenance Technician, 2nd Shift](https://boards.greenhouse.io/andurilindustries/jobs/5209899007?gh_jid=5209899007) | Costa Mesa, California, United States | 2026-08-12 |

…and 281 more — see the [latest digest](reports/reqcon-2026-08-12.md).

<details>
<summary>All tracked postings (3008)</summary>

**Lila Sciences** (127)
- 🎓 [Co-Op, Autonomous SEM](https://job-boards.greenhouse.io/lilasciences/jobs/4300246009) — Cambridge, MA USA
- 🎓 [Co-Op, Data Extraction](https://job-boards.greenhouse.io/lilasciences/jobs/4280811009) — Cambridge, MA USA
- 🎓 [Co-Op, Enterprise Go-to-Market](https://job-boards.greenhouse.io/lilasciences/jobs/4332041009) — Cambridge, MA USA
- 🎓 [Co-Op, ML Scientist for Biology](https://job-boards.greenhouse.io/lilasciences/jobs/4294212009) — San Francisco, CA USA
- 🎓 [Co-Op, ML Scientist for Protein Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4289387009) — San Francisco, CA USA
- 🎓 [Co-Op, Next Gen Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4289960009) — Cambridge, MA USA
- 🎓 [Co-Op, Software Product Management](https://job-boards.greenhouse.io/lilasciences/jobs/4286512009) — Cambridge, MA USA
- [(Senior) Director, Portfolio Strategy, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4258093009) — Cambridge, MA USA
- [AI Residency Program, Material Science (2026 Cohort)](https://job-boards.greenhouse.io/lilasciences/jobs/4031379009) — Cambridge, MA USA
- [Associate Director / Director, Customer Program Management, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4184652009) — Cambridge, MA USA
- [Associate Director / Director, Customer Program Management, Physical Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4290011009) — Cambridge, MA USA
- [Associate Director/Director, Commercial Counsel ](https://job-boards.greenhouse.io/lilasciences/jobs/4174259009) — Cambridge, MA USA; San Francisco, CA USA
- [Associate Scientist/Scientist I, Protein Science Developability](https://job-boards.greenhouse.io/lilasciences/jobs/4299967009) — Cambridge, MA USA
- [Chemistry Technical Program Manager](https://job-boards.greenhouse.io/lilasciences/jobs/4204188009) — Cambridge, MA USA
- [Chief of Staff to the CEO](https://job-boards.greenhouse.io/lilasciences/jobs/4285660009) — Cambridge, MA USA
- [Chief of Staff to the CFO](https://job-boards.greenhouse.io/lilasciences/jobs/4291690009) — Cambridge, MA USA
- [Computational Scientist I/II, Soft Matter Formulations , Complex Fluids](https://job-boards.greenhouse.io/lilasciences/jobs/4327124009) — Cambridge, MA USA
- [Computational Scientist I/II, Soft Matter Formulations, Solids and Melts](https://job-boards.greenhouse.io/lilasciences/jobs/4327126009) — Cambridge, MA USA
- [Contract, Lab Operations Specialist I (2nd shift)](https://job-boards.greenhouse.io/lilasciences/jobs/4246299009) — Cambridge, MA USA
- [Contract, Technical Writer, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4318081009) — Cambridge, MA USA
- [Contractor, Maintenance Engineering Technician I/II](https://job-boards.greenhouse.io/lilasciences/jobs/4274132009) — Cambridge, MA USA
- [Contractor, Site Services Coordinator ](https://job-boards.greenhouse.io/lilasciences/jobs/4338180009) — Cambridge, MA USA
- [Contractor, Support Engineer I, Automation (2nd shift)](https://job-boards.greenhouse.io/lilasciences/jobs/4249657009) — Cambridge, MA USA
- [Contractor, Technical Recruiter](https://job-boards.greenhouse.io/lilasciences/jobs/4313985009) — Cambridge, MA USA
- [Controls Engineer II, Sustaining Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4294210009) — Cambridge, MA USA
- [Director / Senior Director of New Product Planning, Physical Science](https://job-boards.greenhouse.io/lilasciences/jobs/4276938009) — Cambridge, MA USA; San Francisco, CA USA
- [Director / Senior Director, Origins](https://job-boards.greenhouse.io/lilasciences/jobs/4314463009) — Cambridge, MA USA
- [Director / Senior Director, Research Engineering, Life Sciences AI](https://job-boards.greenhouse.io/lilasciences/jobs/4343454009) — San Francisco, CA USA
- [Director of Product, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4048370009) — Cambridge, MA USA
- [Director, Data Platform Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4202443009) — San Francisco, CA USA
- [Director, Discovery Chemistry ](https://job-boards.greenhouse.io/lilasciences/jobs/4192648009) — Cambridge, MA USA
- [Director, Materials AISF Program Lead](https://job-boards.greenhouse.io/lilasciences/jobs/4287216009) — Cambridge, MA USA
- [Director/ Senior Director, Product, Electronic Materials](https://job-boards.greenhouse.io/lilasciences/jobs/4257319009) — Cambridge, MA USA
- [Director/ Senior Director, Product, Materials Chemistry](https://job-boards.greenhouse.io/lilasciences/jobs/4320806009) — Cambridge, MA USA
- [Director/Senior Director, Molecular Discovery](https://job-boards.greenhouse.io/lilasciences/jobs/4273680009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Distinguished Scientist, Small Molecule Therapeutics ](https://job-boards.greenhouse.io/lilasciences/jobs/4291685009) — Cambridge, MA USA
- [Engineer II /Senior Controls Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4311159009) — Cambridge, MA USA
- [Engineer II /Senior Software Engineer, Simulation](https://job-boards.greenhouse.io/lilasciences/jobs/4254265009) — Cambridge, MA USA
- [Executive Assistant](https://job-boards.greenhouse.io/lilasciences/jobs/4335619009) — Cambridge, MA USA
- [Head of Software Product](https://job-boards.greenhouse.io/lilasciences/jobs/4205624009) — Cambridge, MA USA; San Francisco, CA USA
- [Join Our Talent Community](https://job-boards.greenhouse.io/lilasciences/jobs/4070054009) — Cambridge, MA USA; San Francisco, CA USA
- [Lead Recruiter](https://job-boards.greenhouse.io/lilasciences/jobs/4353666009) — Cambridge, MA USA
- [Machine Learning Scientist I/II, Multi-Modal Scientific Reasonings](https://job-boards.greenhouse.io/lilasciences/jobs/4116672009) — Cambridge, MA USA
- [Manager / Senior Manager, Enterprise GTM, Chemicals](https://job-boards.greenhouse.io/lilasciences/jobs/4353659009) — Cambridge, MA USA
- [Manager / Senior Manager, Enterprise GTM, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4251026009) — Cambridge, MA USA
- [Manager / Senior Manager, Enterprise GTM, Materials](https://job-boards.greenhouse.io/lilasciences/jobs/4353656009) — Cambridge, MA USA
- [Manager / Senior Manager, Finance, Fixed Asset Accounting](https://job-boards.greenhouse.io/lilasciences/jobs/4195640009) — Cambridge, MA USA; San Francisco, CA USA
- [Manager / Senior Manager, Product Marketing, Life Science](https://job-boards.greenhouse.io/lilasciences/jobs/4118210009) — Cambridge, MA USA
- [Manager / Senior Manager, Product Marketing, Physical Science](https://job-boards.greenhouse.io/lilasciences/jobs/4118224009) — Cambridge, MA USA
- [Manager, Revenue Accounting](https://job-boards.greenhouse.io/lilasciences/jobs/4195605009) — Cambridge, MA USA
- [Materials Technical Program Manager](https://job-boards.greenhouse.io/lilasciences/jobs/4207843009) — Cambridge, MA USA
- [ML Research Scientist I/II, Multimodal Data Extraction](https://job-boards.greenhouse.io/lilasciences/jobs/4052832009) — Cambridge, MA USA
- [ML Scientist I / II, Foundation Models for Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4222051009) — San Francisco, CA USA
- [ML Scientist I/II, Nucleic Acid Design](https://job-boards.greenhouse.io/lilasciences/jobs/4324969009) — San Francisco, CA USA
- [Operations and Quality Engineer, Sustained Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4277749009) — Cambridge, MA USA
- [Platform Scientist, Soft Materials](https://job-boards.greenhouse.io/lilasciences/jobs/4295120009) — Cambridge, MA USA
- [Portfolio Manager, Government Partnerships (DARPA & ARPA-H)](https://job-boards.greenhouse.io/lilasciences/jobs/4297690009) — Cambridge, MA USA
- [Principal / Senior Principal Scientist, Small Molecule Therapeutics](https://job-boards.greenhouse.io/lilasciences/jobs/4322844009) — Cambridge, MA USA
- [Principal Engineer, AI Security](https://job-boards.greenhouse.io/lilasciences/jobs/4210497009) — Cambridge, MA USA
- [Principal Engineer, Software (Enterprise Platform)](https://job-boards.greenhouse.io/lilasciences/jobs/4247103009) — San Francisco, CA USA
- [Principal Scientist / Associate Director, Agentic AI Research for Materials Science](https://job-boards.greenhouse.io/lilasciences/jobs/4273850009) — Cambridge, MA USA; San Francisco, CA USA
- [Principal Software Engineer, Data](https://job-boards.greenhouse.io/lilasciences/jobs/4250071009) — Cambridge, MA USA; San Francisco, CA USA
- [Principal Software Engineer, Instrument Simulations](https://job-boards.greenhouse.io/lilasciences/jobs/4186530009) — Cambridge, MA USA
- [Principal Technical Program Manager, App](https://job-boards.greenhouse.io/lilasciences/jobs/4087979009) — Cambridge, MA USA
- [Principal, Machine Learning Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4222224009) — San Francisco, CA USA
- [Product Lead, Software/Applied AI](https://job-boards.greenhouse.io/lilasciences/jobs/4182437009) — Cambridge, MA USA; San Francisco, CA USA
- [Research Engineer, Frontier Capabilities](https://job-boards.greenhouse.io/lilasciences/jobs/4031323009) — Cambridge, MA USA; San Francisco, CA USA
- [Research Product Manager, Fine-tuning](https://job-boards.greenhouse.io/lilasciences/jobs/4339607009) — Cambridge, MA USA; San Francisco, CA USA
- [Research Product Manager, Post Training](https://job-boards.greenhouse.io/lilasciences/jobs/4310498009) — Cambridge, MA USA; San Francisco, CA USA
- [Research Scientist, Computational Condensed Matter Physics](https://job-boards.greenhouse.io/lilasciences/jobs/4324886009) — Cambridge, MA USA
- [Research Scientist, Frontier Capabilities ](https://job-boards.greenhouse.io/lilasciences/jobs/4031326009) — Cambridge, MA USA; San Francisco, CA USA
- [Scientist I/II, mRNA Translation Dynamics ](https://job-boards.greenhouse.io/lilasciences/jobs/4204230009) — Cambridge, MA USA
- [Scientist I/II, Organic Chemistry](https://job-boards.greenhouse.io/lilasciences/jobs/4192801009) — Cambridge, MA USA
- [Scientist I/II, Process Chemistry](https://job-boards.greenhouse.io/lilasciences/jobs/4192775009) — Cambridge, MA USA
- [Scientist II / Senior ML Scientist, Cofolding and Structure-Aware ML](https://job-boards.greenhouse.io/lilasciences/jobs/4340151009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Scientist II / Senior ML Scientist, Data-Efficient Learning for Drug Discovery](https://job-boards.greenhouse.io/lilasciences/jobs/4340147009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Scientist II/Senior Characterization Scientist,  Condensed Matter](https://job-boards.greenhouse.io/lilasciences/jobs/4246305009) — Cambridge, MA USA
- [Scientist II/Senior Scientist, Computational Biophysics](https://job-boards.greenhouse.io/lilasciences/jobs/4340155009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Scientist II/Senior Scientist, Computational Chemistry, Drug Discovery](https://job-boards.greenhouse.io/lilasciences/jobs/4340153009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Scientist, Epitaxial Thin Film Synthesis](https://job-boards.greenhouse.io/lilasciences/jobs/4253548009) — Cambridge, MA USA
- [Senior / Engineer II, AI Lab Research Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4029507009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior / Principal ML Scientist, Foundation Models for Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4222034009) — San Francisco, CA USA
- [Senior / Staff Machine Learning Engineer, Applied AI](https://job-boards.greenhouse.io/lilasciences/jobs/4302917009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior Automated Systems Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4110339009) — Cambridge, MA USA
- [Senior Director / Vice President, Chemistry Experiment ](https://job-boards.greenhouse.io/lilasciences/jobs/4300718009) — Cambridge, MA USA
- [Senior Director, Software Development, Test Automation](https://job-boards.greenhouse.io/lilasciences/jobs/4294875009) — San Francisco, CA USA
- [Senior Electromechanical Technician](https://job-boards.greenhouse.io/lilasciences/jobs/4240297009) — Cambridge, MA USA
- [Senior Engineer I/II, Drug Discovery Platform](https://job-boards.greenhouse.io/lilasciences/jobs/4286513009) — Cambridge, MA USA
- [Senior Engineer II, Cloud Security](https://job-boards.greenhouse.io/lilasciences/jobs/4337833009) — Cambridge, MA USA
- [Senior Human Factors Engineer - Robotics](https://job-boards.greenhouse.io/lilasciences/jobs/4332442009) — Cambridge, MA USA
- [Senior II/Staff Mechatronics Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4337828009) — Cambridge, MA USA
- [Senior Machine Learning Engineer I, Physical Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4116513009) — Cambridge, MA USA
- [Senior ML Scientist, Biological Systems](https://job-boards.greenhouse.io/lilasciences/jobs/4308126009) — San Francisco, CA USA
- [Senior Research Associate , Automated Chemistry](https://job-boards.greenhouse.io/lilasciences/jobs/4254693009) — Cambridge, MA USA
- [Senior Research Associate / Associate Scientist, Characterization](https://job-boards.greenhouse.io/lilasciences/jobs/4310496009) — Cambridge, MA USA
- [Senior Software Engineer I/II, Back-end/Data, Robotics](https://job-boards.greenhouse.io/lilasciences/jobs/4339324009) — Cambridge, MA USA
- [Senior Software Engineer I/II, Test Robotics](https://job-boards.greenhouse.io/lilasciences/jobs/4332043009) — Cambridge, MA USA
- [Senior Software Engineer II, Enterprise Platform](https://job-boards.greenhouse.io/lilasciences/jobs/4299652009) — San Francisco, CA USA
- [Senior Software Engineer, App](https://job-boards.greenhouse.io/lilasciences/jobs/4248042009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior Software Engineer, Applied AI](https://job-boards.greenhouse.io/lilasciences/jobs/4031455009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior Software Engineer, Data](https://job-boards.greenhouse.io/lilasciences/jobs/4250077009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior Software Engineer, Lab Software](https://job-boards.greenhouse.io/lilasciences/jobs/4250038009) — Cambridge, MA USA
- [Senior Software Engineer, ML Research](https://job-boards.greenhouse.io/lilasciences/jobs/4031328009) — Cambridge, MA USA
- [Senior Software Engineer, Operations Research](https://job-boards.greenhouse.io/lilasciences/jobs/4246973009) — Cambridge, MA USA
- [Senior Software Engineer, Scientific System of Record](https://job-boards.greenhouse.io/lilasciences/jobs/4248049009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior Technical Program Manager, AISF](https://job-boards.greenhouse.io/lilasciences/jobs/4289723009) — Cambridge, MA USA
- [Senior Technical Program Manager, Robotics](https://job-boards.greenhouse.io/lilasciences/jobs/4341034009) — Cambridge, MA USA
- [Senior/Principal Scientist, Small Molecule Therapeutics](https://job-boards.greenhouse.io/lilasciences/jobs/4296054009) — Cambridge, MA USA
- [Software Engineer I, Instrument Software ](https://job-boards.greenhouse.io/lilasciences/jobs/4186444009) — Cambridge, MA USA
- [Software Engineer II, Lab Software](https://job-boards.greenhouse.io/lilasciences/jobs/4250045009) — Cambridge, MA USA
- [Sr Principal/ Principal Software Engineer, Scientific System of Record](https://job-boards.greenhouse.io/lilasciences/jobs/4193827009) — Cambridge, MA USA; San Francisco, CA USA
- [Sr Principal/Principal Software Engineer, App](https://job-boards.greenhouse.io/lilasciences/jobs/4248036009) — Cambridge, MA USA; San Francisco, CA USA
- [Staff  Research Engineer, Scientific Computing and ML/Physics Infrastructure](https://job-boards.greenhouse.io/lilasciences/jobs/4340149009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Staff / Principal Automated Systems Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4110350009) — Cambridge, MA USA
- [Staff / Principal Research Engineer, AI Safety, Technical Mitigations](https://job-boards.greenhouse.io/lilasciences/jobs/4210472009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Staff DevOps Engineer, Software, Product Operations ](https://job-boards.greenhouse.io/lilasciences/jobs/4212473009) — Cambridge, MA USA
- [Staff Engineer, Data Platform](https://job-boards.greenhouse.io/lilasciences/jobs/4222065009) — Cambridge, MA USA; San Francisco, CA USA
- [Staff Engineer, OT Security ](https://job-boards.greenhouse.io/lilasciences/jobs/4330472009) — Cambridge, MA USA
- [Staff Forward Deployed Engineer, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4031282009) — Cambridge, MA USA
- [Staff Forward Deployed Engineer, Physical Sciences (Level Flexible)](https://job-boards.greenhouse.io/lilasciences/jobs/4031303009) — Cambridge, MA USA
- [Staff Software Engineer, Lab Software](https://job-boards.greenhouse.io/lilasciences/jobs/4250063009) — Cambridge, MA USA
- [Staff Software Engineer, Scientific System of Record](https://job-boards.greenhouse.io/lilasciences/jobs/4248045009) — Cambridge, MA USA; San Francisco, CA USA
- [Staff/Principal DevOps Engineer, AI Inference](https://job-boards.greenhouse.io/lilasciences/jobs/4248032009) — Cambridge, MA USA
- [Technical Program Manager, AI Data](https://job-boards.greenhouse.io/lilasciences/jobs/4259557009) — Cambridge, MA USA; San Francisco, CA USA
- [Vice President, Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4232839009) — Cambridge, MA USA
- [Vice President, Head of Government Partnerships](https://job-boards.greenhouse.io/lilasciences/jobs/4324020009) — Cambridge, MA USA
- [Vice President, Head of Marketing](https://job-boards.greenhouse.io/lilasciences/jobs/4146076009) — Cambridge, MA USA

**BillionToOne** (96)
- [Accessioner, Prenatal (Part-Time)](https://job-boards.greenhouse.io/billiontoone/jobs/4713218005) — Union City, CA
- [Associate Director of Events](https://job-boards.greenhouse.io/billiontoone/jobs/4720973005) — Remote
- [Automation Service Engineer I/II, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4711447005) — Menlo Park, CA
- [Automation Service Engineering Associate I/II, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4703333005) — Menlo Park, CA
- [Automation Service Engineering Manager, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4470824005) — Menlo Park, CA
- [CLIA Laboratory Supervisor, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4708309005) — Menlo Park, CA
- [Client Services Associate I, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4716882005) — Union City, CA
- [Client Services Associate I, Prenatal](https://job-boards.greenhouse.io/billiontoone/jobs/4666394005) — Union City, CA
- [Clinical Laboratory Associate, Prenatal (Overnight Shift)](https://job-boards.greenhouse.io/billiontoone/jobs/4678611005) — Union City, CA
- [Clinical Laboratory Associate, Prenatal and Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4709984005) — Menlo Park or Union City, CA
- [Clinical Laboratory Scientist, Oncology (PM Shift) ](https://job-boards.greenhouse.io/billiontoone/jobs/4683074005) — Menlo Park, CA
- [Clinical Laboratory Scientist, Oncology (Sunday AM Shift) ](https://job-boards.greenhouse.io/billiontoone/jobs/4718937005) — Menlo Park, CA
- [Clinical Laboratory Scientist, Prenatal ](https://job-boards.greenhouse.io/billiontoone/jobs/4702009005) — Union City, CA
- [Clinical Laboratory Scientist, Prenatal (contractor)](https://job-boards.greenhouse.io/billiontoone/jobs/4702002005) — Union City, CA
- [Data Scientist, Prenatal](https://job-boards.greenhouse.io/billiontoone/jobs/4694395005) — Menlo Park, CA
- [Director / Associate Director, Oncology Product Marketing](https://job-boards.greenhouse.io/billiontoone/jobs/4720536005) — Remote
- [Director of Commercial Strategy and Operations](https://job-boards.greenhouse.io/billiontoone/jobs/4705871005) — Remote
- [Director of IT](https://job-boards.greenhouse.io/billiontoone/jobs/4683268005) — Menlo Park, CA or Union City, CA
- [Director of Office of the CEO, Founder in Residence ](https://job-boards.greenhouse.io/billiontoone/jobs/4707633005) — Menlo Park, CA
- [EMR Success Manager](https://job-boards.greenhouse.io/billiontoone/jobs/4657257005) — Remote
- [General Supervisor, Prenatal](https://job-boards.greenhouse.io/billiontoone/jobs/4710464005) — Union City, CA
- [Head of Strategic Pharma Partnerships, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4507427005) — Remote
- [Lead UX Designer](https://job-boards.greenhouse.io/billiontoone/jobs/4704105005) — Menlo Park, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4481121005) — Remote
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4566777005) — Spokane, WA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4663423005) — San Jose, CA 
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4676850005) — South Atlanta, GA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4689412005) — Temecula, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4689413005) — Roanoke, VA 
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4689420005) — Rochester, MN
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4689426005) — State College, PA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4689921005) — Chico, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4706194005) — Redwood City, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4706195005) — Santa Clara, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4706197005) — Murrieta, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4706897005) — Bozeman, MT
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707154005) — Boise, ID 
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707158005) — Boston, MA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707162005) — North Columbus, OH
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707168005) — Fresno, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707169005) — Houston, TX
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707180005) — Las Vegas, NV
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707181005) — South Miami, FL
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707185005) — Milwaukee, WI
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707189005) — Columbus/Dayton, OH
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707191005) — Omaha, NE
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707194005) — Portland, OR
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707196005) — Philadelphia, PA 
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707198005) — Riverside, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707205005) — West Seattle, WA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707206005) — Macon, GA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707207005) — Virginia Beach, VA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707209005) — Washington D.C., DC
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4714793005) — South New Jersey, NJ
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4716898005) — Sarasota / Fort Meyers, FL
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4717249005) — Eugene, OR
- [Oncology Regional Sales Manager, Southern California ](https://job-boards.greenhouse.io/billiontoone/jobs/4703269005) — Southern California 
- [Oncology Regional Sales Manager, Upper Midwest](https://job-boards.greenhouse.io/billiontoone/jobs/4667498005) — Minnesota
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4668001005) — West Boston, MA
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4679893005) — Southeast San Antonio, TX
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4684168005) — Chesapeake, VA
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4685595005) — East Phoenix, AZ
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4686559005) — Baton Rouge, LA
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4688013005) — Queens, NYC
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4699323005) — Northeast San Antonio, TX
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707214005) — Colorado Springs, CO
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707215005) — Fayetteville, NC
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707219005) — Fredericksburg, VA
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707221005) — Idaho Falls, ID
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707225005) — Monterey, CA
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707226005) — Albuquerque, NM
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707227005) — Eau Claire, WI
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707239005) — San Jose/South Bay, CA
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707240005) — Evansville, IN
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707243005) — Springfield, MO
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707244005) — Westchester, NY
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4716459005) — Oklahoma City, OK
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4718574005) — Frederick, MD
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4720160005) — Salt Lake City, Utah
- [Prenatal Account Support Representative](https://job-boards.greenhouse.io/billiontoone/jobs/4711496005) — San Antonio, TX
- [Prenatal Regional Sales Manager, DMV](https://job-boards.greenhouse.io/billiontoone/jobs/4364573005) — Maryland, Washington, D.C., Eastern Virginia
- [Prenatal Regional Sales Manager, Great Plains](https://job-boards.greenhouse.io/billiontoone/jobs/4611958005) — Minnesota, Iowa, South Dakota, North Dakota
- [Prenatal Regional Sales Manager, Gulf Coast](https://job-boards.greenhouse.io/billiontoone/jobs/4685827005) — Mississippi, Louisiana, Tennessee
- [Prenatal Regional Sales Manager, North Atlantic](https://job-boards.greenhouse.io/billiontoone/jobs/4665574005) — Pennsylvania, New Jersey, Delaware
- [Prenatal Regional Sales Manager, Northern Los Angeles](https://job-boards.greenhouse.io/billiontoone/jobs/4707253005) — Northern California
- [Prenatal Senior Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4080962005) — Remote
- [Process Engineering Associate I/II, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4482409005) — Menlo Park, CA
- [Quality Engineer, Prenatal](https://job-boards.greenhouse.io/billiontoone/jobs/4707547005) — Union City, CA
- [Research Associate](https://job-boards.greenhouse.io/billiontoone/jobs/4714147005) — Menlo Park, CA
- [Revenue Manager](https://job-boards.greenhouse.io/billiontoone/jobs/4717344005) — Menlo Park, CA
- [Sales Training Manager, Prenatal](https://job-boards.greenhouse.io/billiontoone/jobs/4711331005) — Remote
- [Senior AI Engineer I](https://job-boards.greenhouse.io/billiontoone/jobs/4570095005) — Menlo Park, CA
- [Senior Director, Software Product Management and Product Engineering](https://job-boards.greenhouse.io/billiontoone/jobs/4707466005) — Menlo Park, CA
- [Senior IT Desktop Support Technician](https://job-boards.greenhouse.io/billiontoone/jobs/4720084005) — Menlo Park, CA
- [Senior Software Engineer, Digital Experiences](https://job-boards.greenhouse.io/billiontoone/jobs/4683643005) — Menlo Park, CA
- [Senior Software Engineer, Prenatal](https://job-boards.greenhouse.io/billiontoone/jobs/4305991005) — Menlo Park, CA

**Anduril** (2211)
- 🎓 [2027 Electrical Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5148101007?gh_jid=5148101007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Costa Mesa, California, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- 🎓 [2027 Manufacturing Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5153218007?gh_jid=5153218007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Costa Mesa, California, United States; Irvine, California, United States; Seattle, Washington, United States
- 🎓 [2027 Mechanical Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5153187007?gh_jid=5153187007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Costa Mesa, California, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- 🎓 [2027 Software Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5148079007?gh_jid=5148079007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Costa Mesa, California, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- 🎓 [Naval Architect Co-op - Winter 2027](https://boards.greenhouse.io/andurilindustries/jobs/5170844007?gh_jid=5170844007) — Costa Mesa, California, United States
- [	CNC Programmer](https://boards.greenhouse.io/andurilindustries/jobs/4799423007?gh_jid=4799423007) — Costa Mesa, California, United States
- [ Development Test Engineer](https://boards.greenhouse.io/andurilindustries/jobs/4676612007?gh_jid=4676612007) — Costa Mesa, California, United States
- [ Early Career Product Operations Rotation Program ](https://boards.greenhouse.io/andurilindustries/jobs/5181983007?gh_jid=5181983007) — Costa Mesa, California, United States
- [ Head of Maintenance Repair & Overhaul](https://boards.greenhouse.io/andurilindustries/jobs/5148720007?gh_jid=5148720007) — Costa Mesa, California, United States
- [ Lead Manufacturing Engineer, Missiles](https://boards.greenhouse.io/andurilindustries/jobs/5137065007?gh_jid=5137065007) — Costa Mesa, California, United States
- [ Low Observables Engineer, RCS](https://boards.greenhouse.io/andurilindustries/jobs/4418353007?gh_jid=4418353007) — Costa Mesa, California, United States
- [ Manufacturing Engineer, Production, Sentry](https://boards.greenhouse.io/andurilindustries/jobs/5085941007?gh_jid=5085941007) — Irvine, California, United States
- [ Multi-Domain Mission Capabilities Lead, Multinational Digital Infrastructure ](https://boards.greenhouse.io/andurilindustries/jobs/5117575007?gh_jid=5117575007) — Washington, District of Columbia, United States
- [ Multi-Domain Mission Capabilities Lead, Multinational Digital Infrastructure ](https://boards.greenhouse.io/andurilindustries/jobs/5117576007?gh_jid=5117576007) — Boston, Massachusetts, United States
- [ Quality Control Manager ](https://boards.greenhouse.io/andurilindustries/jobs/5187522007?gh_jid=5187522007) — Costa Mesa, California, United States
- [ Quality Specialist, Intelligence Systems (Secret Clearance)](https://boards.greenhouse.io/andurilindustries/jobs/5120533007?gh_jid=5120533007) — Santa Ana, California, United States
- [ Senior Aerodynamics Engineer, Air Vehicles](https://boards.greenhouse.io/andurilindustries/jobs/4629832007?gh_jid=4629832007) — Costa Mesa, California, United States
- [ Senior FPGA Test Engineer, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/4591133007?gh_jid=4591133007) — Reston, Virginia, United States
- [ Senior Program Manager, People Operations](https://boards.greenhouse.io/andurilindustries/jobs/5188731007?gh_jid=5188731007) — Seattle, Washington, United States
- [ Senior Supplier Quality Engineer, Mechanical Subassembly / Composites](https://boards.greenhouse.io/andurilindustries/jobs/5134865007?gh_jid=5134865007) — Costa Mesa, California, United States
- [(HVAC Specialist) Technical Operations Engineer - Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5200126007?gh_jid=5200126007) — Costa Mesa, California, United States
- [2026 Early Career Electrical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/4802172007?gh_jid=4802172007) — Costa Mesa, California, United States; Fort Collins, Colorado, United States
- [2026 Early Career Engineering Finance Associate](https://boards.greenhouse.io/andurilindustries/jobs/5159092007?gh_jid=5159092007) — Costa Mesa, California, United States
- [2026 Early Career Flight Test Engineer, Mission Autonomy](https://boards.greenhouse.io/andurilindustries/jobs/5185089007?gh_jid=5185089007) — Costa Mesa, California, United States
- [2026 Early Career Manufacturing Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5176254007?gh_jid=5176254007) — Costa Mesa, California, United States; Irvine, California, United States; Santa Ana, California, United States
- [2026 Early Career Mechanical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/4802167007?gh_jid=4802167007) — Costa Mesa, California, United States
- [2026 Early Career Software Engineer](https://boards.greenhouse.io/andurilindustries/jobs/4802146007?gh_jid=4802146007) — Atlanta, Georgia, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Seattle, Washington, United States
- [2026 Early Career Test & Evaluation Systems Integrator](https://boards.greenhouse.io/andurilindustries/jobs/5185888007?gh_jid=5185888007) — Costa Mesa, California, United States
- [2026 Total Rewards/People Operations Specialist - Early Career Rotation Program](https://boards.greenhouse.io/andurilindustries/jobs/5159933007?gh_jid=5159933007) — Costa Mesa, California, United States
- [2027 Early Career Electrical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5136925007?gh_jid=5136925007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Costa Mesa, California, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- [2027 Early Career Manufacturing Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5136970007?gh_jid=5136970007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Costa Mesa, California, United States; Irvine, California, United States; Seattle, Washington, United States
- [2027 Early Career Mechanical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5136984007?gh_jid=5136984007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Costa Mesa, California, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- [2027 Early Career Software Engineer ](https://boards.greenhouse.io/andurilindustries/jobs/5162263007?gh_jid=5162263007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Costa Mesa, California, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- [2nd Shift Quality Inspector](https://boards.greenhouse.io/andurilindustries/jobs/4910739007?gh_jid=4910739007) — Ashville, Ohio, United States
- [2nd Shift Quality Inspector](https://boards.greenhouse.io/andurilindustries/jobs/5201654007?gh_jid=5201654007) — Atlanta, Georgia, United States
- [Acceptance Test Procedure Technician, Roadrunner](https://boards.greenhouse.io/andurilindustries/jobs/5116801007?gh_jid=5116801007) — Ashville, Ohio, United States
- [AD&S, Air Vehicle Software Systems Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5131822007?gh_jid=5131822007) — Costa Mesa, California, United States
- [Aerodynamics Engineer, Air Vehicles](https://boards.greenhouse.io/andurilindustries/jobs/5000486007?gh_jid=5000486007) — Costa Mesa, California, United States
- [Aerodynamics Engineer, Hypersonic Air Vehicles](https://boards.greenhouse.io/andurilindustries/jobs/5032351007?gh_jid=5032351007) — Costa Mesa, California, United States
- [AFSIM Operations Analyst, Mission Engineering, Air Dominance & Strike, Active Clearance](https://boards.greenhouse.io/andurilindustries/jobs/5103907007?gh_jid=5103907007) — Ashville, Ohio, United States; Costa Mesa, California, United States
- [AI Solutions Engineer, Talent Acquisition](https://boards.greenhouse.io/andurilindustries/jobs/5171942007?gh_jid=5171942007) — Costa Mesa, California, United States
- [AI Solutions Engineer, Talent Acquisition](https://boards.greenhouse.io/andurilindustries/jobs/5173388007?gh_jid=5173388007) — Boston, Massachusetts, United States
- [AI Solutions Engineer, Talent Acquisition](https://boards.greenhouse.io/andurilindustries/jobs/5173534007?gh_jid=5173534007) — Seattle, Washington, United States
- [Air Vehicle Lead](https://boards.greenhouse.io/andurilindustries/jobs/5088612007?gh_jid=5088612007) — Costa Mesa, California, United States
- [Air Vehicle Lead, Thunder ](https://boards.greenhouse.io/andurilindustries/jobs/5175758007?gh_jid=5175758007) — Costa Mesa, California, United States
- [Air Vehicle Systems Engineer, Hardware Verification, Integration & Validation](https://boards.greenhouse.io/andurilindustries/jobs/5131979007?gh_jid=5131979007) — Costa Mesa, California, United States
- [Air Vehicle Systems Verification Lead](https://boards.greenhouse.io/andurilindustries/jobs/5131984007?gh_jid=5131984007) — Costa Mesa, California, United States
- [Air-Vehicle Multidisciplinary Design Analysis and Optimization (MDAO) Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5132442007?gh_jid=5132442007) — Costa Mesa, California, United States
- [Algorithm Developer, Battlespace Awareness](https://boards.greenhouse.io/andurilindustries/jobs/5207731007?gh_jid=5207731007) — Broomfield, Colorado, United States; Fort Collins, Colorado, United States
- [Algorithm Engineer, Battlespace Awareness](https://boards.greenhouse.io/andurilindustries/jobs/5207732007?gh_jid=5207732007) — Broomfield, Colorado, United States; Fort Collins, Colorado, United States
- [Analytics Engineer, Hardware Test](https://boards.greenhouse.io/andurilindustries/jobs/4768437007?gh_jid=4768437007) — Costa Mesa, California, United States
- [Analytics Lead, Manufacturing Quality](https://boards.greenhouse.io/andurilindustries/jobs/5167749007?gh_jid=5167749007) — Atlanta, Georgia, United States
- [Analytics Lead, Manufacturing Quality](https://boards.greenhouse.io/andurilindustries/jobs/5198870007?gh_jid=5198870007) — Ashville, Ohio, United States
- [Android Engineer ](https://boards.greenhouse.io/andurilindustries/jobs/5158239007?gh_jid=5158239007) — Costa Mesa, California, United States; Seattle, Washington, United States; Washington, District of Columbia, United States
- [Applied LLM Systems Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5197253007?gh_jid=5197253007) — Costa Mesa, California, United States
- [ASNT/NAVSEA NDT Inspector, UT Level III, Maritime](https://boards.greenhouse.io/andurilindustries/jobs/5167576007?gh_jid=5167576007) — Santa Ana, California, United States
- [Assembly Technician, Launch Team](https://boards.greenhouse.io/andurilindustries/jobs/5152071007?gh_jid=5152071007) — Ashville, Ohio, United States
- [Assistant Contractor Special Security Officer](https://boards.greenhouse.io/andurilindustries/jobs/5203761007?gh_jid=5203761007) — Costa Mesa, California, United States
- [Assistant Facility Security Officer](https://boards.greenhouse.io/andurilindustries/jobs/5202409007?gh_jid=5202409007) — Costa Mesa, California, United States
- [Associate Director of Finance, Maritime](https://boards.greenhouse.io/andurilindustries/jobs/5208200007?gh_jid=5208200007) — Costa Mesa, California, United States
- [Associate Director, Army Mission Operations](https://boards.greenhouse.io/andurilindustries/jobs/5188188007?gh_jid=5188188007) — Seattle, Washington, United States
- [Associate Director, Army Mission Operations](https://boards.greenhouse.io/andurilindustries/jobs/5195955007?gh_jid=5195955007) — Washington, District of Columbia, United States
- [Associate Director, Army Mission Operations](https://boards.greenhouse.io/andurilindustries/jobs/5195961007?gh_jid=5195961007) — Fort Bragg, North Carolina, United States
- [Associate Director, Finance Strategy and Planning](https://boards.greenhouse.io/andurilindustries/jobs/5121418007?gh_jid=5121418007) — Costa Mesa, California, United States
- [Associate Director, International Project Logistics](https://boards.greenhouse.io/andurilindustries/jobs/5201946007?gh_jid=5201946007) — Costa Mesa, California, United States
- [Associate Director, International Project Logistics](https://boards.greenhouse.io/andurilindustries/jobs/5201948007?gh_jid=5201948007) — Ashville, Ohio, United States
- [Associate Director, Space Growth](https://boards.greenhouse.io/andurilindustries/jobs/5133374007?gh_jid=5133374007) — Chantilly, Virginia, United States
- [Associate Facilities Manager](https://boards.greenhouse.io/andurilindustries/jobs/5156366007?gh_jid=5156366007) — Costa Mesa, California, United States
- [Associate General Counsel, Policy](https://boards.greenhouse.io/andurilindustries/jobs/5169153007?gh_jid=5169153007) — Washington, District of Columbia, United States
- [Associate Workplace Manager](https://boards.greenhouse.io/andurilindustries/jobs/5156606007?gh_jid=5156606007) — Costa Mesa, California, United States
- [Automation & Torque Tooling Technician](https://boards.greenhouse.io/andurilindustries/jobs/5183582007?gh_jid=5183582007) — Costa Mesa, California, United States
- [Automation Engineer, Manufacturing Automation](https://boards.greenhouse.io/andurilindustries/jobs/5201063007?gh_jid=5201063007) — Costa Mesa, California, United States
- [Autonomy Lead](https://boards.greenhouse.io/andurilindustries/jobs/5167055007?gh_jid=5167055007) — Costa Mesa, California, United States
- [AV Systems Administrator ](https://boards.greenhouse.io/andurilindustries/jobs/5190224007?gh_jid=5190224007) — Washington, District of Columbia, United States
- [AV Technician](https://boards.greenhouse.io/andurilindustries/jobs/5083595007?gh_jid=5083595007) — Costa Mesa, California, United States
- [Aviation Maintenance Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5115028007?gh_jid=5115028007) — Phoenix, Arizona, United States
- [Aviation Maintenance Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5178802007?gh_jid=5178802007) — Costa Mesa, California, United States
- [Battery Mechanical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5187738007?gh_jid=5187738007) — Costa Mesa, California, United States
- [Battery Technical Program Manager](https://boards.greenhouse.io/andurilindustries/jobs/5200203007?gh_jid=5200203007) — Costa Mesa, California, United States
- [Battery Test Technician](https://boards.greenhouse.io/andurilindustries/jobs/5130695007?gh_jid=5130695007) — Costa Mesa, California, United States
- [BOM Sourcing Engineer, Intelligence Systems & Space (Active Clearance)](https://boards.greenhouse.io/andurilindustries/jobs/5029722007?gh_jid=5029722007) — Costa Mesa, California, United States
- [BOM Sourcing Engineer, Supply Chain](https://boards.greenhouse.io/andurilindustries/jobs/5174509007?gh_jid=5174509007) — Costa Mesa, California, United States
- [Business Operations Associate](https://boards.greenhouse.io/andurilindustries/jobs/4951316007?gh_jid=4951316007) — Costa Mesa, California, United States
- [Business Operations Associate - Technical Projects](https://boards.greenhouse.io/andurilindustries/jobs/4951318007?gh_jid=4951318007) — Costa Mesa, California, United States
- [Business Operations Associate, Production](https://boards.greenhouse.io/andurilindustries/jobs/4619191007?gh_jid=4619191007) — Costa Mesa, California, United States
- [Business Operations Engineer, Air Dominance & Strike ](https://boards.greenhouse.io/andurilindustries/jobs/5111193007?gh_jid=5111193007) — Costa Mesa, California, United States
- [Business Operations Lead](https://boards.greenhouse.io/andurilindustries/jobs/4951325007?gh_jid=4951325007) — Costa Mesa, California, United States
- [Business Operations Lead - Technical Projects](https://boards.greenhouse.io/andurilindustries/jobs/5117374007?gh_jid=5117374007) — Costa Mesa, California, United States
- [Business Operations, Air Dominance & Strike](https://boards.greenhouse.io/andurilindustries/jobs/4790841007?gh_jid=4790841007) — Costa Mesa, California, United States
- [Business Operations, Air Dominance & Strike](https://boards.greenhouse.io/andurilindustries/jobs/5155193007?gh_jid=5155193007) — Costa Mesa, California, United States
- [Business Operations, Production](https://boards.greenhouse.io/andurilindustries/jobs/5195711007?gh_jid=5195711007) — Costa Mesa, California, United States
- [Business Operations, Strategic Supply Chain](https://boards.greenhouse.io/andurilindustries/jobs/5165934007?gh_jid=5165934007) — Costa Mesa, California, United States
- [Business Process Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5206041007?gh_jid=5206041007) — Atlanta, Georgia, United States
- [Business Systems Infrastructure Coordinator](https://boards.greenhouse.io/andurilindustries/jobs/5203778007?gh_jid=5203778007) — Costa Mesa, California, United States
- [Buyer](https://boards.greenhouse.io/andurilindustries/jobs/5163565007?gh_jid=5163565007) — Quonset, Rhode Island, United States
- [Buyer ](https://boards.greenhouse.io/andurilindustries/jobs/5200843007?gh_jid=5200843007) — Waltham, Massachusetts, United States
- [Buyer, Commercial Hardware Procurement](https://boards.greenhouse.io/andurilindustries/jobs/4802276007?gh_jid=4802276007) — Costa Mesa, California, United States
- [Buyer, Federal Technical Procurement/FAR & DFAR](https://boards.greenhouse.io/andurilindustries/jobs/4802288007?gh_jid=4802288007) — Costa Mesa, California, United States
- [Buyer, Indirect (R&D/Soft Services Procurement)](https://boards.greenhouse.io/andurilindustries/jobs/4802297007?gh_jid=4802297007) — Costa Mesa, California, United States
- [Buyer, Maritime](https://boards.greenhouse.io/andurilindustries/jobs/5087656007?gh_jid=5087656007) — Costa Mesa, California, United States
- [Buyer/Planner](https://boards.greenhouse.io/andurilindustries/jobs/5072024007?gh_jid=5072024007) — Quonset, Rhode Island, United States
- [Buyer/Planner](https://boards.greenhouse.io/andurilindustries/jobs/5169966007?gh_jid=5169966007) — Quincy, Massachusetts, United States
- [C++ Mission Software Engineer, Mission Autonomy](https://boards.greenhouse.io/andurilindustries/jobs/5125189007?gh_jid=5125189007) — Costa Mesa, California, United States; Seattle, Washington, United States; Washington, District of Columbia, United States
- [Calibration Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5201425007?gh_jid=5201425007) — Ashville, Ohio, United States
- [Calibration Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5201431007?gh_jid=5201431007) — Costa Mesa, California, United States
- [Calibration Technician](https://boards.greenhouse.io/andurilindustries/jobs/5198192007?gh_jid=5198192007) — Costa Mesa, California, United States
- [Calibration Technician](https://boards.greenhouse.io/andurilindustries/jobs/5201450007?gh_jid=5201450007) — Costa Mesa, California, United States
- [Camera Test Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5196583007?gh_jid=5196583007) — Lexington, Massachusetts, United States
- [Chief Architect, EW](https://boards.greenhouse.io/andurilindustries/jobs/5155026007?gh_jid=5155026007) — Costa Mesa, California, United States
- [Chief Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5084723007?gh_jid=5084723007) — Amsterdam, North Holland, Netherlands
- [Chief Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5159733007?gh_jid=5159733007) — Costa Mesa, California, United States
- [Chief Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5192229007?gh_jid=5192229007) — Waltham, Massachusetts, United States
- [Chief Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5194664007?gh_jid=5194664007) — Costa Mesa, California, United States
- [Chief Engineer, Advanced Effects](https://boards.greenhouse.io/andurilindustries/jobs/4742120007?gh_jid=4742120007) — Costa Mesa, California, United States
- [Chief Engineer, Autonomous Airpower](https://boards.greenhouse.io/andurilindustries/jobs/5087403007?gh_jid=5087403007) — Costa Mesa, California, United States
- [Chief Engineer, Autonomous Flight](https://boards.greenhouse.io/andurilindustries/jobs/5158222007?gh_jid=5158222007) — Costa Mesa, California, United States; Seattle, Washington, United States; Washington, District of Columbia, United States
- [Chief Engineer, Fury  Science & Tech](https://boards.greenhouse.io/andurilindustries/jobs/5060066007?gh_jid=5060066007) — Costa Mesa, California, United States
- [Chief Engineer, Fury Advanced Concepts](https://boards.greenhouse.io/andurilindustries/jobs/5081059007?gh_jid=5081059007) — Costa Mesa, California, United States
- [Chief Engineer, Fury Aircraft Development](https://boards.greenhouse.io/andurilindustries/jobs/5081020007?gh_jid=5081020007) — Costa Mesa, California, United States
- [Chief Engineer, Ground Maneuver](https://boards.greenhouse.io/andurilindustries/jobs/5149344007?gh_jid=5149344007) — Costa Mesa, California, United States
- [Chief Engineer, Intel Systems](https://boards.greenhouse.io/andurilindustries/jobs/5032221007?gh_jid=5032221007) — Reston, Virginia, United States
- [Chief Engineer, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/5126292007?gh_jid=5126292007) — Reston, Virginia, United States
- [Chief Engineer, Maritime Integrated Systems](https://boards.greenhouse.io/andurilindustries/jobs/5103884007?gh_jid=5103884007) — Quincy, Massachusetts, United States
- [Chief Engineer, Maritime Integrated Systems](https://boards.greenhouse.io/andurilindustries/jobs/5199934007?gh_jid=5199934007) — Boston, Massachusetts, United States
- [Chief Engineer, Tactical Recon and Strike](https://boards.greenhouse.io/andurilindustries/jobs/5130983007?gh_jid=5130983007) — Costa Mesa, California, United States
- [Chief Radar Engineer ](https://boards.greenhouse.io/andurilindustries/jobs/5205891007?gh_jid=5205891007) — Broomfield, Colorado, United States; Fort Collins, Colorado, United States
- [Chief Systems Architect, SIG](https://boards.greenhouse.io/andurilindustries/jobs/5194571007?gh_jid=5194571007) — Santa Ana, California, United States
- [Classified System Administrator (Active Clearance), Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/5160343007?gh_jid=5160343007) — Reston, Virginia, United States
- [Cloud Deployment Engineer, Space ](https://boards.greenhouse.io/andurilindustries/jobs/5016027007?gh_jid=5016027007) — Costa Mesa, California, United States
- [CNC Programmer/Operator](https://boards.greenhouse.io/andurilindustries/jobs/5179736007?gh_jid=5179736007) — Morrisville, North Carolina, United States
- [Commercial HVAC/R & Mechanical Systems Technician, Maritime](https://boards.greenhouse.io/andurilindustries/jobs/5166928007?gh_jid=5166928007) — Santa Ana, California, United States
- [Composite Technician, Weekend Shift](https://boards.greenhouse.io/andurilindustries/jobs/5175477007?gh_jid=5175477007) — Morrisville, North Carolina, United States
- [Computer Vision Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5102920007?gh_jid=5102920007) — Costa Mesa, California, United States
- [Configuration Design Engineer ](https://boards.greenhouse.io/andurilindustries/jobs/5208194007?gh_jid=5208194007) — Costa Mesa, California, United States
- [Connectivity Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5107257007?gh_jid=5107257007) — Costa Mesa, California, United States
- [Construction Project Manager](https://boards.greenhouse.io/andurilindustries/jobs/5186776007?gh_jid=5186776007) — McHenry, Mississippi, United States
- [Construction Project Manager, Asset Improvements](https://boards.greenhouse.io/andurilindustries/jobs/5184060007?gh_jid=5184060007) — Ashville, Ohio, United States
- [Construction Project Manager, Asset Improvements](https://boards.greenhouse.io/andurilindustries/jobs/5184062007?gh_jid=5184062007) — Washington, District of Columbia, United States
- [Construction Project Manager, Asset Improvements ](https://boards.greenhouse.io/andurilindustries/jobs/5183350007?gh_jid=5183350007) — Boston, Massachusetts, United States
- [Construction Systems Specialist](https://boards.greenhouse.io/andurilindustries/jobs/5205867007?gh_jid=5205867007) — Costa Mesa, California, United States
- [Contractor Special Security Officer](https://boards.greenhouse.io/andurilindustries/jobs/5141080007?gh_jid=5141080007) — El Segundo, California, United States
- [Contractor Special Security Officer](https://boards.greenhouse.io/andurilindustries/jobs/5187665007?gh_jid=5187665007) — Costa Mesa, California, United States
- [Contractor Special Security Officer](https://boards.greenhouse.io/andurilindustries/jobs/5200176007?gh_jid=5200176007) — Ashville, Ohio, United States
- [Contracts Manager](https://boards.greenhouse.io/andurilindustries/jobs/5185207007?gh_jid=5185207007) — Washington, District of Columbia, United States
- [Contracts Manager](https://boards.greenhouse.io/andurilindustries/jobs/5200578007?gh_jid=5200578007) — Reston, Virginia, United States
- [Contracts Manager ](https://boards.greenhouse.io/andurilindustries/jobs/5184594007?gh_jid=5184594007) — Costa Mesa, California, United States
- [Controls Engineer, Manufacturing Automation ](https://boards.greenhouse.io/andurilindustries/jobs/5038031007?gh_jid=5038031007) — Costa Mesa, California, United States
- [Cost Value Engineer, Intelligence Systems & Space (Active Clearance)](https://boards.greenhouse.io/andurilindustries/jobs/5029726007?gh_jid=5029726007) — Costa Mesa, California, United States
- [Counterintelligence Analyst Lead](https://boards.greenhouse.io/andurilindustries/jobs/5165171007?gh_jid=5165171007) — Costa Mesa, California, United States
- [Creative Operations Manager, Environmental Design](https://boards.greenhouse.io/andurilindustries/jobs/5176659007?gh_jid=5176659007) — Costa Mesa, California, United States
- [Curriculum Developer ](https://boards.greenhouse.io/andurilindustries/jobs/4997521007?gh_jid=4997521007) — Costa Mesa, California, United States
- [Customer Success Manager - AIRS](https://boards.greenhouse.io/andurilindustries/jobs/5209733007?gh_jid=5209733007) — Hudson, New Hampshire, United States
- [CW Production Recruiting Lead](https://boards.greenhouse.io/andurilindustries/jobs/5202671007?gh_jid=5202671007) — Costa Mesa, California, United States
- [CW Production Recruiting Lead](https://boards.greenhouse.io/andurilindustries/jobs/5205305007?gh_jid=5205305007) — Seattle, Washington, United States
- [Data Analyst, Manufacturing](https://boards.greenhouse.io/andurilindustries/jobs/5198002007?gh_jid=5198002007) — Santa Ana, California, United States
- [Data Product Enablement Specialist ](https://boards.greenhouse.io/andurilindustries/jobs/5088628007?gh_jid=5088628007) — Costa Mesa, California, United States
- [Demand & Supply Planner ](https://boards.greenhouse.io/andurilindustries/jobs/5165236007?gh_jid=5165236007) — Costa Mesa, California, United States
- [Demand & Supply Planner, Advanced Effects Missiles](https://boards.greenhouse.io/andurilindustries/jobs/5165129007?gh_jid=5165129007) — Costa Mesa, California, United States
- [Demand & Supply Planner, Air Defense](https://boards.greenhouse.io/andurilindustries/jobs/5200160007?gh_jid=5200160007) — Costa Mesa, California, United States
- [Demand & Supply Planner, Air Dominance & Strike](https://boards.greenhouse.io/andurilindustries/jobs/5165226007?gh_jid=5165226007) — Costa Mesa, California, United States
- [Demand & Supply Planner, Precision Engagement Systems](https://boards.greenhouse.io/andurilindustries/jobs/5200161007?gh_jid=5200161007) — Costa Mesa, California, United States
- [Demand & Supply Planning, Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5200169007?gh_jid=5200169007) — Costa Mesa, California, United States
- [Demand & Supply Planning, Counter Intrusion](https://boards.greenhouse.io/andurilindustries/jobs/5200163007?gh_jid=5200163007) — Costa Mesa, California, United States
- [Demand & Supply Planning, Electronic Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5200180007?gh_jid=5200180007) — Costa Mesa, California, United States
- [Demand & Supply Planning, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/5200181007?gh_jid=5200181007) — Costa Mesa, California, United States
- [Deployment Coordination Analyst](https://boards.greenhouse.io/andurilindustries/jobs/5189372007?gh_jid=5189372007) — Costa Mesa, California, United States
- [Deployment Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5204368007?gh_jid=5204368007) — Broomfield, Colorado, United States; Fort Collins, Colorado, United States
- [Deployment Engineer, Anvil](https://boards.greenhouse.io/andurilindustries/jobs/4833091007?gh_jid=4833091007) — Costa Mesa, California, United States
- [Deployment Lead, Air Defense](https://boards.greenhouse.io/andurilindustries/jobs/5171009007?gh_jid=5171009007) — Irvine, California, United States
- [Deployment Lead, Maritime](https://boards.greenhouse.io/andurilindustries/jobs/5199224007?gh_jid=5199224007) — Irvine, California, United States
- [Deployment Lead, PACOM](https://boards.greenhouse.io/andurilindustries/jobs/5168364007?gh_jid=5168364007) — Okinawa, Japan
- [Deployment Operations Lead, Maritime Taiwan](https://boards.greenhouse.io/andurilindustries/jobs/5155380007?gh_jid=5155380007) — Taipei, Taiwan
- [Deployment Operations Manager, Roadrunner](https://boards.greenhouse.io/andurilindustries/jobs/5162926007?gh_jid=5162926007) — Irvine, California, United States
- [Deployment Operations Specialist, Maritime Taiwan](https://boards.greenhouse.io/andurilindustries/jobs/5161939007?gh_jid=5161939007) — Taipei, Taiwan
- [Deputy Chief Engineer, Autonomous Airpower](https://boards.greenhouse.io/andurilindustries/jobs/5062369007?gh_jid=5062369007) — Costa Mesa, California, United States
- [Deputy Chief Engineer, PES](https://boards.greenhouse.io/andurilindustries/jobs/5043104007?gh_jid=5043104007) — Costa Mesa, California, United States
- [Deputy Chief Engineer, TRS Edge Autonomy](https://boards.greenhouse.io/andurilindustries/jobs/5098951007?gh_jid=5098951007) — Costa Mesa, California, United States

_…truncated at 400 rows (3008 total)._

</details>
<!-- REQCON:END -->
