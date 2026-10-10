# Usage
1. Copy templates/ to runs/<run_id>/ and fill input.json (offer, ICP, geography, segments, rules, disqualifiers, channels, suppressed_account_ids).
2. Write icp.md and segment-map.md; get human review.
3. Import your prospect CSV; normalize to accounts.csv (one row per canonical domain). Log claims in source-register.csv.
4. Set weights and threshold in scoring-config.yaml; fill qualified-leads.csv and disqualified-leads.csv. score_components uses `name=value;...` and must sum to score_total.
5. One account-briefs/<account_id>.md per qualified account with a ## Provenance section.
6. outreach-drafts.md starts with `DRAFT ONLY - NOT SENT`; no email addresses, no suppressed accounts. Human review; sending is out of scope.
7. crm-export.csv contains qualified accounts only: account_id, company, domain, segment, country, score.
Run `python3 scripts/validate.py runs/<run_id>` after each phase.
