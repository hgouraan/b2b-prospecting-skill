import json, os, shutil, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import validate

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "examples", "synthetic-sample")

class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.r = os.path.join(self.d, "run")
        shutil.copytree(SAMPLE, self.r)
    def tearDown(self):
        shutil.rmtree(self.d)
    def v(self):
        return validate.validate(self.r)
    def edit(self, path, fn):
        p = os.path.join(self.r, path)
        obj = json.load(open(p))
        fn(obj)
        json.dump(obj, open(p, "w"))
    def edit_text(self, path, old, new):
        p = os.path.join(self.r, path)
        t = open(p).read()
        assert old in t, f"{old} not in {path}"
        open(p, "w").write(t.replace(old, new, 1))

    def test_sample_valid(self):
        self.assertEqual(self.v(), {"valid": True, "errors": []})
    def test_missing_file(self):
        os.remove(os.path.join(self.r, "accounts.csv"))
        self.assertFalse(self.v()["valid"])
    def test_duplicate_domain(self):
        import csv as _csv
        pth = os.path.join(self.r, "accounts.csv")
        rows = list(_csv.reader(open(pth)))
        rows[2][2] = rows[1][2]  # copy row1 domain into row2
        with open(pth, "w", newline="") as fh:
            _csv.writer(fh).writerows(rows)
        self.assertFalse(self.v()["valid"])
    def test_below_threshold(self):
        self.edit_text("qualified-leads.csv", "target_segment=40", "target_segment=10")
        self.assertFalse(self.v()["valid"])
    def test_score_sum_mismatch(self):
        p = os.path.join(self.r, "qualified-leads.csv")
        t = open(p).read()
        assert ",80," in t
        t = t.replace(",80,", ",81,", 1)
        open(p, "w").write(t)
        self.assertFalse(self.v()["valid"])
    def test_fabricated_email(self):
        self.edit_text("outreach-drafts.md", "مرحباً،", "مرحباً، contact me at sara@realcompany.com")
        self.assertFalse(self.v()["valid"])
    def test_suppressed_in_drafts(self):
        self.edit_text("outreach-drafts.md", "DRAFT ONLY - NOT SENT", "DRAFT ONLY - NOT SENT\nA-003")
        self.assertFalse(self.v()["valid"])
    def test_missing_brief(self):
        import glob
        os.remove(sorted(glob.glob(os.path.join(self.r, "account-briefs", "*.md")))[0])
        self.assertFalse(self.v()["valid"])
    def test_brief_without_provenance(self):
        import glob
        p = sorted(glob.glob(os.path.join(self.r, "account-briefs", "*.md")))[0]
        t = open(p).read().replace("## Provenance", "## Sources")
        open(p, "w").write(t)
        self.assertFalse(self.v()["valid"])
    def test_draft_marker_removed(self):
        self.edit_text("outreach-drafts.md", "DRAFT ONLY - NOT SENT", "READY TO SEND")
        self.assertFalse(self.v()["valid"])
    def test_disq_empty_reason(self):
        p = os.path.join(self.r, "disqualified-leads.csv")
        lines = open(p).read().splitlines()
        parts = lines[1].rsplit(",", 1)
        lines[1] = parts[0] + ','
        open(p, "w").write("\n".join(lines) + "\n")
        self.assertFalse(self.v()["valid"])
    def test_bad_state_status(self):
        self.edit("state.json", lambda v: v.update(status="done"))
        self.assertFalse(self.v()["valid"])
    def test_export_nonqualified(self):
        p = os.path.join(self.r, "crm-export.csv")
        with open(p, "a") as fh:
            fh.write("A-003,X,x.example,clinics,Saudi Arabia,80\n")
        self.assertFalse(self.v()["valid"])

if __name__ == "__main__":
    unittest.main()
