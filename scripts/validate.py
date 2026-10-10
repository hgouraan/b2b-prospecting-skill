#!/usr/bin/env python3
"""Deterministic contract validator for a b2b-prospecting run directory.

Read-only. Checks file contracts only; it cannot judge fit quality, source
legitimacy or consent. Exit 0 with {"valid": true} on pass, 1 on failures.
"""
import csv, io, json, os, re, sys

ACCOUNTS_HEADERS = ["account_id", "name", "canonical_domain", "segment", "country", "notes"]
LEAD_HEADERS = ["account_id", "name", "score_total", "score_components", "reasons"]
SOURCE_HEADERS = ["source_id", "source_ref", "captured_date", "confidence", "claims"]
STATE_FIELDS = ["run_id", "skill_version", "phase", "status", "completed_phases", "timestamps"]
STATUSES = {"not_started", "in_progress", "blocked", "needs_review", "approved", "rejected", "completed"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def parse_config(path):
    """Minimal flat-YAML parse: threshold: N and a weights: map of name: N."""
    threshold, weights = None, {}
    in_weights = False
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("threshold:"):
            threshold = float(s.split(":", 1)[1])
        elif s == "weights:":
            in_weights = True
        elif in_weights and ":" in s:
            k, v = s.split(":", 1)
            weights[k.strip()] = float(v)
    return threshold, weights

def validate(run):
    errors = []
    def need(p):
        if not os.path.isfile(os.path.join(run, p)):
            errors.append(f"missing file: {p}")
            return False
        return True

    ok_state = need("state.json")
    for p in ["icp.md", "segment-map.md", "source-register.csv", "accounts.csv",
              "scoring-config.yaml", "qualified-leads.csv", "disqualified-leads.csv",
              "outreach-drafts.md", "crm-export.csv", "input.json"]:
        need(p)
    if errors:
        return {"valid": False, "errors": errors}

    # state
    state = json.load(open(os.path.join(run, "state.json"), encoding="utf-8"))
    for f in STATE_FIELDS:
        if f not in state:
            errors.append(f"state.json missing field: {f}")
    if state.get("status") not in STATUSES:
        errors.append(f"state.json bad status: {state.get('status')}")

    inp = json.load(open(os.path.join(run, "input.json"), encoding="utf-8"))
    suppressed = set(inp.get("suppressed_account_ids", []))

    # accounts: headers, unique ids, unique canonical domains
    accounts = read_csv(os.path.join(run, "accounts.csv"))
    if accounts:
        for h in ACCOUNTS_HEADERS:
            if h not in accounts[0]:
                errors.append(f"accounts.csv missing header: {h}")
        ids = [r["account_id"] for r in accounts]
        if len(ids) != len(set(ids)):
            errors.append("accounts.csv duplicate account_id")
        doms = [r["canonical_domain"].lower().strip() for r in accounts]
        if len(doms) != len(set(doms)):
            errors.append("accounts.csv duplicate canonical_domain (dedup incomplete)")
        for r in accounts:
            if not r["canonical_domain"].strip():
                errors.append(f"accounts.csv {r['account_id']}: empty canonical_domain")

    # source register
    src = read_csv(os.path.join(run, "source-register.csv"))
    if src:
        for h in SOURCE_HEADERS:
            if h not in src[0]:
                errors.append(f"source-register.csv missing header: {h}")
        for r in src:
            if not DATE_RE.match(r.get("captured_date", "")):
                errors.append(f"source-register.csv {r.get('source_id')}: bad captured_date")
            if r.get("confidence") not in {"high", "medium", "low"}:
                errors.append(f"source-register.csv {r.get('source_id')}: bad confidence")

    # scoring
    threshold, _ = parse_config(os.path.join(run, "scoring-config.yaml"))
    if threshold is None:
        errors.append("scoring-config.yaml missing threshold")
    qual = read_csv(os.path.join(run, "qualified-leads.csv"))
    disq = read_csv(os.path.join(run, "disqualified-leads.csv"))
    for label, rows in [("qualified-leads.csv", qual), ("disqualified-leads.csv", disq)]:
        if rows:
            for h in LEAD_HEADERS:
                if h not in rows[0]:
                    errors.append(f"{label} missing header: {h}")
    for r in qual:
        comp = r.get("score_components", "")
        try:
            total = sum(float(p.split("=")[1]) for p in comp.split(";") if p)
        except Exception:
            errors.append(f"qualified-leads.csv {r.get('account_id')}: unparseable score_components")
            continue
        if abs(total - float(r["score_total"])) > 1e-6:
            errors.append(f"qualified-leads.csv {r.get('account_id')}: components do not sum to score_total")
        if threshold is not None and total < threshold:
            errors.append(f"qualified-leads.csv {r.get('account_id')}: below threshold {threshold}")
        if not r.get("reasons", "").strip():
            errors.append(f"qualified-leads.csv {r.get('account_id')}: empty reasons")
        if r.get("account_id") in suppressed:
            errors.append(f"qualified-leads.csv {r.get('account_id')}: suppressed account present")
    for r in disq:
        if not r.get("reasons", "").strip():
            errors.append(f"disqualified-leads.csv {r.get('account_id')}: empty reasons")

    # no fabricated contacts anywhere in lead files
    for label in ["qualified-leads.csv", "disqualified-leads.csv", "accounts.csv"]:
        text = open(os.path.join(run, label), encoding="utf-8").read()
        for m in EMAIL_RE.findall(text):
            if not m.endswith(".example"):
                errors.append(f"{label}: possible fabricated contact email: {m}")

    # briefs: one per qualified account, with provenance
    brief_dir = os.path.join(run, "account-briefs")
    briefs = {os.path.splitext(f)[0] for f in os.listdir(brief_dir)} if os.path.isdir(brief_dir) else set()
    for r in qual:
        b = r["account_id"]
        if b not in briefs:
            errors.append(f"missing account brief for qualified account: {b}")
        else:
            body = open(os.path.join(brief_dir, b + ".md"), encoding="utf-8").read()
            if "## Provenance" not in body:
                errors.append(f"account-briefs/{b}.md missing ## Provenance section")
    extra = briefs - {r["account_id"] for r in qual}
    if extra:
        errors.append(f"briefs without qualified account: {sorted(extra)}")

    # drafts: draft-only marker, no emails, no suppressed ids
    drafts = open(os.path.join(run, "outreach-drafts.md"), encoding="utf-8").read()
    if not drafts.lstrip().startswith("DRAFT ONLY - NOT SENT"):
        errors.append("outreach-drafts.md must start with 'DRAFT ONLY - NOT SENT'")
    for m in EMAIL_RE.findall(drafts):
        if not m.endswith(".example"):
            errors.append(f"outreach-drafts.md contains an email address: {m}")
    for s in suppressed:
        if s in drafts:
            errors.append(f"outreach-drafts.md mentions suppressed account: {s}")

    # export: qualified ids only
    exp = read_csv(os.path.join(run, "crm-export.csv"))
    qids = {r["account_id"] for r in qual}
    for r in exp:
        if r.get("account_id") not in qids:
            errors.append(f"crm-export.csv contains non-qualified account: {r.get('account_id')}")

    return {"valid": not errors, "errors": errors}

if __name__ == "__main__":
    result = validate(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["valid"] else 1)
