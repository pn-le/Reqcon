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
    data = build_report_data(RUN_AT, results)
    assert data["run_at"] == RUN_AT
    assert data["summary"] == {"added": 1, "removed": 1, "changed": 1, "boards_ok": 1, "boards_error": 1}
    assert data["boards"][0]["added"][0]["posting_id"] == "1"
    assert data["boards"][0]["total_postings"] == 10
    assert data["boards"][1] == {"board_id": "e", "status": "error", "error": "timeout"}


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


class TestReadmeOpenings:
    BOARDS = [{"id": "b", "name": "Board"}, {"id": "empty", "name": "Empty Board"}]
    STATE = {
        "b": {"fetched_at": "t", "postings": [
            posting("1", "Staff Engineer").to_dict(),
            posting("2", "Software Intern", tags=["student-role"]).to_dict(),
        ]},
        "empty": {"fetched_at": "t", "postings": [posting("3", "Principal Scientist").to_dict()]},
    }

    def section(self):
        from reqcon.report import build_openings_section
        return build_openings_section(self.BOARDS, self.STATE, "2026-07-17 07:00 EDT")

    def test_section_lists_tagged_only(self):
        section = self.section()
        assert "### Board — 1 of 2 postings" in section
        assert "[Software Intern](https://x/2)" in section
        assert "Staff Engineer" not in section
        assert "_no intern/co-op postings right now_" in section

    def test_appends_then_replaces_in_place(self, tmp_path):
        from reqcon.report import update_readme_openings
        readme = tmp_path / "README.md"
        readme.write_text("# Reqcon\n\nIntro.\n")
        assert update_readme_openings(readme, self.section()) is True
        assert readme.read_text().startswith("# Reqcon\n\nIntro.")
        assert "Software Intern" in readme.read_text()

        # second update replaces the section instead of appending again
        assert update_readme_openings(readme, self.section()) is False  # unchanged content
        new = self.section().replace("Software Intern", "ML Intern")
        assert update_readme_openings(readme, new) is True
        text = readme.read_text()
        assert "ML Intern" in text and "Software Intern" not in text
        assert text.count("## Current openings") == 1

    def test_missing_readme_is_noop(self, tmp_path):
        from reqcon.report import update_readme_openings
        assert update_readme_openings(tmp_path / "README.md", self.section()) is False


def test_markdown_prune_keeps_fourteen(tmp_path):
    for day in range(1, 20):
        write_markdown_report(tmp_path, f"2026-06-{day:02d}", "x\n")
    kept = sorted(p.name for p in tmp_path.glob("reqcon-*.md"))
    assert len(kept) == 14
    assert kept[0] == "reqcon-2026-06-06.md"
