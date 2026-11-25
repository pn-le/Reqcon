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
**Last scan:** 2026-11-25 14:34 EST · 8 boards · 84 new · 94 removed

✅ Lila Sciences · ✅ BillionToOne · ✅ Anduril · ✅ Formlabs · ✅ STR · ⚠️ Draper · ✅ MERL (Mitsubishi Electric Research Labs) · ✅ Ubicept

### New this week

| Company | Role | Location | First seen |
|---|---|---|---|
| 🎓 Formlabs | [Events Logistics Intern (EMEA)](https://careers.formlabs.com/job/8416844/apply/?gh_jid=8416844) | Budapest, Hungary | 2026-11-25 |
| 🎓 Formlabs | [Software Engineer Intern (Full stack)](https://careers.formlabs.com/job/8416639/apply/?gh_jid=8416639) | Budapest, Hungary | 2026-11-25 |
| 🎓 Formlabs | [Campus Recruiting Intern (Winter/Spring 2027)](https://careers.formlabs.com/job/8413030/apply/?gh_jid=8413030) | Somerville, MA | 2026-11-24 |
| 🎓 Anduril | [Winter 2027 Test & Evaluation Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236583007?gh_jid=5236583007) | Costa Mesa, California, United States | 2026-11-23 |
| 🎓 Formlabs | [2027 (Summer) API & Automation Intern](https://careers.formlabs.com/job/8400855/apply/?gh_jid=8400855) | Somerville, MA | 2026-11-20 |
| 🎓 Formlabs | [2027 (Summer) Marketing Events Logistics Intern](https://careers.formlabs.com/job/8400561/apply/?gh_jid=8400561) | Somerville, MA | 2026-11-20 |
| 🎓 MERL (Mitsubishi Electric Research Labs) | [CV0361: Internship - Training Efficient Vision + Language Reasoning Models](https://www.merl.com/employment/internship-openings#CV0361) | — | 2026-11-20 |
| 🎓 MERL (Mitsubishi Electric Research Labs) | [OR0362: Internship - Robot Learning](https://www.merl.com/employment/internship-openings#OR0362) | — | 2026-11-20 |
| 🎓 Anduril | [2027 Engineering Systems Intern](https://boards.greenhouse.io/andurilindustries/jobs/5302147007?gh_jid=5302147007) | Costa Mesa, California, United States | 2026-11-19 |
| 🎓 Formlabs | [2027 (Summer) Marketing - Social Media Intern](https://careers.formlabs.com/job/8400491/apply/?gh_jid=8400491) | Somerville, MA | 2026-11-19 |
| 🎓 Formlabs | [Global Operations MBA Intern (Summer 2027)](https://careers.formlabs.com/job/8385550/apply/?gh_jid=8385550) | Somerville, MA | 2026-11-19 |
| 🎓 Formlabs | [Video Content Creator Intern (Summer 2027)](https://careers.formlabs.com/job/8395549/apply/?gh_jid=8395549) | Somerville, MA | 2026-11-19 |
| 🎓 MERL (Mitsubishi Electric Research Labs) | [CV0356: Internship - Embodied Multi-Agent Cooperation](https://www.merl.com/employment/internship-openings#CV0356) | — | 2026-11-19 |
| 🎓 MERL (Mitsubishi Electric Research Labs) | [CV0357: Internship - Physical AI Reasoning](https://www.merl.com/employment/internship-openings#CV0357) | — | 2026-11-19 |
| 🎓 MERL (Mitsubishi Electric Research Labs) | [CV0358: Internship - Multimodal Instruction and Video Synthesis](https://www.merl.com/employment/internship-openings#CV0358) | — | 2026-11-19 |
| 🎓 MERL (Mitsubishi Electric Research Labs) | [MS0359: Internship - Time Series Foundation Models](https://www.merl.com/employment/internship-openings#MS0359) | — | 2026-11-19 |
| 🎓 MERL (Mitsubishi Electric Research Labs) | [ST0360: Internship - Multimodal Tracking and Imaging](https://www.merl.com/employment/internship-openings#ST0360) | — | 2026-11-19 |
| Anduril | [ Maintenance Specialist, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/5307075007?gh_jid=5307075007) | Santa Ana, California, United States | 2026-11-25 |
| Anduril | [Aircraft Technician UAE, Omen](https://boards.greenhouse.io/andurilindustries/jobs/5307916007?gh_jid=5307916007) | Abu Dhabi, United Arab Emirates | 2026-11-25 |
| Anduril | [Benefits Specialist](https://boards.greenhouse.io/andurilindustries/jobs/5307188007?gh_jid=5307188007) | Costa Mesa, California, United States | 2026-11-25 |
| Anduril | [Buyer, Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5308901007?gh_jid=5308901007) | Costa Mesa, California, United States | 2026-11-25 |
| Anduril | [Buyer, Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5308942007?gh_jid=5308942007) | Costa Mesa, California, United States | 2026-11-25 |
| Anduril | [Data Analytics Lead, Corporate Planning & Operations](https://boards.greenhouse.io/andurilindustries/jobs/5308110007?gh_jid=5308110007) | Costa Mesa, California, United States | 2026-11-25 |
| Anduril | [Director, Business Development - Space Imaging](https://boards.greenhouse.io/andurilindustries/jobs/5225241007?gh_jid=5225241007) | Costa Mesa, California, United States | 2026-11-25 |
| Anduril | [Experimental Test Pilot UAE, Omen](https://boards.greenhouse.io/andurilindustries/jobs/5307912007?gh_jid=5307912007) | Abu Dhabi, United Arab Emirates | 2026-11-25 |
| Anduril | [Flight Software Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5309020007?gh_jid=5309020007) | Atlanta, Georgia, United States | 2026-11-25 |
| Anduril | [Flight Test Engineer - Advanced Effects (Missiles)](https://boards.greenhouse.io/andurilindustries/jobs/5308954007?gh_jid=5308954007) | Dallas, Texas, United States | 2026-11-25 |
| Anduril | [Flight Test Engineer UAE, Omen](https://boards.greenhouse.io/andurilindustries/jobs/5308294007?gh_jid=5308294007) | Abu Dhabi, United Arab Emirates; London, England, United Kingdom | 2026-11-25 |
| Anduril | [Flight Test Engineer UAE, Omen](https://boards.greenhouse.io/andurilindustries/jobs/5308296007?gh_jid=5308296007) | Abu Dhabi, United Arab Emirates; London, England, United Kingdom | 2026-11-25 |
| Anduril | [Flight Test Engineer UAE, Omen](https://boards.greenhouse.io/andurilindustries/jobs/5309508007?gh_jid=5309508007) | London, England, United Kingdom | 2026-11-25 |

…and 262 more — see the [latest digest](reports/reqcon-2026-11-25.md).

<details>
<summary>All tracked postings (3496)</summary>

**Lila Sciences** (114)
- 🎓 [Co-op, Agentic and Generative Protein Design](https://job-boards.greenhouse.io/lilasciences/jobs/4462613009) — Cambridge, MA USA; San Francisco, CA USA
- 🎓 [Co-Op, Agentic Simulations for Materials Science](https://job-boards.greenhouse.io/lilasciences/jobs/4465059009) — Cambridge, MA USA; San Francisco, CA USA
- 🎓 [Co-op, AI for Protein Design](https://job-boards.greenhouse.io/lilasciences/jobs/4480337009) — San Francisco, CA USA
- 🎓 [Co-Op, AI Nucleic Acid Design](https://job-boards.greenhouse.io/lilasciences/jobs/4465061009) — San Francisco, CA USA
- 🎓 [Co-Op, AI-Driven Equation Discovery](https://job-boards.greenhouse.io/lilasciences/jobs/4469152009) — Cambridge, MA USA; San Francisco, CA USA
- 🎓 [Co-Op, Automated Systems Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4462594009) — Cambridge, MA USA
- 🎓 [Co-Op, Bayesian Methods for Complex Decision Making](https://job-boards.greenhouse.io/lilasciences/jobs/4469148009) — Cambridge, MA USA; San Francisco, CA USA
- 🎓 [Co-Op, Characterization Electrodeposited Material ](https://job-boards.greenhouse.io/lilasciences/jobs/4462616009) — Cambridge, MA USA
- 🎓 [Co-Op, Editorial Content](https://job-boards.greenhouse.io/lilasciences/jobs/4472542009) — Cambridge, MA USA
- 🎓 [Co-Op, Electron Microscopy](https://job-boards.greenhouse.io/lilasciences/jobs/4469144009) — Cambridge, MA USA
- 🎓 [Co-Op, Finance](https://job-boards.greenhouse.io/lilasciences/jobs/4469146009) — Cambridge, MA USA
- 🎓 [Co-Op, IT/OT Security Analyst](https://job-boards.greenhouse.io/lilasciences/jobs/4477308009) — Cambridge, MA USA
- 🎓 [Co-Op, Materials Science, Heterogeneous Catalysis](https://job-boards.greenhouse.io/lilasciences/jobs/4465077009) — Cambridge, MA USA
- 🎓 [Co-op, Mechatronics Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4465068009) — Cambridge, MA USA
- 🎓 [Co-Op, Reaction Prediction & Benchmarking](https://job-boards.greenhouse.io/lilasciences/jobs/4465064009) — Cambridge, MA USA; San Francisco, CA USA
- 🎓 [Co-Op, Robot Perception & State Estimation](https://job-boards.greenhouse.io/lilasciences/jobs/4467398009) — Cambridge, MA USA
- 🎓 [Co-Op, SCADA Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4467407009) — Cambridge, MA USA
- 🎓 [Co-op, Software, Applied AI Platform Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4472540009) — San Francisco, CA USA
- 🎓 [Co-Op, Structuring Scientific Data for Discovery](https://job-boards.greenhouse.io/lilasciences/jobs/4469150009) — Cambridge, MA USA; San Francisco, CA USA
- [(Senior) Director, Portfolio Strategy, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4258093009) — Cambridge, MA USA
- [Associate Director / Director, Customer Program Management, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4184652009) — Cambridge, MA USA
- [Associate Director / Director, Customer Program Management, Physical Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4290011009) — Cambridge, MA USA
- [Associate Director / Director, Strategic Finance](https://job-boards.greenhouse.io/lilasciences/jobs/4353595009) — Cambridge, MA USA
- [Associate Director, Agentic Computational Platform](https://job-boards.greenhouse.io/lilasciences/jobs/4472546009) — Cambridge, MA USA; San Francisco, CA USA
- [Associate Director/Director, Commercial Counsel ](https://job-boards.greenhouse.io/lilasciences/jobs/4174259009) — Cambridge, MA USA; San Francisco, CA USA
- [Associate Director/Director, Frontier and AI Product Counsel](https://job-boards.greenhouse.io/lilasciences/jobs/4429017009) — Cambridge, MA USA; San Francisco, CA USA
- [Associate Director/Director, Inference Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4459902009) — Cambridge, MA USA; San Francisco, CA USA
- [Contractor, Robotics Lab Technician](https://job-boards.greenhouse.io/lilasciences/jobs/4412279009) — Cambridge, MA USA
- [Director / Senior Director, AI x Lab Integration](https://job-boards.greenhouse.io/lilasciences/jobs/4465079009) — Cambridge, MA USA; San Francisco, CA USA
- [Director / Senior Director, Intellectual Property, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4477305009) — Cambridge, MA USA; San Francisco, CA USA
- [Director of Product, Life Sciences (Chemistry)](https://job-boards.greenhouse.io/lilasciences/jobs/4048370009) — Cambridge, MA USA
- [Director, Enterprise Account Management, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4423498009) — Cambridge, MA USA
- [Director, Enterprise Account Management, Physical Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4423477009) — Cambridge, MA USA
- [Director, Materials AISF Program Lead](https://job-boards.greenhouse.io/lilasciences/jobs/4287216009) — Cambridge, MA USA
- [Director, Product Marketing, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4420035009) — Cambridge, MA USA
- [Director/ Senior Director, Lab Platform Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4458156009) — Cambridge, MA USA; San Francisco, CA USA
- [Director/ Senior Director, Product, Materials Chemistry](https://job-boards.greenhouse.io/lilasciences/jobs/4320806009) — Cambridge, MA USA
- [Engineer I, Research Operations (1st shift)](https://job-boards.greenhouse.io/lilasciences/jobs/4291695009) — Cambridge, MA USA
- [Engineer I, Research Operations, (1st shift)](https://job-boards.greenhouse.io/lilasciences/jobs/4277806009) — Cambridge, MA USA
- [Engineer II/ Senior Engineer, Robotics Platform Evaluation](https://job-boards.greenhouse.io/lilasciences/jobs/4404771009) — Cambridge, MA USA
- [Finance Business Partner, AI & Software](https://job-boards.greenhouse.io/lilasciences/jobs/4359832009) — Cambridge, MA USA
- [Head of Software Product](https://job-boards.greenhouse.io/lilasciences/jobs/4205624009) — Cambridge, MA USA; San Francisco, CA USA
- [Join Our Talent Community](https://job-boards.greenhouse.io/lilasciences/jobs/4070054009) — Cambridge, MA USA; San Francisco, CA USA
- [Lab IT/OT Systems Administrator](https://job-boards.greenhouse.io/lilasciences/jobs/4505109009) — Cambridge, MA USA
- [Lab Operations Manager](https://job-boards.greenhouse.io/lilasciences/jobs/4509101009) — Cambridge, MA USA
- [Machine Learning Engineer, Physical Sciences AI](https://job-boards.greenhouse.io/lilasciences/jobs/4116513009) — Cambridge, MA USA; San Francisco, CA USA
- [Machine Learning Research Scientist, Open-Endedness](https://job-boards.greenhouse.io/lilasciences/jobs/4215959009) — San Francisco, CA USA
- [Machine Learning Scientist, AI for Protein Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4392245009) — San Francisco, CA USA
- [Machine Learning Scientist, BioML](https://job-boards.greenhouse.io/lilasciences/jobs/4395729009) — San Francisco, CA USA
- [Machine Learning Scientist, Protein Design](https://job-boards.greenhouse.io/lilasciences/jobs/4396760009) — San Francisco, CA USA
- [Manager / Senior Manager, AI Safety Data and Evaluation Program](https://job-boards.greenhouse.io/lilasciences/jobs/4423490009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Manager / Senior Manager, Capital Equipment Accounting](https://job-boards.greenhouse.io/lilasciences/jobs/4195640009) — Cambridge, MA USA; San Francisco, CA USA
- [Manager / Senior Manager, Multimedia ](https://job-boards.greenhouse.io/lilasciences/jobs/4157130009) — Cambridge, MA USA
- [Manager / Senior Robotics Operations Manager](https://job-boards.greenhouse.io/lilasciences/jobs/4467396009) — Cambridge, MA USA
- [Manager / Senior Technical Program Manager](https://job-boards.greenhouse.io/lilasciences/jobs/4455695009) — Cambridge, MA USA
- [Manager, Revenue Accounting](https://job-boards.greenhouse.io/lilasciences/jobs/4195605009) — Cambridge, MA USA
- [Member of Technical Staff, AI Security](https://job-boards.greenhouse.io/lilasciences/jobs/4403714009) — Cambridge, MA USA
- [Microfabrication Scientist I/II](https://job-boards.greenhouse.io/lilasciences/jobs/4400746009) — Cambridge, MA USA
- [ML Research Engineer, Performance Optimization](https://job-boards.greenhouse.io/lilasciences/jobs/4455701009) — Cambridge, MA USA; San Francisco, CA USA
- [ML Research Scientist, Environments & Harnesses](https://job-boards.greenhouse.io/lilasciences/jobs/4462270009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [ML Research Scientist, Scientific Evaluations](https://job-boards.greenhouse.io/lilasciences/jobs/4472554009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [ML Scientist, Retrieval & RAG for Scientific Literature](https://job-boards.greenhouse.io/lilasciences/jobs/4477299009) — Cambridge, MA USA; San Francisco, CA USA
- [Platform Scientist I/II, Functional Materials Instrumentation](https://job-boards.greenhouse.io/lilasciences/jobs/4423504009) — Cambridge, MA USA
- [Portfolio Manager, Government Partnerships (DARPA & ARPA-H)](https://job-boards.greenhouse.io/lilasciences/jobs/4297690009) — Cambridge, MA USA
- [Principal Engineer, Software (Enterprise Platform)](https://job-boards.greenhouse.io/lilasciences/jobs/4247103009) — San Francisco, CA USA
- [Principal Machine Learning Engineer, Applied AI ](https://job-boards.greenhouse.io/lilasciences/jobs/4400744009) — Cambridge, MA USA; San Francisco, CA USA
- [Principal Network Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4373604009) — Cambridge, MA USA
- [Principal Scientist / Associate Director, Agentic AI Research for Materials Science](https://job-boards.greenhouse.io/lilasciences/jobs/4273850009) — Cambridge, MA USA; San Francisco, CA USA
- [Principal Software Engineer, App](https://job-boards.greenhouse.io/lilasciences/jobs/4248036009) — Cambridge, MA USA; San Francisco, CA USA
- [Principal Software Engineer, Applied AI](https://job-boards.greenhouse.io/lilasciences/jobs/4031455009) — Cambridge, MA USA; San Francisco, CA USA
- [Principal Software Engineer, Instrument Simulations](https://job-boards.greenhouse.io/lilasciences/jobs/4186530009) — Cambridge, MA USA
- [Research Engineer, Scientific Data & Workflow Infrastructure](https://job-boards.greenhouse.io/lilasciences/jobs/4286513009) — Cambridge, MA USA; San Francisco, CA USA
- [Research Scientist / Research Engineer, Automated Safety](https://job-boards.greenhouse.io/lilasciences/jobs/4423488009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Research Scientist, Computational Condensed Matter Physics](https://job-boards.greenhouse.io/lilasciences/jobs/4324886009) — Cambridge, MA USA
- [Research Scientist, Soft Matter Simulations](https://job-boards.greenhouse.io/lilasciences/jobs/4465081009) — Cambridge, MA USA; San Francisco, CA USA
- [Scientist I/II, Characterization and Composition Analysis](https://job-boards.greenhouse.io/lilasciences/jobs/4384606009) — Cambridge, MA USA
- [Scientist II / Senior Scientist, Electron Diffraction Characterization](https://job-boards.greenhouse.io/lilasciences/jobs/4378383009) — Cambridge, MA USA
- [Scientist II/ Senior ML Scientist,  Multimodal Scientific Data Extraction & Understanding](https://job-boards.greenhouse.io/lilasciences/jobs/4477297009) — Cambridge, MA USA; San Francisco, CA USA
- [Scientist II/Senior Characterization Scientist,  Condensed Matter](https://job-boards.greenhouse.io/lilasciences/jobs/4246305009) — Cambridge, MA USA
- [Scientist II/Senior Scientist, Solid-State Materials](https://job-boards.greenhouse.io/lilasciences/jobs/4271809009) — Cambridge, MA USA
- [Senior / Principal Chemist, AI Safety](https://job-boards.greenhouse.io/lilasciences/jobs/4423500009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Senior / Principal Computational Biologist, AI Safety](https://job-boards.greenhouse.io/lilasciences/jobs/4423494009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Senior / Principal Materials Scientist, AI Safety](https://job-boards.greenhouse.io/lilasciences/jobs/4423496009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Senior / Staff Machine Learning Engineer, Applied AI](https://job-boards.greenhouse.io/lilasciences/jobs/4302917009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior Automated Systems Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4110339009) — Cambridge, MA USA
- [Senior Data Engineer, Bioinformatics, Cheminformatics, Materials](https://job-boards.greenhouse.io/lilasciences/jobs/4377096009) — San Francisco, CA USA
- [Senior Director, Software Development, Test Automation](https://job-boards.greenhouse.io/lilasciences/jobs/4294875009) — San Francisco, CA USA
- [Senior II/ Staff Robotics Platform Evaluation Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4404934009) — Cambridge, MA USA
- [Senior II/ Staff Software Engineer, Platform Operations](https://job-boards.greenhouse.io/lilasciences/jobs/4212473009) — San Francisco, CA USA
- [Senior II/Staff Mechatronics Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4337828009) — Cambridge, MA USA
- [Senior Manager, Scientific Discovery Capacity Planning](https://job-boards.greenhouse.io/lilasciences/jobs/4359834009) — Cambridge, MA USA
- [Senior Manager, Scientific System of Record](https://job-boards.greenhouse.io/lilasciences/jobs/4378747009) — Cambridge, MA USA
- [Senior ML Scientist, AI for Protein Engineering](https://job-boards.greenhouse.io/lilasciences/jobs/4392247009) — San Francisco, CA USA
- [Senior ML Scientist, Biological Systems](https://job-boards.greenhouse.io/lilasciences/jobs/4395725009) — San Francisco, CA USA
- [Senior Research Associate , Automated Chemistry](https://job-boards.greenhouse.io/lilasciences/jobs/4254693009) — Cambridge, MA USA
- [Senior Scientist, Analytical Chemistry](https://job-boards.greenhouse.io/lilasciences/jobs/4192713009) — Cambridge, MA USA
- [Senior Software Engineer, App](https://job-boards.greenhouse.io/lilasciences/jobs/4248042009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior Software Engineer, Data](https://job-boards.greenhouse.io/lilasciences/jobs/4250077009) — Cambridge, MA USA; San Francisco, CA USA
- [Senior Software Engineer, Scientific System of Record](https://job-boards.greenhouse.io/lilasciences/jobs/4248049009) — Cambridge, MA USA; San Francisco, CA USA
- [Software Engineer, AI Platform](https://job-boards.greenhouse.io/lilasciences/jobs/4031328009) — Cambridge, MA USA
- [Specialist / Senior Procurement Specialist](https://job-boards.greenhouse.io/lilasciences/jobs/4420037009) — Cambridge, MA USA
- [Staff / Principal Automated Systems Engineer](https://job-boards.greenhouse.io/lilasciences/jobs/4110350009) — Cambridge, MA USA
- [Staff / Principal Research Engineer, AI Safety Mitigations](https://job-boards.greenhouse.io/lilasciences/jobs/4423492009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Staff / Principal Security Engineer, AI Safety and Security](https://job-boards.greenhouse.io/lilasciences/jobs/4429015009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Staff Engineer, Data Platform](https://job-boards.greenhouse.io/lilasciences/jobs/4222065009) — Cambridge, MA USA; San Francisco, CA USA
- [Staff Engineer, Enterprise Externalization](https://job-boards.greenhouse.io/lilasciences/jobs/4390579009) — San Francisco, CA USA
- [Staff Forward Deployed Engineer, Life Sciences](https://job-boards.greenhouse.io/lilasciences/jobs/4031282009) — Cambridge, MA USA; San Francisco, CA USA
- [Staff Forward Deployed Engineer, Physical Sciences (Level Flexible)](https://job-boards.greenhouse.io/lilasciences/jobs/4031303009) — Cambridge, MA USA; San Francisco, CA USA
- [Staff Software Engineer, AI Safety](https://job-boards.greenhouse.io/lilasciences/jobs/4423484009) — Cambridge, MA USA; London, UK; San Francisco, CA USA
- [Staff/ Principal Software Engineer, Scientific System of Record](https://job-boards.greenhouse.io/lilasciences/jobs/4193827009) — Cambridge, MA USA; San Francisco, CA USA
- [Staff/Principal Engineer, Search & Retrieval ](https://job-boards.greenhouse.io/lilasciences/jobs/4455692009) — San Francisco, CA USA
- [Supply Chain Demand Planner](https://job-boards.greenhouse.io/lilasciences/jobs/4423502009) — Cambridge, MA USA
- [Technical Program Manager, AI Data](https://job-boards.greenhouse.io/lilasciences/jobs/4259557009) — Cambridge, MA USA; San Francisco, CA USA
- [Technical Recruiter, AI Research](https://job-boards.greenhouse.io/lilasciences/jobs/4423474009) — Cambridge, MA USA; San Francisco, CA USA

**BillionToOne** (79)
- 🎓 [Research Associate Intern](https://job-boards.greenhouse.io/billiontoone/jobs/4747865005) — Menlo Park, CA
- [Account Support Representative](https://job-boards.greenhouse.io/billiontoone/jobs/4731424005) — Maryland, Washington, D.C., Eastern Virginia
- [Account Support Representative](https://job-boards.greenhouse.io/billiontoone/jobs/4750072005) — Missouri
- [Associate Creative Director](https://job-boards.greenhouse.io/billiontoone/jobs/4747883005) — Menlo Park, CA
- [Automation Engineer Associate II](https://job-boards.greenhouse.io/billiontoone/jobs/4744376005) — Union City, CA
- [Automation Service Engineer I/II, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4733813005) — Menlo Park, CA
- [Automation Service Engineering Associate I/II, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4736701005) — Menlo Park, CA
- [Bioinformatics Associate, Prenatal](https://job-boards.greenhouse.io/billiontoone/jobs/4757632005) — Menlo Park, CA
- [Client Services Associate I - Spanish, Prenatal (Temporary)](https://job-boards.greenhouse.io/billiontoone/jobs/4745213005) — Remote
- [Client Services Associate I, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4716882005) — Union City, CA
- [Client Services Associate I, Oncology (East Coast)](https://job-boards.greenhouse.io/billiontoone/jobs/4751445005) — New York, NY
- [Clinical Genomics Scientist, Prenatal (Part-Time Contractor)](https://job-boards.greenhouse.io/billiontoone/jobs/4758147005) — Remote
- [Clinical Laboratory Associate, Prenatal and Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4743708005) — Menlo Park or Union City, CA
- [Clinical Laboratory Scientist, Oncology (PM Shift) ](https://job-boards.greenhouse.io/billiontoone/jobs/4728398005) — Menlo Park, CA
- [Clinical Laboratory Scientist, Prenatal ](https://job-boards.greenhouse.io/billiontoone/jobs/4755919005) — Union City, CA
- [Clinical Laboratory Scientist, Prenatal (contractor)](https://job-boards.greenhouse.io/billiontoone/jobs/4728402005) — Union City, CA
- [Development Associate, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4749186005) — Menlo Park, CA
- [Director of IT](https://job-boards.greenhouse.io/billiontoone/jobs/4746677005) — Menlo Park, CA or Union City, CA
- [Director of Office of the CEO, Founder in Residence ](https://job-boards.greenhouse.io/billiontoone/jobs/4707633005) — Menlo Park, CA
- [General Supervisor, Prenatal](https://job-boards.greenhouse.io/billiontoone/jobs/4755918005) — Union City, CA
- [LIMS Associate, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4753550005) — Menlo Park, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4481121005) — Remote
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4689413005) — Roanoke, VA 
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4689420005) — Rochester, MN
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707158005) — Boston, MA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707168005) — Fresno, CA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707185005) — Milwaukee, WI
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707191005) — Omaha, NE
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707194005) — Portland, OR
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707205005) — South Seattle, WA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707206005) — Macon, GA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707207005) — Virginia Beach, VA
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4707209005) — Washington D.C., DC
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4717249005) — Eugene, OR
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4727611005) — Asheville, NC
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4740520005) — Wilmington, NC
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4743194005) — Knoxville, TN
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4751610005) — Albuquerque, NM
- [Oncology Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4751628005) — El Paso, TX
- [Oncology Medical Science Liaison](https://job-boards.greenhouse.io/billiontoone/jobs/4758136005) — Southern California
- [Oncology Regional Sales Manager, Gulf Coast](https://job-boards.greenhouse.io/billiontoone/jobs/4748932005) — Alabama, Arkansas, Georgia, Kentucky, Tennessee
- [Oncology Regional Sales Manager, Upper Midwest](https://job-boards.greenhouse.io/billiontoone/jobs/4667498005) — Minnesota, Wisconsin, North Dakota, South Dakota, Iowa, Nebraska, Missouri
- [Patient Billing Associate (Temporary)](https://job-boards.greenhouse.io/billiontoone/jobs/4748601005) — Remote
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4679905005) — Harrisburg, PA
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4702967005) — Roanoke, VA
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4718574005) — Frederick, MD
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4743052005) — Camden, NJ
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4747895005) — Colorado Springs, CO
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4747896005) — Columbus, GA
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4747898005) — Idaho Falls, ID
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4747899005) — Albuquerque, NM
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4747901005) — Omaha, NE
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4747902005) — Portland, OR
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4747904005) — South Tampa, FL
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4747905005) — Salt Lake City, UT
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4747908005) — St. George, UT
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4749213005) — Yakima, WA
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4749926005) — South Pittsburgh, PA
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4752788005) — East Bay, CA
- [Prenatal Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4753771005) — South Kansas City, MO
- [Prenatal Account Executive ](https://job-boards.greenhouse.io/billiontoone/jobs/4749922005) — Buffalo, NY
- [Prenatal Regional Sales Manager, Denver (CO)](https://job-boards.greenhouse.io/billiontoone/jobs/4749632005) — Denver, CO
- [Prenatal Regional Sales Manager, Great Plains](https://job-boards.greenhouse.io/billiontoone/jobs/4747910005) — Minnesota, Iowa, South Dakota, North Dakota
- [Prenatal Regional Sales Manager, Northern Los Angeles](https://job-boards.greenhouse.io/billiontoone/jobs/4707253005) — Northern California
- [Prenatal Senior Account Executive](https://job-boards.greenhouse.io/billiontoone/jobs/4747894005) — Remote
- [Reporting Clinical Laboratory Scientist (contractor)](https://job-boards.greenhouse.io/billiontoone/jobs/4747272005) — Union City, CA
- [Research Associate](https://job-boards.greenhouse.io/billiontoone/jobs/4747864005) — Menlo Park, CA
- [Senior Accounting Manager (Team Leader)](https://job-boards.greenhouse.io/billiontoone/jobs/4753500005) — Menlo Park, CA
- [Senior Director, Software Product Management and Product Engineering](https://job-boards.greenhouse.io/billiontoone/jobs/4745725005) — Menlo Park, CA
- [Senior IT Desktop Support Technician](https://job-boards.greenhouse.io/billiontoone/jobs/4720084005) — Menlo Park, CA
- [Senior LIMS Engineer, Prenatal](https://job-boards.greenhouse.io/billiontoone/jobs/4749225005) — Union City, CA
- [Senior Manager / Associate Director of Client Services](https://job-boards.greenhouse.io/billiontoone/jobs/4753184005) — Union City, CA
- [Senior Manager, Oncology Product Marketing](https://job-boards.greenhouse.io/billiontoone/jobs/4745804005) — Remote
- [Senior Marketing Specialist ](https://job-boards.greenhouse.io/billiontoone/jobs/4734273005) — Menlo Park, CA or Union City, CA
- [Senior Process Engineer, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4738692005) — Menlo Park, CA
- [Senior Product Manager, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4745966005) — Menlo Park, CA
- [Senior Stock Plan Administrator ](https://job-boards.greenhouse.io/billiontoone/jobs/4730826005) — Remote
- [Strategic Account Manager](https://job-boards.greenhouse.io/billiontoone/jobs/4747912005) — Remote
- [Vice President of Sales, Oncology](https://job-boards.greenhouse.io/billiontoone/jobs/4753269005) — United States

**Anduril** (2603)
- 🎓 [2027 Brand Marketing Intern](https://boards.greenhouse.io/andurilindustries/jobs/5261731007?gh_jid=5261731007) — Costa Mesa, California, United States
- 🎓 [2027 Business Operations Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5271672007?gh_jid=5271672007) — Ashville, Ohio, United States; Costa Mesa, California, United States
- 🎓 [2027 Business Operations Intern - Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5271826007?gh_jid=5271826007) — Costa Mesa, California, United States; Seattle, Washington, United States
- 🎓 [2027 Business Systems Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5300647007?gh_jid=5300647007) — Costa Mesa, California, United States
- 🎓 [2027 Deployment Operations Intern](https://boards.greenhouse.io/andurilindustries/jobs/5296825007?gh_jid=5296825007) — Quincy, Massachusetts, United States
- 🎓 [2027 Electrical Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5148101007?gh_jid=5148101007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- 🎓 [2027 Engineering Systems Intern](https://boards.greenhouse.io/andurilindustries/jobs/5302147007?gh_jid=5302147007) — Costa Mesa, California, United States
- 🎓 [2027 Field Test Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5268689007?gh_jid=5268689007) — Costa Mesa, California, United States; Quincy, Massachusetts, United States
- 🎓 [2027 Finance Data Analyst Intern](https://boards.greenhouse.io/andurilindustries/jobs/5269977007?gh_jid=5269977007) — Costa Mesa, California, United States
- 🎓 [2027 Firmware Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5265158007?gh_jid=5265158007) — Costa Mesa, California, United States
- 🎓 [2027 Flight Software Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5239083007?gh_jid=5239083007) — Costa Mesa, California, United States
- 🎓 [2027 Flight Test Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5257709007?gh_jid=5257709007) — Costa Mesa, California, United States
- 🎓 [2027 Guidance, Navigation, & Control Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5268736007?gh_jid=5268736007) — Costa Mesa, California, United States
- 🎓 [2027 Industrial Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5255593007?gh_jid=5255593007) — Ashville, Ohio, United States; Costa Mesa, California, United States
- 🎓 [2027 Industrial Equipment Maintenance Intern](https://boards.greenhouse.io/andurilindustries/jobs/5289632007?gh_jid=5289632007) — Ashville, Ohio, United States
- 🎓 [2027 Library Science Intern](https://boards.greenhouse.io/andurilindustries/jobs/5278662007?gh_jid=5278662007) — Santa Ana, California, United States
- 🎓 [2027 Low Observables Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5268752007?gh_jid=5268752007) — Costa Mesa, California, United States
- 🎓 [2027 Machine Learning Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5274037007?gh_jid=5274037007) — Santa Ana, California, United States
- 🎓 [2027 Manufacturing Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5153218007?gh_jid=5153218007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Seattle, Washington, United States
- 🎓 [2027 Mechanical Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5153187007?gh_jid=5153187007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- 🎓 [2027 Mission Operations Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5297134007?gh_jid=5297134007) — Honolulu, Hawaii, United States; Washington, District of Columbia, United States
- 🎓 [2027 Optical Payload Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5291546007?gh_jid=5291546007) — Costa Mesa, California, United States
- 🎓 [2027 Product Data Quality Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5273039007?gh_jid=5273039007) — Santa Ana, California, United States
- 🎓 [2027 Product Designer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5265097007?gh_jid=5265097007) — Costa Mesa, California, United States
- 🎓 [2027 Product Marketing Intern](https://boards.greenhouse.io/andurilindustries/jobs/5261735007?gh_jid=5261735007) — Costa Mesa, California, United States
- 🎓 [2027 Product Sourcing Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5271285007?gh_jid=5271285007) — Costa Mesa, California, United States; Irvine, California, United States; Santa Ana, California, United States
- 🎓 [2027 Quality & Test Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5257674007?gh_jid=5257674007) — Ashville, Ohio, United States; Costa Mesa, California, United States; Irvine, California, United States; Quonset, Rhode Island, United States; Santa Ana, California, United States
- 🎓 [2027 Reliability Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5257682007?gh_jid=5257682007) — Costa Mesa, California, United States
- 🎓 [2027 Software Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5148079007?gh_jid=5148079007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- 🎓 [2027 Supply Chain Intern](https://boards.greenhouse.io/andurilindustries/jobs/5255827007?gh_jid=5255827007) — Costa Mesa, California, United States; Fort Collins, Colorado, United States; Quincy, Massachusetts, United States; Santa Ana, California, United States; Waltham, Massachusetts, United States
- 🎓 [2027 Systems Engineer Intern](https://boards.greenhouse.io/andurilindustries/jobs/5257690007?gh_jid=5257690007) — Boston, Massachusetts, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Reston, Virginia, United States; Seattle, Washington, United States
- 🎓 [2027 Technical Program Manager Intern](https://boards.greenhouse.io/andurilindustries/jobs/5268864007?gh_jid=5268864007) — Costa Mesa, California, United States; Honolulu, Hawaii, United States; Reston, Virginia, United States; Seattle, Washington, United States; Washington, District of Columbia, United States
- 🎓 [Fall 2027 Manufacturing Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5280611007?gh_jid=5280611007) — Ashville, Ohio, United States; Quincy, Massachusetts, United States; Santa Ana, California, United States
- 🎓 [Winter 2027 Business Operations Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5271686007?gh_jid=5271686007) — Ashville, Ohio, United States; Costa Mesa, California, United States
- 🎓 [Winter 2027 Electrical Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236565007?gh_jid=5236565007) — Costa Mesa, California, United States; Quincy, Massachusetts, United States
- 🎓 [Winter 2027 Manufacturing Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236589007?gh_jid=5236589007) — Ashville, Ohio, United States; Lexington, Massachusetts, United States; Quincy, Massachusetts, United States; Quonset, Rhode Island, United States
- 🎓 [Winter 2027 Quality & Test Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5257571007?gh_jid=5257571007) — Ashville, Ohio, United States; Santa Ana, California, United States
- 🎓 [Winter 2027 Reliability Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5257693007?gh_jid=5257693007) — Costa Mesa, California, United States
- 🎓 [Winter 2027 Software Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236563007?gh_jid=5236563007) — Quincy, Massachusetts, United States
- 🎓 [Winter 2027 Supply Chain Analyst Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236592007?gh_jid=5236592007) — Quincy, Massachusetts, United States
- 🎓 [Winter 2027 Systems Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236599007?gh_jid=5236599007) — Quincy, Massachusetts, United States
- 🎓 [Winter 2027 Technical Program Management Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236571007?gh_jid=5236571007) — Washington, District of Columbia, United States
- 🎓 [Winter 2027 Test & Evaluation Engineer Co-op](https://boards.greenhouse.io/andurilindustries/jobs/5236583007?gh_jid=5236583007) — Costa Mesa, California, United States
- [ Development Test Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5287568007?gh_jid=5287568007) — Costa Mesa, California, United States
- [ Emerging Talent Recruiter](https://boards.greenhouse.io/andurilindustries/jobs/5277422007?gh_jid=5277422007) — Boston, Massachusetts, United States
- [ FPGA Engineer, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/5147059007?gh_jid=5147059007) — Reston, Virginia, United States
- [ Head of Maintenance Repair & Overhaul](https://boards.greenhouse.io/andurilindustries/jobs/5148720007?gh_jid=5148720007) — Costa Mesa, California, United States
- [ Leadership Development Designer & Facilitator (Manufacturing) ](https://boards.greenhouse.io/andurilindustries/jobs/5240674007?gh_jid=5240674007) — Ashville, Ohio, United States
- [ Low Observables Engineer, RCS](https://boards.greenhouse.io/andurilindustries/jobs/4418353007?gh_jid=4418353007) — Costa Mesa, California, United States
- [ Maintenance Specialist, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/5307075007?gh_jid=5307075007) — Santa Ana, California, United States
- [ Manufacturing Engineer, Production, Sentry](https://boards.greenhouse.io/andurilindustries/jobs/5085941007?gh_jid=5085941007) — Irvine, California, United States
- [ Manufacturing Test Engineer, Missiles](https://boards.greenhouse.io/andurilindustries/jobs/5254383007?gh_jid=5254383007) — Costa Mesa, California, United States
- [ Manufacturing Test Engineer, Missiles](https://boards.greenhouse.io/andurilindustries/jobs/5254434007?gh_jid=5254434007) — Ashville, Ohio, United States
- [ Mechanical Engineer, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/5293515007?gh_jid=5293515007) — Santa Ana, California, United States
- [ Mechanical Engineer, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/5298926007?gh_jid=5298926007) — Reston, Virginia, United States
- [ Recruiting Lead](https://boards.greenhouse.io/andurilindustries/jobs/5278804007?gh_jid=5278804007) — Costa Mesa, California, United States
- [ Senior Aerodynamics Engineer, Air Vehicles](https://boards.greenhouse.io/andurilindustries/jobs/4629832007?gh_jid=4629832007) — Costa Mesa, California, United States
- [ Senior Discovery Engineer (Modeling & Simulation) ](https://boards.greenhouse.io/andurilindustries/jobs/5252658007?gh_jid=5252658007) — Boston, Massachusetts, United States; Waltham, Massachusetts, United States
- [ Senior FPGA Engineer, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/4591133007?gh_jid=4591133007) — Reston, Virginia, United States
- [ Senior Manager, Emerging Talent Programs](https://boards.greenhouse.io/andurilindustries/jobs/5291358007?gh_jid=5291358007) — Seattle, Washington, United States
- [ Senior Reliability Engineer, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/5268453007?gh_jid=5268453007) — Reston, Virginia, United States
- [ Senior Security Engineer, Identity](https://boards.greenhouse.io/andurilindustries/jobs/5259074007?gh_jid=5259074007) — Washington, District of Columbia, United States
- [ Senior Supplier Quality Engineer, Composites](https://boards.greenhouse.io/andurilindustries/jobs/5134865007?gh_jid=5134865007) — Costa Mesa, California, United States
- [ Senior System Safety Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5266274007?gh_jid=5266274007) — Costa Mesa, California, United States
- [ Senior Technical Recruiter, Contractor Mission Systems](https://boards.greenhouse.io/andurilindustries/jobs/5014749007?gh_jid=5014749007) — Boulder, Colorado, United States; Waltham, Massachusetts, United States
- [ Software Engineer, Discovery](https://boards.greenhouse.io/andurilindustries/jobs/5242907007?gh_jid=5242907007) — Boston, Massachusetts, United States; Costa Mesa, California, United States; Washington, District of Columbia, United States
- [ Software Engineering Manager (ArsenalOS Deployment)](https://boards.greenhouse.io/andurilindustries/jobs/5291774007?gh_jid=5291774007) — Santa Ana, California, United States
- [ VP Production, Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5173257007?gh_jid=5173257007) — Costa Mesa, California, United States
- [(PIPELINE) Advanced Effects - Buyer](https://boards.greenhouse.io/andurilindustries/jobs/5264682007?gh_jid=5264682007) — Ashville, Ohio, United States
- [(Pipeline) Structural Analyst, Space Emerging Talent](https://boards.greenhouse.io/andurilindustries/jobs/5239598007?gh_jid=5239598007) — Costa Mesa, California, United States
- [2026 Early Career Electrical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/4802172007?gh_jid=4802172007) — Costa Mesa, California, United States; Fort Collins, Colorado, United States
- [2026 Early Career Manufacturing Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5176254007?gh_jid=5176254007) — Costa Mesa, California, United States; Irvine, California, United States; Santa Ana, California, United States
- [2026 Early Career Mechanical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/4802167007?gh_jid=4802167007) — Costa Mesa, California, United States
- [2026 Early Career Test & Evaluation Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5196267007?gh_jid=5196267007) — Channel Islands, California, United States
- [2027 Early Career Associate Product Designer](https://boards.greenhouse.io/andurilindustries/jobs/5265088007?gh_jid=5265088007) — Costa Mesa, California, United States
- [2027 Early Career Business Operations Analyst](https://boards.greenhouse.io/andurilindustries/jobs/5271811007?gh_jid=5271811007) — Costa Mesa, California, United States; Seattle, Washington, United States; Washington, District of Columbia, United States
- [2027 Early Career Division Operations](https://boards.greenhouse.io/andurilindustries/jobs/5261363007?gh_jid=5261363007) — Reston, Virginia, United States
- [2027 Early Career Electrical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5136925007?gh_jid=5136925007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- [2027 Early Career Electrical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5272501007?gh_jid=5272501007) — Dublin, Dublin, Ireland
- [2027 Early Career Firmware Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5246141007?gh_jid=5246141007) — Costa Mesa, California, United States
- [2027 Early Career Flight Software Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5228868007?gh_jid=5228868007) — Costa Mesa, California, United States
- [2027 Early Career Flight Test Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5246225007?gh_jid=5246225007) — Costa Mesa, California, United States
- [2027 Early Career Industrial Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5236921007?gh_jid=5236921007) — Ashville, Ohio, United States
- [2027 Early Career Manufacturing Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5136970007?gh_jid=5136970007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Seattle, Washington, United States
- [2027 Early Career Mechanical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5136984007?gh_jid=5136984007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- [2027 Early Career Mechanical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5258587007?gh_jid=5258587007) — Dublin, Dublin, Ireland
- [2027 Early Career Quality Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5262324007?gh_jid=5262324007) — Ashville, Ohio, United States; Costa Mesa, California, United States; Irvine, California, United States; Quonset, Rhode Island, United States; Santa Ana, California, United States
- [2027 Early Career Software Development in Test](https://boards.greenhouse.io/andurilindustries/jobs/5270953007?gh_jid=5270953007) — Dublin, Dublin, Ireland
- [2027 Early Career Software Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5272481007?gh_jid=5272481007) — Dublin, Dublin, Ireland
- [2027 Early Career Software Engineer ](https://boards.greenhouse.io/andurilindustries/jobs/5162263007?gh_jid=5162263007) — Atlanta, Georgia, United States; Boston, Massachusetts, United States; Broomfield, Colorado, United States; Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Fort Collins, Colorado, United States; Irvine, California, United States; Reston, Virginia, United States; Seattle, Washington, United States
- [2027 Early Career Supply Chain Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5268564007?gh_jid=5268564007) — Costa Mesa, California, United States
- [2027 Early Career Systems Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5262340007?gh_jid=5262340007) — Boston, Massachusetts, United States; Boulder, Colorado, United States; Costa Mesa, California, United States; Foothill Ranch, California, United States; Huntsville, Alabama, United States; Reston, Virginia, United States; Seattle, Washington, United States; Washington, District of Columbia, United States
- [2027 Early Career Technical Program Manager](https://boards.greenhouse.io/andurilindustries/jobs/5268883007?gh_jid=5268883007) — Costa Mesa, California, United States; Seattle, Washington, United States; Washington, District of Columbia, United States
- [2027 Early Career Test & Evaluation Operations Analyst](https://boards.greenhouse.io/andurilindustries/jobs/5296757007?gh_jid=5296757007) — Costa Mesa, California, United States
- [2027 Early Career Test & Quality Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5266291007?gh_jid=5266291007) — Dublin, Dublin, Ireland
- [2027 Early Career Warhead Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5268704007?gh_jid=5268704007) — Costa Mesa, California, United States
- [2027 New Grad GNC Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5270855007?gh_jid=5270855007) — Costa Mesa, California, United States
- [2027 New Grad Information Security Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5270839007?gh_jid=5270839007) — Costa Mesa, California, United States
- [2027 New Grad Low Observables Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5269789007?gh_jid=5269789007) — Costa Mesa, California, United States
- [Acceptance Test Procedure Technician, Roadrunner](https://boards.greenhouse.io/andurilindustries/jobs/5116801007?gh_jid=5116801007) — Ashville, Ohio, United States
- [Account Director, Maritime](https://boards.greenhouse.io/andurilindustries/jobs/5210043007?gh_jid=5210043007) — Sydney, New South Wales, Australia
- [Account Director, Maritime](https://boards.greenhouse.io/andurilindustries/jobs/5210045007?gh_jid=5210045007) — Canberra, Australian Capital Territory, Australia
- [Accounts Payable Specialist](https://boards.greenhouse.io/andurilindustries/jobs/5290454007?gh_jid=5290454007) — Sydney, New South Wales, Australia
- [Accounts Payable Specialist](https://boards.greenhouse.io/andurilindustries/jobs/5301127007?gh_jid=5301127007) — Amsterdam, North Holland, Netherlands
- [Actuation Engineer, Air Maneuver Dominance](https://boards.greenhouse.io/andurilindustries/jobs/5217256007?gh_jid=5217256007) — Costa Mesa, California, United States
- [AD&S, Air Vehicle Software Systems Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5131822007?gh_jid=5131822007) — Costa Mesa, California, United States
- [Advanced Effects -Senior Buyer](https://boards.greenhouse.io/andurilindustries/jobs/5292581007?gh_jid=5292581007) — Ashville, Ohio, United States
- [Advanced Effects -Senior Buyer](https://boards.greenhouse.io/andurilindustries/jobs/5292582007?gh_jid=5292582007) — Costa Mesa, California, United States
- [Aerodynamics Engineer, Air Vehicles](https://boards.greenhouse.io/andurilindustries/jobs/5000486007?gh_jid=5000486007) — Costa Mesa, California, United States
- [Aerodynamics Engineer, Hypersonic Air Vehicles](https://boards.greenhouse.io/andurilindustries/jobs/5032351007?gh_jid=5032351007) — Costa Mesa, California, United States
- [AFSIM Operations Analyst, Mission Engineering, Air Dominance & Strike, Active Clearance](https://boards.greenhouse.io/andurilindustries/jobs/5103907007?gh_jid=5103907007) — Ashville, Ohio, United States; Costa Mesa, California, United States
- [Air Vehicle Lead, Missiles](https://boards.greenhouse.io/andurilindustries/jobs/5211965007?gh_jid=5211965007) — Costa Mesa, California, United States
- [Air Vehicle Systems Engineer, Hardware Verification, Integration & Validation](https://boards.greenhouse.io/andurilindustries/jobs/5131979007?gh_jid=5131979007) — Costa Mesa, California, United States
- [Air Vehicle Systems Verification Lead](https://boards.greenhouse.io/andurilindustries/jobs/5131984007?gh_jid=5131984007) — Costa Mesa, California, United States
- [Air-Vehicle Multidisciplinary Design Analysis and Optimization (MDAO) Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5132442007?gh_jid=5132442007) — Costa Mesa, California, United States
- [Aircraft Technician UAE, Omen](https://boards.greenhouse.io/andurilindustries/jobs/5307916007?gh_jid=5307916007) — Abu Dhabi, United Arab Emirates
- [Aircraft Technician, Omen](https://boards.greenhouse.io/andurilindustries/jobs/5302803007?gh_jid=5302803007) — Costa Mesa, California, United States
- [Airworthiness Engineer, Rotary Aircraft](https://boards.greenhouse.io/andurilindustries/jobs/5235387007?gh_jid=5235387007) — Costa Mesa, California, United States
- [Algorithm Developer, Tracking Systems](https://boards.greenhouse.io/andurilindustries/jobs/5226940007?gh_jid=5226940007) — Broomfield, Colorado, United States; Fort Collins, Colorado, United States
- [Algorithm Engineer, Tracking Systems](https://boards.greenhouse.io/andurilindustries/jobs/5226941007?gh_jid=5226941007) — Broomfield, Colorado, United States; Fort Collins, Colorado, United States
- [Altius - Product Sourcing Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5140464007?gh_jid=5140464007) — Atlanta, Georgia, United States
- [Altius - Product Sourcing Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5223799007?gh_jid=5223799007) — Costa Mesa, California, United States
- [Altius - Senior Product Sourcing Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5205961007?gh_jid=5205961007) — Costa Mesa, California, United States
- [Analytical Chemist](https://boards.greenhouse.io/andurilindustries/jobs/5291422007?gh_jid=5291422007) — McHenry, Mississippi, United States
- [Analytics Engineer, Hardware Test](https://boards.greenhouse.io/andurilindustries/jobs/4768437007?gh_jid=4768437007) — Costa Mesa, California, United States
- [Antenna RF Engineer, EW](https://boards.greenhouse.io/andurilindustries/jobs/5231092007?gh_jid=5231092007) — Costa Mesa, California, United States
- [Assembly Integration and Test Engineer, Space Systems](https://boards.greenhouse.io/andurilindustries/jobs/5266880007?gh_jid=5266880007) — Costa Mesa, California, United States
- [Asset Improvement Manager, East](https://boards.greenhouse.io/andurilindustries/jobs/5293893007?gh_jid=5293893007) — Washington, District of Columbia, United States
- [Asset Improvements Project Manager ](https://boards.greenhouse.io/andurilindustries/jobs/5280417007?gh_jid=5280417007) — Costa Mesa, California, United States
- [Assistant Contractor Special Security Officer](https://boards.greenhouse.io/andurilindustries/jobs/5262829007?gh_jid=5262829007) — Washington, District of Columbia, United States
- [Assistant Contractor Special Security Officer](https://boards.greenhouse.io/andurilindustries/jobs/5290285007?gh_jid=5290285007) — Chantilly, Virginia, United States
- [Associate Director, Business Development - Tactical Recon and Strike (International)](https://boards.greenhouse.io/andurilindustries/jobs/5298951007?gh_jid=5298951007) — Washington, District of Columbia, United States
- [Associate Director, Business Development, Federal Civilian Counter-UAS](https://boards.greenhouse.io/andurilindustries/jobs/5176542007?gh_jid=5176542007) — Washington, District of Columbia, United States
- [Associate Director, Business Development, Federal Civilian Counter-UAS](https://boards.greenhouse.io/andurilindustries/jobs/5178152007?gh_jid=5178152007) — Costa Mesa, California, United States
- [Associate Director, Corporate Planning & Operations](https://boards.greenhouse.io/andurilindustries/jobs/4964602007?gh_jid=4964602007) — Costa Mesa, California, United States
- [Associate Director, Government Relations](https://boards.greenhouse.io/andurilindustries/jobs/5267543007?gh_jid=5267543007) — Washington, District of Columbia, United States
- [Associate Director, Kitchen Operations - West Coast](https://boards.greenhouse.io/andurilindustries/jobs/5256115007?gh_jid=5256115007) — Costa Mesa, California, United States
- [Associate Director, Production (Missiles)](https://boards.greenhouse.io/andurilindustries/jobs/5241195007?gh_jid=5241195007) — Costa Mesa, California, United States
- [Associate Director, Production (Missiles) - International Growth](https://boards.greenhouse.io/andurilindustries/jobs/5250418007?gh_jid=5250418007) — Costa Mesa, California, United States
- [Associate Director, Production (Roadrunner)](https://boards.greenhouse.io/andurilindustries/jobs/5215053007?gh_jid=5215053007) — Ashville, Ohio, United States
- [Associate Mechanical Engineer, Actuators](https://boards.greenhouse.io/andurilindustries/jobs/5286571007?gh_jid=5286571007) — Costa Mesa, California, United States
- [Associate People Business Partner](https://boards.greenhouse.io/andurilindustries/jobs/5277479007?gh_jid=5277479007) — Ashville, Ohio, United States
- [Associate People Business Partner](https://boards.greenhouse.io/andurilindustries/jobs/5285469007?gh_jid=5285469007) — Waltham, Massachusetts, United States
- [Associate Workplace Manager](https://boards.greenhouse.io/andurilindustries/jobs/5265105007?gh_jid=5265105007) — Costa Mesa, California, United States
- [Automation & Torque Tooling Technician](https://boards.greenhouse.io/andurilindustries/jobs/5227022007?gh_jid=5227022007) — Costa Mesa, California, United States
- [Automation Engineer, General](https://boards.greenhouse.io/andurilindustries/jobs/5239028007?gh_jid=5239028007) — Costa Mesa, California, United States
- [Automation Engineer, Manufacturing Automation](https://boards.greenhouse.io/andurilindustries/jobs/5234628007?gh_jid=5234628007) — Costa Mesa, California, United States
- [Autonomous Flight Test Engineer, Rotorcraft](https://boards.greenhouse.io/andurilindustries/jobs/5206291007?gh_jid=5206291007) — Costa Mesa, California, United States
- [Autonomous Senior Flight Test Engineer,  Rotorcraft ](https://boards.greenhouse.io/andurilindustries/jobs/5189391007?gh_jid=5189391007) — Costa Mesa, California, United States
- [Avionics Systems Engineer, Space ](https://boards.greenhouse.io/andurilindustries/jobs/5300687007?gh_jid=5300687007) — Costa Mesa, California, United States
- [Battery Mechanical Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5290138007?gh_jid=5290138007) — Costa Mesa, California, United States
- [Battery Systems Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5290158007?gh_jid=5290158007) — Costa Mesa, California, United States
- [Battery Test Technician](https://boards.greenhouse.io/andurilindustries/jobs/5130695007?gh_jid=5130695007) — Costa Mesa, California, United States
- [Benefits Specialist](https://boards.greenhouse.io/andurilindustries/jobs/5307188007?gh_jid=5307188007) — Costa Mesa, California, United States
- [BOM Sourcing Engineer, Intelligence Systems & Space (Active Clearance)](https://boards.greenhouse.io/andurilindustries/jobs/5029722007?gh_jid=5029722007) — Costa Mesa, California, United States
- [BOM Sourcing Engineer, Supply Chain](https://boards.greenhouse.io/andurilindustries/jobs/5174509007?gh_jid=5174509007) — Costa Mesa, California, United States
- [Business Operations Analyst, Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5213194007?gh_jid=5213194007) — Seattle, Washington, United States
- [Business Operations Associate](https://boards.greenhouse.io/andurilindustries/jobs/4951316007?gh_jid=4951316007) — Costa Mesa, California, United States
- [Business Operations Associate - Technical Projects](https://boards.greenhouse.io/andurilindustries/jobs/4951318007?gh_jid=4951318007) — Costa Mesa, California, United States
- [Business Operations Engineer, Air Dominance & Strike ](https://boards.greenhouse.io/andurilindustries/jobs/5111193007?gh_jid=5111193007) — Costa Mesa, California, United States
- [Business Operations Lead](https://boards.greenhouse.io/andurilindustries/jobs/4951325007?gh_jid=4951325007) — Costa Mesa, California, United States
- [Business Operations Lead - Technical Projects](https://boards.greenhouse.io/andurilindustries/jobs/5117374007?gh_jid=5117374007) — Costa Mesa, California, United States
- [Business Operations, Anduril](https://boards.greenhouse.io/andurilindustries/jobs/5219004007?gh_jid=5219004007) — Costa Mesa, California, United States
- [Buyer](https://boards.greenhouse.io/andurilindustries/jobs/5282085007?gh_jid=5282085007) — Costa Mesa, California, United States
- [Buyer ](https://boards.greenhouse.io/andurilindustries/jobs/5300640007?gh_jid=5300640007) — Hudson, New Hampshire, United States
- [Buyer - Altius 600](https://boards.greenhouse.io/andurilindustries/jobs/5302018007?gh_jid=5302018007) — Atlanta, Georgia, United States
- [Buyer, Advanced Effects](https://boards.greenhouse.io/andurilindustries/jobs/5219013007?gh_jid=5219013007) — Costa Mesa, California, United States
- [Buyer, Autonomous Airpower Hardware Procurement](https://boards.greenhouse.io/andurilindustries/jobs/4802276007?gh_jid=4802276007) — Costa Mesa, California, United States
- [Buyer, Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5308901007?gh_jid=5308901007) — Costa Mesa, California, United States
- [Buyer, Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5308942007?gh_jid=5308942007) — Costa Mesa, California, United States
- [Buyer, Intelligence Systems & Space ](https://boards.greenhouse.io/andurilindustries/jobs/5252055007?gh_jid=5252055007) — Costa Mesa, California, United States
- [Buyer, Mission Systems](https://boards.greenhouse.io/andurilindustries/jobs/5222695007?gh_jid=5222695007) — Irvine, California, United States
- [C++ Engineer, High-Performance Systems](https://boards.greenhouse.io/andurilindustries/jobs/5226945007?gh_jid=5226945007) — Broomfield, Colorado, United States; Fort Collins, Colorado, United States
- [CAD Administrator](https://boards.greenhouse.io/andurilindustries/jobs/5256520007?gh_jid=5256520007) — Costa Mesa, California, United States
- [CAD Administrator](https://boards.greenhouse.io/andurilindustries/jobs/5256522007?gh_jid=5256522007) — Seattle, Washington, United States
- [CAD Administrator](https://boards.greenhouse.io/andurilindustries/jobs/5256524007?gh_jid=5256524007) — Mountain View, California, United States
- [CAD Drafter](https://boards.greenhouse.io/andurilindustries/jobs/5247471007?gh_jid=5247471007) — Costa Mesa, California, United States
- [CAD Drafter, Counter Intrusion](https://boards.greenhouse.io/andurilindustries/jobs/5277829007?gh_jid=5277829007) — Irvine, California, United States
- [CAD Systems Architect](https://boards.greenhouse.io/andurilindustries/jobs/5262845007?gh_jid=5262845007) — Costa Mesa, California, United States
- [Calibration Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5201431007?gh_jid=5201431007) — Costa Mesa, California, United States
- [Channel Relationship Manager, Connected Warfare](https://boards.greenhouse.io/andurilindustries/jobs/5092442007?gh_jid=5092442007) — Washington, District of Columbia, United States
- [Chemical Manufacturing Technician](https://boards.greenhouse.io/andurilindustries/jobs/5285225007?gh_jid=5285225007) — McHenry, Mississippi, United States
- [Chief Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5228068007?gh_jid=5228068007) — Costa Mesa, California, United States
- [Chief Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5255071007?gh_jid=5255071007) — Costa Mesa, California, United States
- [Chief Engineer - Tactical Effects](https://boards.greenhouse.io/andurilindustries/jobs/5254633007?gh_jid=5254633007) — Costa Mesa, California, United States
- [Chief Engineer, Advanced Effects (Hypersonics) ](https://boards.greenhouse.io/andurilindustries/jobs/5252457007?gh_jid=5252457007) — Costa Mesa, California, United States
- [Chief Engineer, Advanced Effects (Missiles) ](https://boards.greenhouse.io/andurilindustries/jobs/5226623007?gh_jid=5226623007) — Costa Mesa, California, United States
- [Chief Engineer, Air Defense, Middle East Programs](https://boards.greenhouse.io/andurilindustries/jobs/5248044007?gh_jid=5248044007) — Huntsville, Alabama, United States; Irvine, California, United States; Seattle, Washington, United States; Washington, District of Columbia, United States
- [Chief Engineer, Autonomous Flight](https://boards.greenhouse.io/andurilindustries/jobs/5158222007?gh_jid=5158222007) — Costa Mesa, California, United States; Seattle, Washington, United States; Washington, District of Columbia, United States
- [Chief Engineer, Containerized Effects](https://boards.greenhouse.io/andurilindustries/jobs/5290206007?gh_jid=5290206007) — Costa Mesa, California, United States
- [Chief Engineer, Conventional ISR](https://boards.greenhouse.io/andurilindustries/jobs/5172075007?gh_jid=5172075007) — Costa Mesa, California, United States
- [Chief Engineer, Copperhead](https://boards.greenhouse.io/andurilindustries/jobs/5251222007?gh_jid=5251222007) — Quincy, Massachusetts, United States
- [Chief Engineer, Dive-LD](https://boards.greenhouse.io/andurilindustries/jobs/5251191007?gh_jid=5251191007) — Quincy, Massachusetts, United States
- [Chief Engineer, FQ-44 Fury](https://boards.greenhouse.io/andurilindustries/jobs/5081020007?gh_jid=5081020007) — Costa Mesa, California, United States
- [Chief Engineer, Fury Advanced Concepts](https://boards.greenhouse.io/andurilindustries/jobs/5218065007?gh_jid=5218065007) — Costa Mesa, California, United States
- [Chief Engineer, Fury Advanced Development & Prototyping](https://boards.greenhouse.io/andurilindustries/jobs/5060066007?gh_jid=5060066007) — Costa Mesa, California, United States
- [Chief Engineer, Intelligence Systems](https://boards.greenhouse.io/andurilindustries/jobs/5294564007?gh_jid=5294564007) — Reston, Virginia, United States
- [Chief Engineer, Launcher Systems](https://boards.greenhouse.io/andurilindustries/jobs/5307006007?gh_jid=5307006007) — Costa Mesa, California, United States
- [Chief Engineer, Navy Airpower](https://boards.greenhouse.io/andurilindustries/jobs/5172083007?gh_jid=5172083007) — Costa Mesa, California, United States
- [Chief Engineer, USMC, Air Defense](https://boards.greenhouse.io/andurilindustries/jobs/5284445007?gh_jid=5284445007) — Huntsville, Alabama, United States; Irvine, California, United States; Seattle, Washington, United States; Washington, District of Columbia, United States
- [Chief Engineers, Advanced Aircraft Programs](https://boards.greenhouse.io/andurilindustries/jobs/5087403007?gh_jid=5087403007) — Costa Mesa, California, United States
- [Chief Integration Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5287645007?gh_jid=5287645007) — McHenry, Mississippi, United States
- [Chief of Staff, Production](https://boards.greenhouse.io/andurilindustries/jobs/5251746007?gh_jid=5251746007) — Costa Mesa, California, United States
- [Chief Software Engineer, Space Ground Systems ](https://boards.greenhouse.io/andurilindustries/jobs/5145121007?gh_jid=5145121007) — Colorado Springs, Colorado, United States; Costa Mesa, California, United States; Washington, District of Columbia, United States
- [Circuit Designer, Space Special Programs](https://boards.greenhouse.io/andurilindustries/jobs/5169876007?gh_jid=5169876007) — Chantilly, Virginia, United States
- [Classified Cloud & Platform Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5269017007?gh_jid=5269017007) — Costa Mesa, California, United States
- [Classified Cloud & Platform Engineer](https://boards.greenhouse.io/andurilindustries/jobs/5271233007?gh_jid=5271233007) — Washington, District of Columbia, United States

_…truncated at 400 rows (3496 total)._

</details>
<!-- REQCON:END -->
