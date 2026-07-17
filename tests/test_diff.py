from reqcon.diff import diff_postings, evaluate_board
from reqcon.models import Posting

NOW = "2026-07-17T07:00:00-04:00"


def posting(pid, title="T", url=None, location=None):
    return Posting(board_id="b", posting_id=pid, title=title, url=url or f"https://x/{pid}", location=location)


def snapshot(postings, **extra):
    snap = {"fetched_at": "2026-07-16T07:00:00-04:00", "postings": [p.to_dict() for p in postings]}
    snap.update(extra)
    return snap


class TestDiffPostings:
    def test_added_removed_changed(self):
        prev = [posting("1"), posting("2", title="Old"), posting("3")]
        curr = [posting("2", title="New"), posting("3"), posting("4")]
        diff = diff_postings(prev, curr)
        assert [p.posting_id for p in diff.added] == ["4"]
        assert [p.posting_id for p in diff.removed] == ["1"]
        assert [(c.previous.title, c.current.title) for c in diff.changed] == [("Old", "New")]

    def test_identical_runs_no_changes(self):
        prev = [posting("1"), posting("2")]
        diff = diff_postings(prev, list(prev))
        assert not diff.has_changes

    def test_location_change_detected(self):
        diff = diff_postings([posting("1", location="Boston")], [posting("1", location="NYC")])
        assert len(diff.changed) == 1


class TestEvaluateBoard:
    def test_first_run_is_baseline_not_added(self):
        out = evaluate_board(None, [posting("1"), posting("2")], None, NOW)
        assert out.status == "baseline"
        assert len(out.diff.baseline) == 2
        assert out.diff.added == []
        assert len(out.new_snapshot["postings"]) == 2

    def test_error_carries_snapshot_forward(self):
        out = evaluate_board(snapshot([posting("1")]), None, "timeout", NOW)
        assert out.status == "error"
        assert out.error == "timeout"
        assert out.new_snapshot is None  # caller keeps previous snapshot untouched

    def test_ok_run_updates_snapshot(self):
        out = evaluate_board(snapshot([posting("1")]), [posting("1"), posting("2")], None, NOW)
        assert out.status == "ok"
        assert [p.posting_id for p in out.diff.added] == ["2"]
        assert out.new_snapshot["fetched_at"] == NOW

    def test_zero_drop_first_run_is_error(self):
        out = evaluate_board(snapshot([posting("1"), posting("2")]), [], None, NOW)
        assert out.status == "error"
        assert "suspicious" in out.error
        assert out.new_snapshot["zero_pending"] is True
        # previous postings preserved
        assert len(out.new_snapshot["postings"]) == 2

    def test_zero_drop_second_run_marks_removed(self):
        pending = snapshot([posting("1"), posting("2")], zero_pending=True)
        out = evaluate_board(pending, [], None, NOW)
        assert out.status == "ok"
        assert len(out.diff.removed) == 2
        assert out.new_snapshot["postings"] == []
        assert "zero_pending" not in out.new_snapshot

    def test_zero_drop_recovery_clears_flag(self):
        pending = snapshot([posting("1")], zero_pending=True)
        out = evaluate_board(pending, [posting("1")], None, NOW)
        assert out.status == "ok"
        assert not out.diff.has_changes
        assert "zero_pending" not in out.new_snapshot

    def test_zero_from_empty_snapshot_is_ok(self):
        out = evaluate_board(snapshot([]), [], None, NOW)
        assert out.status == "ok"
        assert not out.diff.has_changes
