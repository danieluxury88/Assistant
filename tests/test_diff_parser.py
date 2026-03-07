from commit_sage.diff_parser import parse_diff, compact_diff, count_diff_stats

SAMPLE_DIFF = """\
diff --git a/src/main.py b/src/main.py
index abc1234..def5678 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,5 @@
 import os
+import sys
+
 def main():
-    print("hello")
+    print("hello world")
     pass
"""


def test_parse_diff_returns_file():
    diffs = parse_diff(SAMPLE_DIFF)
    assert len(diffs) == 1
    assert diffs[0].path == "src/main.py"


def test_parse_diff_counts_lines():
    diffs = parse_diff(SAMPLE_DIFF)
    assert diffs[0].added == 3
    assert diffs[0].removed == 1


def test_count_diff_stats():
    added, removed = count_diff_stats(SAMPLE_DIFF)
    assert added == 3
    assert removed == 1


def test_compact_diff_empty():
    assert compact_diff("") == ""


def test_compact_diff_within_limit():
    result = compact_diff(SAMPLE_DIFF, max_lines=500)
    assert "src/main.py" in result


def test_compact_diff_truncation():
    # Create a diff with many lines
    big_diff = SAMPLE_DIFF * 20
    result = compact_diff(big_diff, max_lines=10)
    assert "trimmed" in result or len(result.splitlines()) <= 15


def test_parse_diff_empty():
    diffs = parse_diff("")
    assert diffs == []
