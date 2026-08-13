"""Live review does not need a task pack or gold."""

from __future__ import annotations

from sift.cli import main
from sift.tasks import parse_diff_stats, task_from_diff


DIFF = """\
diff --git a/src/a.py b/src/a.py
--- a/src/a.py
+++ b/src/a.py
@@ -1,2 +1,3 @@
 def f():
-    return 1
+    return 2
"""


def test_parse_diff_stats():
    files, adds, dels = parse_diff_stats(DIFF)
    assert files >= 1
    assert adds == 1
    assert dels == 1


def test_task_from_diff_has_no_gold():
    task = task_from_diff(DIFF, title="fix: return 2")
    assert task.gold.triage_label is None
    assert task.gold.findings == []
    assert task.additions == 1


def test_review_cli(tmp_path, capsys):
    patch = tmp_path / "x.patch"
    patch.write_text(DIFF)
    rc = main(["review", "--diff", str(patch), "--title", "fix: return 2"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Triage:" in out


def test_list_without_pack_fails():
    assert main(["list"]) == 2
