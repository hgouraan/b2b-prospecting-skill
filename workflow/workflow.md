# Workflow

Phases follow the execution graph in `workflow.mmd`; machine gate definitions live in `gates.yaml`.

## 1. ICP
Turn the offer into icp.md (segments, buyer pains, positive signals, disqualifiers, priorities) and segment-map.md. Human review before import: wrong ICP invalidates every later artifact.

## 2. Import / discovery
Default is importing an approved CSV. Web research happens only with user-authorized tools and compliant public sources. Every material claim (size, funding, signals, market) gets a source-register.csv row: source_ref, captured_date (YYYY-MM-DD), confidence (high|medium|low). Normalize into accounts.csv keyed by canonical domain; one row per organization. Duplicates are merged or flagged in the notes column - never silently dropped.

## 3. Scoring
scoring-config.yaml defines weighted rules and the qualification threshold. Each lead's score_components must sum to score_total. qualified-leads.csv holds rows at or above threshold; disqualified-leads.csv holds the rest, each with a non-empty reason. Scores judge company fit only. No emails, phone numbers, named contacts, funding or headcount may be invented: unknown stays empty and counts as zero.

## 4. Briefs
One account-briefs/<account_id>.md per qualified account. Each brief ends with a `## Provenance` section listing the source-register refs behind its claims.

## 5. Drafts
outreach-drafts.md starts with the line `DRAFT ONLY - NOT SENT`. One tailored draft per qualified account. Any account_id on the suppression list (input.json `suppressed_account_ids`) must not appear in drafts or qualified-leads.csv. Sending is out of scope and requires separate explicit user approval plus authorized tools.

## 6. Export
crm-export.csv contains qualified accounts only, with the documented column mapping (see docs/usage.md).

## Failure and resume
Missing critical inputs, unverifiable material claims, unresolved duplicates or missing suppression handling set state.json status to `blocked` or `needs_review` with blocker details. Resume from the last human-reviewed artifact; never silently replace it.
