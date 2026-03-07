from commit_sage.summarizer import build_summary

SAMPLE_DIFF = """\
diff --git a/src/main.py b/src/main.py
index abc1234..def5678 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,2 +1,3 @@
 def hello():
+    print("hello")
     pass
"""


def test_build_summary_basic():
    summary = build_summary(
        branch="main",
        staged_files=["src/main.py"],
        unstaged_files=[],
        staged_diff=SAMPLE_DIFF,
        unstaged_diff="",
        max_diff_lines=300,
    )
    assert summary.branch == "main"
    assert "src/main.py" in summary.staged_files
    assert "python" in summary.file_categories
    assert "main.py" in summary.summary_text


def test_build_summary_no_changes():
    summary = build_summary(
        branch="dev",
        staged_files=[],
        unstaged_files=[],
        staged_diff="",
        unstaged_diff="",
    )
    assert summary.branch == "dev"
    assert summary.staged_files == []
    assert summary.unstaged_files == []


def test_build_summary_infers_scope():
    summary = build_summary(
        branch="feature/auth",
        staged_files=["src/auth/login.py", "src/auth/logout.py"],
        unstaged_files=[],
        staged_diff=SAMPLE_DIFF,
        unstaged_diff="",
    )
    # scope should be inferred
    assert summary.inferred_scope is not None


def test_build_summary_mixed_areas_detected():
    summary = build_summary(
        branch="main",
        staged_files=["src/main.py", "app.css", "README.md"],
        unstaged_files=[],
        staged_diff=SAMPLE_DIFF,
        unstaged_diff="",
    )
    assert len(summary.mixed_areas) > 1
    assert "backend" in summary.mixed_areas
    assert "frontend" in summary.mixed_areas
    assert "docs" in summary.mixed_areas


def test_build_summary_include_files_filters_summary():
    summary = build_summary(
        branch="main",
        staged_files=["src/main.py", "app.css"],
        unstaged_files=[],
        staged_diff=SAMPLE_DIFF,
        unstaged_diff="",
        include_files={"src/main.py"},
    )
    # Full staged_files list is preserved on the model
    assert "src/main.py" in summary.staged_files
    assert "app.css" in summary.staged_files
    # But the AI summary text only includes selected file
    assert "main.py" in summary.summary_text
    # app.css is not in the effective diff (SAMPLE_DIFF only has main.py)
    assert "python" in summary.file_categories
