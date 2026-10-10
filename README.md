# B2B Prospecting Agent
A file-first, evidence-first workflow for BD managers and founders: turn an offer into an ICP, deduplicate a prospect list, score fit transparently, write account briefs, and prepare draft-only outreach for human review.

**v0.1.0 pre-release.** Early public release of an experimental workflow: the synthetic example and deterministic checks pass, but it has not been piloted on a real prospecting program. Treat it as a starting point, not a production-validated system. Licensed under MIT.

## Five-minute sample
Requirements: a Markdown reader; optional Python 3.10+ standard library for checks.

```sh
python3 scripts/validate.py examples/synthetic-sample
python3 -m unittest discover -s tests -v
```
The checked-in sample is a complete fictional run (30 raw import rows with duplicates and gaps -> 24 deduplicated accounts, 14 qualified, 10 disqualified with reasons, draft-only outreach). It produces a JSON report with `valid` and `errors`. It does not send anything, contact anyone, or verify that any company exists.

Sample input: `examples/synthetic-sample/input.json` + `import-raw.csv`. Sample output: `accounts.csv`, `qualified-leads.csv`, `outreach-drafts.md`.

## Workflow
ICP -> import/discovery -> normalize + dedup -> source and freshness register -> weighted fit scoring -> account briefs -> draft-only outreach -> CRM export. Human review gates every phase.

Mermaid source: [workflow/workflow.mmd](workflow/workflow.mmd). Full gates and recovery: [workflow/workflow.md](workflow/workflow.md).

## Start a real run
1. Read [SKILL.md](SKILL.md) and [docs/usage.md](docs/usage.md).
2. Copy templates to `runs/your-run/`. Supply your own offer, ICP, and prospect CSV. Do not copy synthetic companies or approvals.
3. Keep every material claim in source-register.csv with a source reference, capture date, and confidence. Unknown fields stay empty and score zero - never fabricate contacts, funding, headcount, or signals.
4. Validate with `python3 scripts/validate.py runs/your-run`. The validator checks contracts; it cannot judge fit, verify sources, or establish consent.
5. Human review decides every gate. Sending any draft is out of scope and needs separate explicit approval and authorized tools.

## What this does not do
No bulk sending, contact harvesting, scraping behind logins or robots restrictions, social DM automation, CRM writes, or compliance guarantees. Compliance and consent remain the user's responsibility. See [limitations](docs/limitations.md), [security](SECURITY.md), and [contributing](CONTRIBUTING.md).
