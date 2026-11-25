"""Issue #11: malformed Unicode must never damage either derived index."""
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import library


class UnicodeIndexIntegrity(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.host = Path(temp.name) / "catalog"
        shutil.copytree(ROOT, self.host, ignore=shutil.ignore_patterns("__pycache__"))
        self.records = {}
        for section, name, ident in (("ideas", "idea", "IDEA-000001"),
                                     ("features", "feature", "FEAT-000001")):
            row = json.loads((ROOT / "templates" / (name + ".example.json")).read_text(encoding="utf-8"))
            row["id"] = ident
            if section == "features":
                row["idea_ids"] = ["IDEA-000001"]
            self.records[section] = row
            self.write_record(section, row)
        self.assertEqual(library.run(self.host, "build"), 0)
        self.before = self.index_bytes()

    def write_record(self, section, row):
        path = self.host / section / "records" / (row["id"] + ".json")
        path.write_text(json.dumps(row, ensure_ascii=True), encoding="utf-8")
        return path

    def index_bytes(self):
        return [(self.host / section / "INDEX.md").read_bytes()
                for section in ("ideas", "features")]

    def assert_rejected_unchanged(self, section, row):
        path = self.write_record(section, row)
        record_before = path.read_bytes()
        for action in ("check", "build"):
            with self.subTest(action=action):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    result = library.run(self.host, action)
                self.assertEqual(result, 1)
                self.assertIn("invalid Unicode", output.getvalue())
                self.assertIn(path.name, output.getvalue())
                output.getvalue().encode("utf-8", errors="strict")
                self.assertEqual(self.index_bytes(), self.before)
                self.assertEqual(path.read_bytes(), record_before)

    def test_unpaired_title_surrogates_preserve_both_indexes(self):
        for section in ("ideas", "features"):
            for code in (0xD800, 0xDFFF):
                with self.subTest(section=section, code=code):
                    row = dict(self.records[section], title="ok" + chr(code))
                    self.assert_rejected_unchanged(section, row)
                    self.write_record(section, self.records[section])

    def test_nested_values_and_keys_are_rejected_safely(self):
        section = "ideas"
        for row in (dict(self.records[section], origin=dict(self.records[section]["origin"], source="x" + chr(0xD800))),
                    dict(self.records[section], **{"bad" + chr(0xDFFF): "value"})):
            self.assert_rejected_unchanged(section, row)
        self.write_record(section, self.records[section])

    def test_valid_unicode_and_supplementary_pairs_round_trip(self):
        title = "Caf\u00e9 \u6c34 \U0001f680"
        for section in ("ideas", "features"):
            self.write_record(section, dict(self.records[section], title=title))
        self.assertEqual(library.run(self.host, "build"), 0)
        for data in self.index_bytes():
            self.assertIn(title.encode("utf-8"), data)
            self.assertNotIn(b"\r\n", data)
        expected = self.index_bytes()
        self.assertEqual(library.run(self.host, "check"), 0)
        self.assertEqual(library.run(self.host, "build"), 0)
        self.assertEqual(self.index_bytes(), expected)

    def test_both_views_encoded_before_any_index_is_opened(self):
        original = library.index
        def invalid_second(kind, rows):
            return original(kind, rows) if kind == "ideas" else "bad" + chr(0xD800)
        output = io.StringIO()
        with patch.object(library, "index", side_effect=invalid_second):
            with contextlib.redirect_stdout(output):
                self.assertEqual(library.run(self.host, "build"), 1)
        self.assertIn("invalid Unicode", output.getvalue())
        self.assertIn("features/INDEX.md", output.getvalue())
        self.assertEqual(self.index_bytes(), self.before)

    def test_combined_exact_decimal_and_unicode_record_loader(self):
        path = self.host / "ideas/records/IDEA-000001.json"
        spec = {"type": "object", "properties": {
            "id": {"type": "string"}, "title": {"type": "string"},
            "values": {"type": "array", "uniqueItems": True}}}
        for title, valid in (('"ok\\ud800"', False),
                             ('"Caf\\u00e9 \\ud83d\\ude80"', True)):
            with self.subTest(valid=valid):
                path.write_text('{"id":"IDEA-000001","title":' + title
                                + ',"values":[1.0000000000000001,1.0]}',
                                encoding="utf-8")
                issues, rows = library.read_records(self.host, "ideas", spec)
                if valid:
                    self.assertEqual(issues, [])
                    values = rows["IDEA-000001"]["values"]
                    self.assertNotEqual(library.json_identity(values[0]),
                                        library.json_identity(values[1]))
                else:
                    self.assertIn("invalid Unicode", " ".join(issues))
                    self.assertEqual(rows, {})
                self.assertEqual(self.index_bytes(), self.before)


    def prepare_changed_indexes(self):
        for section in ("ideas", "features"):
            self.write_record(section, dict(self.records[section],
                                           title="Updated " + section))

    def test_directory_at_either_index_preserves_other(self):
        self.prepare_changed_indexes()
        for section, other in (("ideas", "features"), ("features", "ideas")):
            with self.subTest(section=section):
                path = self.host / section / "INDEX.md"
                original = path.read_bytes()
                other_path = self.host / other / "INDEX.md"
                other_before = other_path.read_bytes()
                path.unlink()
                path.mkdir()
                sentinel = path / "keep.txt"
                sentinel.write_bytes(b"KEEP")
                try:
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        self.assertEqual(library.run(self.host, "build"), 1)
                    self.assertIn(str(path), output.getvalue())
                    self.assertEqual(other_path.read_bytes(), other_before)
                    self.assertEqual(sentinel.read_bytes(), b"KEEP")
                finally:
                    sentinel.unlink()
                    path.rmdir()
                    path.write_bytes(original)
                    other_path.write_bytes(other_before)

    def test_second_index_replace_failure_rolls_back_first(self):
        self.prepare_changed_indexes()
        target = self.host / "features/INDEX.md"
        original = Path.replace
        def fail_second(source, destination):
            if Path(destination) == target:
                raise PermissionError("injected second replacement failure")
            return original(source, destination)
        output = io.StringIO()
        with patch.object(Path, "replace", fail_second):
            with contextlib.redirect_stdout(output):
                self.assertEqual(library.run(self.host, "build"), 1)
        self.assertIn(str(target), output.getvalue())
        self.assertEqual(self.index_bytes(), self.before)
        for section in ("ideas", "features"):
            self.assertEqual({p.name for p in (self.host / section).iterdir()},
                             {p.name for p in (ROOT / section).iterdir()})
        self.assertEqual(library.run(self.host, "build"), 0)
        self.assertNotEqual(self.index_bytes(), self.before)
        self.assertEqual(library.run(self.host, "check"), 0)
        expected = self.index_bytes()
        self.assertEqual(library.run(self.host, "build"), 0)
        self.assertEqual(self.index_bytes(), expected)

    def test_missing_first_index_is_not_created_on_second_failure(self):
        self.prepare_changed_indexes()
        first = self.host / "ideas/INDEX.md"
        second = self.host / "features/INDEX.md"
        first.unlink()
        original = Path.replace
        def fail_second(source, destination):
            if Path(destination) == second:
                raise PermissionError("injected second replacement failure")
            return original(source, destination)
        with patch.object(Path, "replace", fail_second):
            self.assertEqual(library.run(self.host, "build"), 1)
        self.assertFalse(first.exists())
        self.assertEqual(second.read_bytes(), self.before[1])
        self.assertEqual(library.run(self.host, "build"), 0)
        self.assertEqual(library.run(self.host, "check"), 0)

if __name__ == "__main__":
    unittest.main()
