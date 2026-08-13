#!/usr/bin/env python3
"""One-shot authoring helper for the v0.2 seed expansion. Idempotent."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tasks"
LICENSE = "Synthetic fixture, original work, free to use"


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n")


def write_task(task_id: str, meta: dict, gold: dict, diff: str, context: dict[str, str] | None = None) -> None:
    d = ROOT / task_id
    dump(d / "task.json", meta)
    dump(d / "gold.json", gold)
    (d / "diff.patch").write_text(diff if diff.endswith("\n") else diff + "\n")
    if context:
        for rel, body in context.items():
            p = d / "context" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body if body.endswith("\n") else body + "\n")


# --- T004 -----------------------------------------------------------------
write_task(
    "T004_readme_typo",
    {
        "id": "T004_readme_typo",
        "family": "T",
        "title": "One-word README typo",
        "language": "markdown",
        "tags": ["noise", "docs", "triage"],
        "difficulty": 1,
        "source": "synthetic",
        "license_note": LICENSE,
        "pr_title": "docs: fix typo in README",
        "pr_body": "typo",
        "author": "agent-bot-7",
        "files_changed": 1,
        "additions": 1,
        "deletions": 1,
    },
    {
        "triage_label": "likely_low_value",
        "triage_priority": 0.05,
        "findings": [],
        "rationale": "Single-character docs fix. Spend zero scarce review budget here.",
    },
    """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -12,7 +12,7 @@
-Quickstart for local developement.
+Quickstart for local development.
""",
)

# --- T005 -----------------------------------------------------------------
write_task(
    "T005_drive_by_reformat",
    {
        "id": "T005_drive_by_reformat",
        "family": "T",
        "title": "Repo-wide formatter drive-by",
        "language": "python",
        "tags": ["noise", "formatting", "volume", "triage"],
        "difficulty": 1,
        "source": "synthetic",
        "license_note": LICENSE,
        "pr_title": "chore: apply black and isort everywhere",
        "pr_body": "formatting pass. no behavior change.",
        "author": "agent-bot-7",
        "files_changed": 41,
        "additions": 280,
        "deletions": 260,
    },
    {
        "triage_label": "likely_low_value",
        "triage_priority": 0.08,
        "findings": [],
        "rationale": "Formatter-only churn across the tree. High token cost, near-zero review value. Classic AI-volume waste.",
    },
    """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,4 +1,4 @@
-from flask import Flask,request
+from flask import Flask, request
 # ... 40 more files of import-sort / quote / wrap churn omitted ...
""",
)

# --- T006 -----------------------------------------------------------------
write_task(
    "T006_large_security_fix",
    {
        "id": "T006_large_security_fix",
        "family": "T",
        "title": "Real session-fixation fix buried in a large PR",
        "language": "python",
        "tags": ["security", "session", "volume", "triage"],
        "difficulty": 3,
        "source": "synthetic",
        "license_note": LICENSE,
        "pr_title": "fix: rotate session on privilege change and harden cookie flags",
        "pr_body": "Security fix for session fixation after role elevation.\n\nRoot cause: login and promote_user reused the pre-auth session id.\nPlan: rotate session, set Secure/HttpOnly/SameSite, add regression tests.\nAlso includes the supporting middleware extract that made the bug possible — the PR is large because the session helper moved modules.",
        "author": "core-maintainer",
        "files_changed": 28,
        "additions": 510,
        "deletions": 340,
    },
    {
        "triage_label": "needs_human",
        "triage_priority": 0.92,
        "findings": [],
        "rationale": "Size is a terrible proxy here. The change is a real session-fixation fix with tests. A structural heuristic that punishes LOC/file count will bury it under formatter noise. Gold is needs_human — this is the budgeted-capture stress case.",
    },
    """diff --git a/src/auth/session.py b/src/auth/session.py
--- a/src/auth/session.py
+++ b/src/auth/session.py
@@ -20,8 +20,14 @@ def promote_user(request, user_id, role):
     user.role = role
     db.commit()
-    # keep existing session so the UI does not log the user out
-    return user
+    # SECURITY: privilege change must rotate the session id
+    request.session.rotate()
+    request.session["uid"] = user.id
+    return user
diff --git a/src/auth/cookies.py b/src/auth/cookies.py
--- a/src/auth/cookies.py
+++ b/src/auth/cookies.py
@@ -4,7 +4,10 @@ def set_session_cookie(resp, sid):
-    resp.set_cookie("sid", sid)
+    resp.set_cookie("sid", sid, secure=True, httponly=True, samesite="Lax")
diff --git a/tests/test_session.py b/tests/test_session.py
--- a/tests/test_session.py
+++ b/tests/test_session.py
@@ -1,3 +1,12 @@
+def test_promote_rotates_session(client):
+    sid = client.login("ada")
+    client.promote("ada", "admin")
+    assert client.cookies["sid"] != sid
# ... supporting middleware move across ~25 files omitted; metadata reflects full PR size ...
""",
)

# --- T007 -----------------------------------------------------------------
write_task(
    "T007_chore_with_tests",
    {
        "id": "T007_chore_with_tests",
        "family": "T",
        "title": "Rename + snapshot tests, no behavior change",
        "language": "typescript",
        "tags": ["noise", "tests", "chore", "triage"],
        "difficulty": 2,
        "source": "synthetic",
        "license_note": LICENSE,
        "pr_title": "chore: rename formatUsd helper and update snapshots",
        "pr_body": "chore: rename helper for consistency. formatting only, snapshots updated. no behavior change.",
        "author": "core-maintainer",
        "files_changed": 2,
        "additions": 22,
        "deletions": 18,
    },
    {
        "triage_label": "likely_low_value",
        "triage_priority": 0.12,
        "findings": [],
        "rationale": "Tests are present, so a structural heuristic will inflate priority. The change is a rename plus snapshot churn. Attention waste if it occupies a scarce review slot.",
    },
    """diff --git a/src/money.ts b/src/money.ts
--- a/src/money.ts
+++ b/src/money.ts
@@ -1,4 +1,4 @@
-export function formatUsd(n: number) {
+export function formatUSD(n: number) {
   return `$${n.toFixed(2)}`
 }
diff --git a/src/money.test.ts b/src/money.test.ts
--- a/src/money.test.ts
+++ b/src/money.test.ts
@@ -1,6 +1,6 @@
-import { formatUsd } from './money'
+import { formatUSD } from './money'
-test('formats', () => expect(formatUsd(2)).toBe('$2.00'))
+test('formats', () => expect(formatUSD(2)).toBe('$2.00'))
""",
)

# --- T008 -----------------------------------------------------------------
write_task(
    "T008_silent_schema_drop",
    {
        "id": "T008_silent_schema_drop",
        "family": "T",
        "title": "Drops a live column described as unused cleanup",
        "language": "python",
        "tags": ["data", "schema", "triage", "domain"],
        "difficulty": 3,
        "source": "synthetic",
        "license_note": LICENSE,
        "pr_title": "chore: remove unused accrual_basis column",
        "pr_body": "typo cleanup and unused field. readme only mention. chore.",
        "author": "agent-bot-7",
        "files_changed": 2,
        "additions": 6,
        "deletions": 14,
    },
    {
        "triage_label": "needs_human",
        "triage_priority": 0.88,
        "findings": [],
        "rationale": "The PR *says* unused. Context shows payroll reports still group on accrual_basis. A dropped live column is a silent production break. Structural signals (tiny, chore, typo) all point the wrong way.",
    },
    """diff --git a/migrations/0042_drop_accrual.py b/migrations/0042_drop_accrual.py
--- /dev/null
+++ b/migrations/0042_drop_accrual.py
@@ -0,0 +1,6 @@
+def upgrade(db):
+    db.execute("ALTER TABLE pay_runs DROP COLUMN accrual_basis")
+
+def downgrade(db):
+    db.execute("ALTER TABLE pay_runs ADD COLUMN accrual_basis text")
diff --git a/src/models/pay_run.py b/src/models/pay_run.py
--- a/src/models/pay_run.py
+++ b/src/models/pay_run.py
@@ -8,7 +8,6 @@ class PayRun:
     id: str
     tenant_id: str
     period_end: date
-    accrual_basis: str
     posted_at: datetime | None
""",
    {
        "src/reports/payroll.py": (
            "# Year-end T4 / RL-1 grouping. Do not drop pay_runs.accrual_basis — "
            "Quebec and federal filings split cash vs accrual runs.\n"
            "def group_for_filing(runs):\n"
            "    return {r.accrual_basis: r for r in runs}\n"
        )
    },
)

# --- T009 -----------------------------------------------------------------
write_task(
    "T009_midsize_feature",
    {
        "id": "T009_midsize_feature",
        "family": "T",
        "title": "Ordinary feature, known author, no tests",
        "language": "typescript",
        "tags": ["feature", "triage"],
        "difficulty": 1,
        "source": "synthetic",
        "license_note": LICENSE,
        "pr_title": "feat: add CSV export of invoice list",
        "pr_body": "Adds a CSV download on the invoices index.\n\nPlan:\n1. Serialize current filtered rows\n2. Stream as text/csv\nNo new permissions — uses the existing list endpoint authz.",
        "author": "core-maintainer",
        "files_changed": 4,
        "additions": 96,
        "deletions": 8,
    },
    {
        "triage_label": "vouching_required",
        "triage_priority": 0.45,
        "findings": [],
        "rationale": "Real product change, known author, no tests. Worth a skim (export + authz assumptions) but not a first-slot security review. vouching_required is the honest middle.",
    },
    """diff --git a/src/invoices/export.ts b/src/invoices/export.ts
--- /dev/null
+++ b/src/invoices/export.ts
@@ -0,0 +1,12 @@
+export function toCsv(rows: Invoice[]) {
+  const header = 'id,total,status'
+  const body = rows.map(r => [r.id, r.total, r.status].join(',')).join('\\n')
+  return header + '\\n' + body
+}
""",
)

# --- T010 -----------------------------------------------------------------
write_task(
    "T010_lockfile_bump",
    {
        "id": "T010_lockfile_bump",
        "family": "T",
        "title": "Dependabot lockfile-only bump",
        "language": "javascript",
        "tags": ["noise", "deps", "triage"],
        "difficulty": 1,
        "source": "synthetic",
        "license_note": LICENSE,
        "pr_title": "chore(deps): bump left-pad from 1.3.0 to 1.3.1",
        "pr_body": "chore",
        "author": "dependabot",
        "files_changed": 1,
        "additions": 3,
        "deletions": 3,
    },
    {
        "triage_label": "likely_low_value",
        "triage_priority": 0.06,
        "findings": [],
        "rationale": "Patch-level lockfile bump of an unused toy dep. Do not spend a human slot.",
    },
    """diff --git a/package-lock.json b/package-lock.json
--- a/package-lock.json
+++ b/package-lock.json
@@ -80,7 +80,7 @@
-        "left-pad": "1.3.0"
+        "left-pad": "1.3.1"
""",
)

# --- F003 -----------------------------------------------------------------
write_task(
    "F003_csrf_dropped",
    {
        "id": "F003_csrf_dropped",
        "family": "F",
        "title": "Form POST drops CSRF check, comments say gateway handles it",
        "language": "python",
        "tags": ["security", "csrf", "findings"],
        "difficulty": 2,
        "source": "synthetic",
        "license_note": LICENSE,
        "pr_title": "refactor: simplify payout form handler",
        "pr_body": "Moves CSRF to the edge gateway so handlers stay thin. No client change.",
        "author": "platform-eng",
        "files_changed": 1,
        "additions": 8,
        "deletions": 9,
    },
    {
        "triage_label": None,
        "triage_priority": None,
        "findings": [
            {
                "id": "F-csrf-removed",
                "path": "src/payouts/views.py",
                "title": "CSRF validation removed from state-changing payout POST",
                "severity": "critical",
                "rationale": "The handler still accepts a browser cookie session. Comment claims the gateway checks CSRF, but this route is also mounted on the internal app without that gateway. State-changing money POST with no CSRF is a substantive defect.",
                "anchor": "csrf",
            }
        ],
        "rationale": "Structural heuristics looking for tenant/id lookups will miss this. The defect is an omitted check, not a new unsafe query.",
    },
    """diff --git a/src/payouts/views.py b/src/payouts/views.py
--- a/src/payouts/views.py
+++ b/src/payouts/views.py
@@ -10,12 +10,8 @@ def create_payout():
     if request.method != "POST":
         return render("payouts/new.html")
-    if not csrf.validate(request):
-        abort(403)
+    # CSRF is enforced at the CDN gateway now
     amount = Decimal(request.form["amount"])
     dest = request.form["account"]
     ledger.transfer(current_user.id, dest, amount)
     return redirect("/payouts")
""",
    {
        "src/app.py": (
            "# create_payout is registered on both public_app (behind CDN) and "
            "internal_app (no CDN, cookie auth still on).\n"
            "internal_app.add_url_rule('/payouts', view_func=create_payout, methods=['POST'])\n"
        )
    },
)

# --- F004 -----------------------------------------------------------------
write_task(
    "F004_jurisdiction_tz",
    {
        "id": "F004_jurisdiction_tz",
        "family": "F",
        "title": "Payroll cutoff uses naive local now()",
        "language": "python",
        "tags": ["domain", "payroll", "timezone", "findings"],
        "difficulty": 3,
        "source": "synthetic",
        "license_note": LICENSE,
        "pr_title": "feat: auto-close pay periods at midnight",
        "pr_body": "Closes the current pay period automatically so ops does not have to click it.",
        "author": "payroll-eng",
        "files_changed": 1,
        "additions": 14,
        "deletions": 2,
    },
    {
        "triage_label": None,
        "triage_priority": None,
        "findings": [
            {
                "id": "F-naive-tz-cutoff",
                "path": "src/payroll/periods.py",
                "title": "Period close uses datetime.now() instead of jurisdiction timezone",
                "severity": "high",
                "rationale": "Quebec and Atlantic employees are not in the host's local TZ. A naive midnight close on a US-east or UTC box files the wrong calendar day for QPP / federal remittance cutoffs. Domain defect: 'correct' is jurisdiction wall-clock, not server now().",
                "anchor": "datetime.now",
            }
        ],
        "rationale": "Needs the domain rule in context. Diff looks like a normal scheduler feature.",
    },
    """diff --git a/src/payroll/periods.py b/src/payroll/periods.py
--- a/src/payroll/periods.py
+++ b/src/payroll/periods.py
@@ -1,6 +1,12 @@
+from datetime import datetime
+
 def close_if_due(period, employee):
-    return False
+    # close at local midnight
+    now = datetime.now()
+    if now.hour == 0 and now.date() > period.end:
+        period.closed = True
+        period.closed_at = now
+        return True
+    return False
""",
    {
        "docs/payroll_invariants.md": (
            "Pay-period close MUST use the employee's work-jurisdiction timezone "
            "(America/Toronto, America/Montreal, America/Halifax). "
            "Never datetime.now() on the app host. Filing day is a legal fact.\n"
        )
    },
)

# --- F005 -----------------------------------------------------------------
write_task(
    "F005_check_then_act",
    {
        "id": "F005_check_then_act",
        "family": "F",
        "title": "Wallet debit is check-then-act without a lock",
        "language": "python",
        "tags": ["concurrency", "money", "findings"],
        "difficulty": 2,
        "source": "synthetic",
        "license_note": LICENSE,
        "pr_title": "feat: allow partial wallet debit for invoices",
        "pr_body": "Debits wallet if balance covers the invoice. Simple read then write.",
        "author": "billing-eng",
        "files_changed": 1,
        "additions": 12,
        "deletions": 1,
    },
    {
        "triage_label": None,
        "triage_priority": None,
        "findings": [
            {
                "id": "F-race-debit",
                "path": "src/billing/wallet.py",
                "title": "Non-atomic balance check then debit can double-spend",
                "severity": "critical",
                "rationale": "Two concurrent requests can both observe balance >= amount and both write balance - amount. Money-handling requires UPDATE ... WHERE balance >= amount, a row lock, or a ledger append. This is a substantive correctness bug.",
                "anchor": "balance",
            }
        ],
        "rationale": "No tenant token, no dropped filter. Heuristics that only look at authz/parity miss it.",
    },
    """diff --git a/src/billing/wallet.py b/src/billing/wallet.py
--- a/src/billing/wallet.py
+++ b/src/billing/wallet.py
@@ -10,4 +10,14 @@ class Wallet:
     def debit(self, invoice_id, amount):
-        raise NotImplementedError
+        row = self.db.fetch_one("SELECT balance FROM wallets WHERE id = %s", (self.id,))
+        if row["balance"] >= amount:
+            new_bal = row["balance"] - amount
+            self.db.execute(
+                "UPDATE wallets SET balance = %s WHERE id = %s",
+                (new_bal, self.id),
+            )
+            self.db.execute(
+                "INSERT INTO wallet_tx (wallet_id, invoice_id, amount) VALUES (%s,%s,%s)",
+                (self.id, invoice_id, amount),
+            )
+            return True
+        return False
""",
)

# --- F006 -----------------------------------------------------------------
write_task(
    "F006_auth_header_log",
    {
        "id": "F006_auth_header_log",
        "family": "F",
        "title": "Debug log writes Authorization header",
        "language": "typescript",
        "tags": ["pii", "secrets", "findings"],
        "difficulty": 1,
        "source": "synthetic",
        "license_note": LICENSE,
        "pr_title": "chore: add request debug logging for partner API",
        "pr_body": "Temporary logs so we can see what the partner sends.",
        "author": "platform-eng",
        "files_changed": 1,
        "additions": 6,
        "deletions": 0,
    },
    {
        "triage_label": None,
        "triage_priority": None,
        "findings": [
            {
                "id": "F-authz-header-log",
                "path": "src/partner/proxy.ts",
                "title": "Logs full incoming headers including Authorization",
                "severity": "high",
                "rationale": "Bearer tokens in application logs are credential leakage. Temporary debug that ships is still a defect. Redact Authorization, Cookie, and Set-Cookie.",
                "anchor": "authorization",
            }
        ],
        "rationale": "One-line observability change. Easy for a size heuristic to ignore; easy for a secret-logging rule to catch.",
    },
    """diff --git a/src/partner/proxy.ts b/src/partner/proxy.ts
--- a/src/partner/proxy.ts
+++ b/src/partner/proxy.ts
@@ -14,6 +14,9 @@ export async function forward(req: Request) {
+  console.log('partner inbound', {
+    url: req.url,
+    headers: req.headers, // includes authorization
+  })
   return fetch(UPSTREAM, { headers: req.headers, method: req.method, body: req.body })
 }
""",
)

# --- F007 -----------------------------------------------------------------
write_task(
    "F007_default_page_size",
    {
        "id": "F007_default_page_size",
        "family": "F",
        "title": "Default page size 20 → 1000 breaks implicit contract",
        "language": "typescript",
        "tags": ["api-contract", "findings", "context"],
        "difficulty": 2,
        "source": "synthetic",
        "license_note": LICENSE,
        "pr_title": "perf: raise default page size for list endpoints",
        "pr_body": "Clients were making too many round-trips. Default limit 1000. Still overridable.",
        "author": "api-team",
        "files_changed": 1,
        "additions": 2,
        "deletions": 2,
    },
    {
        "triage_label": None,
        "triage_priority": None,
        "findings": [
            {
                "id": "F-page-size-contract",
                "path": "src/http/pagination.ts",
                "title": "Default page size change is an implicit API contract break",
                "severity": "medium",
                "rationale": "Mobile clients and the billing exporter assume ≤20 rows and materialise the full page in memory. Jumping the default to 1000 is a behavior change for every caller that omitted limit=. Needs a new query param version or a documented major.",
                "anchor": "DEFAULT_LIMIT",
            }
        ],
        "rationale": "Looks like a performance win. Gold requires knowing callers depend on the old default. Neither a size heuristic nor a simple secret/CSRF checklist should be expected to catch this — it is the residual miss.",
    },
    """diff --git a/src/http/pagination.ts b/src/http/pagination.ts
--- a/src/http/pagination.ts
+++ b/src/http/pagination.ts
@@ -1,4 +1,4 @@
-export const DEFAULT_LIMIT = 20
+export const DEFAULT_LIMIT = 1000
 export function paginate(q: Query) {
   const limit = q.limit ?? DEFAULT_LIMIT
   return { limit, offset: q.offset ?? 0 }
""",
    {
        "docs/api.md": (
            "List endpoints default to 20 rows. Mobile and the billing exporter "
            "do not send limit= and allocate a fixed buffer.\n"
        )
    },
)

# --- F008 -----------------------------------------------------------------
write_task(
    "F008_inventory_salvage",
    {
        "id": "F008_inventory_salvage",
        "family": "F",
        "title": "Salvage stock valued at replacement cost",
        "language": "python",
        "tags": ["domain", "inventory", "accounting", "findings"],
        "difficulty": 3,
        "source": "synthetic",
        "license_note": LICENSE,
        "pr_title": "fix: use replacement cost for damaged-lot valuation",
        "pr_body": "Insurance asked for replacement cost on damaged lots. Wire that into the valuation helper so finance and ops match.",
        "author": "finance-eng",
        "files_changed": 1,
        "additions": 8,
        "deletions": 4,
    },
    {
        "triage_label": None,
        "triage_priority": None,
        "findings": [
            {
                "id": "F-salvage-nrv",
                "path": "src/inventory/valuation.py",
                "title": "Salvage lots must be valued at NRV, not replacement cost",
                "severity": "high",
                "rationale": "Damaged/salvage inventory is written down to net realisable value (expected sell price minus completion/disposal). Replacement cost overstates the asset and can overstate a claim. The PR message cites insurance; the ledger still has to follow the valuation policy in context. Domain-only defect.",
                "anchor": "replacement_cost",
            }
        ],
        "rationale": "Only someone who knows salvage vs replacement vs NRV will flag this. Size, CSRF, tenant, and secret-logging rules all miss. Held out so the suite has a finding neither cheap SUT is supposed to catch.",
    },
    """diff --git a/src/inventory/valuation.py b/src/inventory/valuation.py
--- a/src/inventory/valuation.py
+++ b/src/inventory/valuation.py
@@ -12,8 +12,9 @@ def lot_value(lot):
-    if lot.condition == "salvage":
-        return lot.expected_sale_price - lot.dispose_cost
-    return lot.unit_cost * lot.qty
+    if lot.condition == "salvage":
+        # insurance / finance alignment
+        return lot.replacement_cost * lot.qty
+    return lot.unit_cost * lot.qty
""",
    {
        "docs/inventory_policy.md": (
            "Valuation policy (locked):\n"
            "- sellable: unit cost (FIFO)\n"
            "- salvage / damaged: net realisable value = expected_sale_price - dispose_cost\n"
            "- replacement_cost is for insurance exhibits only, never the inventory subledger\n"
        )
    },
)

print("wrote", sorted(p.name for p in ROOT.iterdir() if p.is_dir()))
