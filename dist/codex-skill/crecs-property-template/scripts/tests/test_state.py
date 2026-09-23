"""Contract for the workspace: state outside the chat, atomic writes, base-revision
check, history and undo.

The importable JSON must never carry internal bookkeeping, and the working file must
never be the export file.
"""

import json
import os
import tempfile
import unittest

from crecs.state import Workspace, StateError


BASE = {
    "content": [
        {"id": "1111111", "elType": "section", "isInner": False, "settings": {},
         "elements": [
             {"id": "2222222", "elType": "column", "isInner": False,
              "settings": {"_column_size": 100}, "elements": [
                  {"id": "3333333", "elType": "widget",
                   "widgetType": "crecs_property_data", "isInner": False,
                   "settings": {"slug": ""}, "elements": []}
              ]}
         ]}
    ],
    "page_settings": [],
    "version": "0.4",
    "title": "Fixture",
    "type": "page",
}


class WorkspaceCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.base_path = os.path.join(self.root, "base.json")
        with open(self.base_path, "w", encoding="utf-8") as fh:
            json.dump(BASE, fh)
        self.wd = os.path.join(self.root, "work")

    def tearDown(self):
        self.tmp.cleanup()

    def init(self):
        return Workspace.init(self.wd, self.base_path)


class TestInit(WorkspaceCase):
    def test_creates_the_expected_layout(self):
        ws = self.init()
        self.assertTrue(os.path.isfile(os.path.join(self.wd, "document.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.wd, "state.json")))
        self.assertTrue(os.path.isdir(os.path.join(self.wd, "history")))
        self.assertEqual(ws.state["revision"], 0)

    def test_records_the_base_hash_and_the_catalog_hash(self):
        ws = self.init()
        self.assertRegex(ws.state["document_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(ws.state["base_sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("catalog", ws.state)

    def test_refuses_to_clobber_an_existing_workspace(self):
        self.init()
        with self.assertRaises(StateError):
            Workspace.init(self.wd, self.base_path)

    def test_reinit_with_force_is_allowed(self):
        self.init()
        ws = Workspace.init(self.wd, self.base_path, force=True)
        self.assertEqual(ws.state["revision"], 0)

    def test_the_working_document_carries_no_internal_fields(self):
        self.init()
        with open(os.path.join(self.wd, "document.json"), encoding="utf-8") as fh:
            payload = json.load(fh)
        for forbidden in ("_crecs", "_crecs_state", "revision", "decisions"):
            self.assertNotIn(forbidden, payload)


class TestCommit(WorkspaceCase):
    def test_commit_bumps_the_revision_and_writes_history(self):
        ws = self.init()
        doc = ws.load_document()
        doc.set_setting("3333333", "slug", "abc")
        ws.commit(doc, "set slug=abc")
        self.assertEqual(ws.state["revision"], 1)
        self.assertEqual(len(os.listdir(os.path.join(self.wd, "history"))), 1)

    def test_history_entry_records_the_operation_summary(self):
        ws = self.init()
        doc = ws.load_document()
        doc.set_setting("3333333", "slug", "abc")
        ws.commit(doc, "set slug=abc")
        self.assertEqual(ws.state["history"][-1]["summary"], "set slug=abc")
        self.assertEqual(ws.state["history"][-1]["revision"], 1)

    def test_decisions_log_is_human_readable_and_outside_the_document(self):
        ws = self.init()
        doc = ws.load_document()
        doc.set_setting("3333333", "slug", "abc")
        ws.commit(doc, "set slug=abc", decision="Preview slug supplied by the target profile.")
        text = open(os.path.join(self.wd, "decisions.md"), encoding="utf-8").read()
        self.assertIn("target profile", text)

    def test_external_change_is_detected(self):
        ws = self.init()
        path = os.path.join(self.wd, "document.json")
        payload = json.load(open(path, encoding="utf-8"))
        payload["title"] = "Edited by someone else"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        doc = ws.load_document(accept_external=True)
        doc.set_setting("3333333", "slug", "x")
        ws2 = Workspace.open(self.wd)
        with self.assertRaises(StateError) as cm:
            ws2.commit(doc, "set slug=x")
        self.assertIn("external", str(cm.exception).lower())

    def test_external_change_can_be_accepted_explicitly(self):
        ws = self.init()
        path = os.path.join(self.wd, "document.json")
        payload = json.load(open(path, encoding="utf-8"))
        payload["title"] = "Edited elsewhere"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        ws = Workspace.open(self.wd)
        doc = ws.load_document(accept_external=True)
        ws.commit(doc, "accepted external", accept_external=True)
        self.assertEqual(ws.load_document().envelope["title"], "Edited elsewhere")

    def test_write_is_atomic_no_temp_left_behind(self):
        ws = self.init()
        doc = ws.load_document()
        doc.set_setting("3333333", "slug", "abc")
        ws.commit(doc, "set slug")
        leftovers = [n for n in os.listdir(self.wd) if n.endswith(".tmp")]
        self.assertEqual(leftovers, [])


class TestUndo(WorkspaceCase):
    def test_undo_restores_the_previous_content(self):
        ws = self.init()
        doc = ws.load_document()
        doc.set_setting("3333333", "slug", "first")
        ws.commit(doc, "set first")
        doc = ws.load_document()
        doc.set_setting("3333333", "slug", "second")
        ws.commit(doc, "set second")
        ws.undo()
        self.assertEqual(ws.load_document().by_id("3333333").settings["slug"], "first")
        self.assertEqual(ws.state["revision"], 3)

    def test_undo_multiple_steps(self):
        ws = self.init()
        for value in ("a", "b", "c"):
            doc = ws.load_document()
            doc.set_setting("3333333", "slug", value)
            ws.commit(doc, "set " + value)
        ws.undo(steps=2)
        self.assertEqual(ws.load_document().by_id("3333333").settings["slug"], "a")

    def test_undo_at_the_beginning_is_an_error(self):
        ws = self.init()
        with self.assertRaises(StateError):
            ws.undo()

    def test_undo_is_itself_recorded_so_it_can_be_undone(self):
        ws = self.init()
        doc = ws.load_document()
        doc.set_setting("3333333", "slug", "first")
        ws.commit(doc, "set first")
        ws.undo()
        self.assertEqual(ws.state["history"][-1]["op"], "undo")


class TestResume(WorkspaceCase):
    def test_a_fresh_process_sees_the_same_state(self):
        ws = self.init()
        doc = ws.load_document()
        doc.set_setting("3333333", "slug", "resumed")
        ws.commit(doc, "set resumed", decision="Chosen with the client.")
        reopened = Workspace.open(self.wd)
        self.assertEqual(reopened.state["revision"], 1)
        self.assertEqual(
            reopened.load_document().by_id("3333333").settings["slug"], "resumed"
        )
        self.assertIn("Chosen with the client.", reopened.decisions_text())

    def test_open_on_a_missing_workspace_is_actionable(self):
        with self.assertRaises(StateError) as cm:
            Workspace.open(os.path.join(self.root, "nope"))
        self.assertIn("init", str(cm.exception))

    def test_summary_is_enough_to_resume_elsewhere(self):
        ws = self.init()
        summary = ws.resume_summary()
        for key in ("workdir", "revision", "document_sha256", "base_template", "catalog"):
            self.assertIn(key, summary)


class TestBaseline(WorkspaceCase):
    def test_pre_existing_unknown_keys_are_recorded_at_import(self):
        payload = json.load(open(self.base_path, encoding="utf-8"))
        payload["content"][0]["settings"]["section_background_image"] = {"id": "5850"}
        with open(self.base_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        ws = Workspace.init(self.wd, self.base_path, force=True)
        self.assertIn("1111111::section_background_image", ws.state["baseline_keys"])

    def test_a_key_added_later_is_not_in_the_baseline(self):
        ws = self.init()
        doc = ws.load_document()
        doc.set_setting("3333333", "invented_key", "x")
        ws.commit(doc, "set invented")
        self.assertNotIn("3333333::invented_key", ws.state["baseline_keys"])


if __name__ == "__main__":
    unittest.main()
