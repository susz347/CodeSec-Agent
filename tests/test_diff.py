import unittest

from agent.diff import classify_finding, parse_unified_diff

_SINGLE_HUNK = """\
diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,3 +1,4 @@
 def main():
     x = 1
+    y = eval(user_input)
     return x
"""

_MULTI_FILE = """\
diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,1 +1,1 @@
-old
+new
diff --git a/util.py b/util.py
--- a/util.py
+++ b/util.py
@@ -5,0 +6,3 @@
+    a = 1
+    b = 2
+    c = 3
"""

_NEW_FILE = """\
diff --git a/new.py b/new.py
new file mode 100644
--- /dev/null
+++ b/new.py
@@ -0,0 +1,2 @@
+first
+second
"""


class ParseUnifiedDiffTests(unittest.TestCase):
    def test_single_hunk(self) -> None:
        self.assertEqual(parse_unified_diff(_SINGLE_HUNK), {"app.py": ((3, 3),)})

    def test_multiple_files(self) -> None:
        parsed = parse_unified_diff(_MULTI_FILE)
        self.assertEqual(parsed["app.py"], ((1, 1),))
        self.assertEqual(parsed["util.py"], ((6, 8),))

    def test_new_file(self) -> None:
        self.assertEqual(parse_unified_diff(_NEW_FILE), {"new.py": ((1, 2),)})

    def test_ignores_deleted_file(self) -> None:
        diff = "diff --git a/gone.py b/gone.py\n--- a/gone.py\n+++ /dev/null\n@@ -1,1 +0,0 @@\n-x\n"
        self.assertEqual(parse_unified_diff(diff), {})


class ClassifyFindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ranges = {"app.py": ((3, 5),)}

    def test_changed_when_overlapping(self) -> None:
        self.assertEqual(classify_finding("app.py", 3, 3, self.ranges), "changed")
        self.assertEqual(classify_finding("app.py", 4, 6, self.ranges), "changed")

    def test_unchanged_when_same_file_no_overlap(self) -> None:
        self.assertEqual(classify_finding("app.py", 1, 2, self.ranges), "unchanged")
        self.assertEqual(classify_finding("app.py", 6, 6, self.ranges), "unchanged")

    def test_unknown_when_path_absent(self) -> None:
        self.assertEqual(classify_finding("other.py", 3, 3, self.ranges), "unknown")

    def test_boundary_is_changed(self) -> None:
        self.assertEqual(classify_finding("app.py", 5, 5, self.ranges), "changed")


if __name__ == "__main__":
    unittest.main()
