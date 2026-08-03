from reqcon.diff import Diff
from reqcon.models import BoardResult, ChangedPosting, Posting
from reqcon.report import build_markdown, build_report_data, write_markdown_report

RUN_AT = "2026-07-17T07:00:00-04:00"


def posting(pid, title="Engineer", tags=None):
    return Posting(board_id="b", posting_id=pid, title=title, url=f"https://x/{pid}",
                   location="Boston, MA", tags=tags or [])


def ok_result(**diff_kw):
    return BoardResult(board_id="b", name="Board", status="ok", diff=Diff(**diff_kw), total_postings=10)


def test_json_report_structure_and_summary():
    results = [
        ok_result(added=[posting("1")], removed=[posting("2")],
                  changed=[ChangedPosting(posting("3", "Old"), posting("3", "New"))]),
        BoardResult(board_id="e", name="Err", status="error", error="timeout"),
    ]
    results.append(BoardResult(board_id="s", name="Skipped", status="skipped-ci"))
    data = build_report_data(RUN_AT, results)
    assert data["run_at"] == RUN_AT
    assert data["summary"] == {
        "added": 1, "removed": 1, "changed": 1,
        "boards_ok": 1, "boards_error": 1, "boards_skipped": 1,
    }
    assert data["boards"][0]["added"][0]["posting_id"] == "1"
    assert data["boards"][0]["total_postings"] == 10
    assert data["boards"][1] == {"board_id": "e", "status": "error", "error": "timeout"}
    assert data["boards"][2] == {"board_id": "s", "status": "skipped-ci"}


def test_markdown_no_changes_single_line():
    md = build_markdown(RUN_AT, [ok_result(), ok_result()])
    assert "No changes across 2 boards." in md


def test_markdown_tagged_bold_and_first():
    plain = posting("1", "Senior Engineer")
    tagged = posting("2", "Software Intern", tags=["student-role"])
    md = build_markdown(RUN_AT, [ok_result(added=[plain, tagged])])
    assert "**[Software Intern](https://x/2)**" in md
    assert md.index("Software Intern") < md.index("Senior Engineer")


def test_markdown_errors_flagged_at_top():
    md = build_markdown(RUN_AT, [
        BoardResult(board_id="e", name="Err", status="error", error="timeout"),
        ok_result(),
    ])
    assert md.splitlines()[2].startswith("> ⚠️ Errored boards: Err (timeout)")


class TestJsonWriteSkip:
    def test_rewrite_skipped_when_only_run_at_differs(self, tmp_path):
        from reqcon.report import write_json_report
        data1 = build_report_data(RUN_AT, [ok_result()])
        _, wrote = write_json_report(tmp_path, data1)
        assert wrote is True
        data2 = build_report_data("2026-07-18T07:00:00-04:00", [ok_result()])
        _, wrote = write_json_report(tmp_path, data2)
        assert wrote is False
        data3 = build_report_data(RUN_AT, [ok_result(added=[posting("9")])])
        _, wrote = write_json_report(tmp_path, data3)
        assert wrote is True


def test_markdown_prune_keeps_fourteen(tmp_path):
    for day in range(1, 20):
        write_markdown_report(tmp_path, f"2026-06-{day:02d}", "x\n")
    kept = sorted(p.name for p in tmp_path.glob("reqcon-*.md"))
    assert len(kept) == 14
    assert kept[0] == "reqcon-2026-06-06.md"
