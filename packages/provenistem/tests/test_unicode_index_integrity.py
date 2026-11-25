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


    def assert_duplicate_record_rejected(self, section, raw, key):
        row = self.records[section]
        path = self.host / section / "records" / (row["id"] + ".json")
        try:
            for action in ("check", "build"):
                with self.subTest(section=section, action=action, key=key):
                    path.write_text(raw, encoding="utf-8")
                    record_before = path.read_bytes()
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        result = library.run(self.host, action)
                    self.assertEqual(result, 1)
                    self.assertIn("duplicate JSON key", output.getvalue())
                    self.assertIn(str(path), output.getvalue())
                    self.assertIn(key, output.getvalue())
                    output.getvalue().encode("utf-8", errors="strict")
                    self.assertEqual(path.read_bytes(), record_before)
                    self.assertEqual(self.index_bytes(), self.before)
        finally:
            self.write_record(section, row)
            self.assertEqual(library.run(self.host, "build"), 0)

    def test_duplicate_record_keys_in_both_orders(self):
        for section, row in self.records.items():
            raw = json.dumps(row)
            original = '"title": ' + json.dumps(row["title"])
            for members in (
                '"title": "different", ' + original,
                original + ', "title": "different"',
                original + ', ' + original,
                r'"tit\u006ce": "different", ' + original,
            ):
                with self.subTest(section=section, members=members):
                    self.assert_duplicate_record_rejected(
                        section, raw.replace(original, members, 1), "title")

    def test_duplicate_nested_record_keys_in_both_orders(self):
        for section, row in self.records.items():
            raw = json.dumps(row)
            original = '"status": "untested"'
            self.assertIn(original, raw)
            for members in ('"status": "planned", ' + original,
                            original + ', "status": "planned"'):
                with self.subTest(section=section, members=members):
                    self.assert_duplicate_record_rejected(
                        section, raw.replace(original, members, 1), "status")

    def test_duplicate_parser_scope_and_safe_diagnostic(self):
        for raw in ('{"a":1,"a":1}', '{"x":[{"a":1,"a":2}]}',
                    r'{"a":1,"\u0061":2}', r'{"\ud800":1,"\ud800":2}'):
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(ValueError, "duplicate JSON key") as caught:
                    library.parse_json(raw)
                str(caught.exception).encode("utf-8", errors="strict")
        self.assertEqual(library.parse_json('{"a":1,"A":2,"x":[{"a":3},{"a":4}]}'),
                         {"a": 1, "A": 2, "x": [{"a": 3}, {"a": 4}]})
        self.assertEqual(library.run(self.host, "check"), 0)
        self.assertEqual(library.run(self.host, "build"), 0)
        self.assertEqual(self.index_bytes(), self.before)

    def test_duplicate_schema_keys_are_rejected(self):
        path = self.host / "ideas/schema/v1/idea.schema.json"
        raw = path.read_text(encoding="utf-8")
        self.assertIn('"type": "object"', raw)
        path.write_text(raw.replace('"type": "object"',
                                    '"type": "object", "type": "object"', 1),
                        encoding="utf-8")
        issues, ideas, features = library.validate(self.host)
        self.assertIn("duplicate JSON key", " ".join(issues))
        self.assertIn("type", " ".join(issues))
        self.assertEqual((ideas, features), ({}, {}))
        self.assertEqual(self.index_bytes(), self.before)

if __name__ == "__main__":
    unittest.main()
