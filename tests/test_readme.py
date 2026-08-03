from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from reqcon.models import BoardResult, Diff, Posting
from reqcon.readme import (
    END_MARKER,
    START_MARKER,
    ReadmeError,
    render_section,
    update_readme,
)

NOW = datetime(2026, 8, 3, 7, 0, tzinfo=ZoneInfo("America/New_York"))
BOARDS = [{"id": "b", "name": "Board"}, {"id": "c", "name": "Cboard"}]


def posting(pid, title, first_seen, tags=None, board_id="b"):
    return Posting(
        board_id=board_id, posting_id=pid, title=title, url=f"https://x/{pid}",
        location="Boston, MA", tags=tags or [], first_seen=first_seen,
    ).to_dict()


def state(postings_b, postings_c=()):
    return {
        "b": {"fetched_at": "t", "postings": list(postings_b)},
        "c": {"fetched_at": "t", "postings": list(postings_c)},
    }


def results(status_b="ok", status_c="ok"):
    return [
        BoardResult(board_id="b", name="Board", status=status_b, diff=Diff()),
        BoardResult(board_id="c", name="Cboard", status=status_c, diff=Diff()),
    ]


class TestRenderSection:
    def test_new_this_week_tagged_first_then_newest(self):
        st = state([
            posting("1", "Old Role", "2026-07-01"),
            posting("2", "Fresh Plain Role", "2026-08-02"),
            posting("3", "Fresh Intern", "2026-07-30", tags=["student-role"]),
        ])
        section = render_section(BOARDS, st, results(), NOW, None)
        table = section.split("<details>")[0]
        assert "Old Role" not in table  # outside 7-day window
        # tagged row first despite being older, with grad cap prefix
        assert table.index("🎓 Board | [Fresh Intern]") < table.index("| Board | [Fresh Plain Role]")
        assert "| First seen |" in table

    def test_status_row_emojis(self):
        section = render_section(BOARDS, state([]), results(status_c="error"), NOW, None)
        assert "✅ Board" in section
        assert "⚠️ Cboard" in section

    def test_skipped_ci_emoji(self):
        section = render_section(BOARDS, state([]), results(status_c="skipped-ci"), NOW, None)
        assert "⏭️ Cboard" in section

    def test_cap_and_overflow_link(self):
        many = [posting(str(i), f"Role {i:03d}", "2026-08-01") for i in range(35)]
        section = render_section(BOARDS, state(many), results(), NOW, "reqcon-2026-08-01.md")
        assert section.count("| Board |") == 30
        assert "…and 5 more" in section
        assert "reports/reqcon-2026-08-01.md" in section

    def test_all_postings_details_block(self):
        st = state([posting("1", "Any Role", "2026-07-01")])
        section = render_section(BOARDS, st, results(), NOW, None)
        assert "<details>" in section
        assert "All tracked postings (1)" in section

    def test_deterministic(self):
        st = state([posting("2", "B Role", "2026-08-02"), posting("1", "A Role", "2026-08-02")])
        a = render_section(BOARDS, st, results(), NOW, None)
        b = render_section(BOARDS, st, results(), NOW, None)
        assert a == b


class TestUpdateReadme:
    def wrap(self, body="\n"):
        return f"# Hand-written\n\n{START_MARKER}{body}{END_MARKER}\n\nfooter\n"

    def test_replaces_only_between_markers(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(self.wrap("\nold\n"))
        assert update_readme(readme, "new content") is True
        text = readme.read_text()
        assert text.startswith("# Hand-written")
        assert text.endswith("footer\n")
        assert "new content" in text and "old" not in text

    def test_missing_markers_fails_loudly(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# No markers here\n")
        with pytest.raises(ReadmeError):
            update_readme(readme, "x")

    def test_missing_file_fails_loudly(self, tmp_path):
        with pytest.raises(ReadmeError):
            update_readme(tmp_path / "README.md", "x")

    def test_timestamp_only_change_is_skipped(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(self.wrap())
        section_v1 = "**Last scan:** 2026-08-03 07:00 EDT · 8 boards · 0 new · 0 removed\n\nbody"
        assert update_readme(readme, section_v1) is True
        section_v2 = "**Last scan:** 2026-08-04 07:00 EDT · 8 boards · 0 new · 0 removed\n\nbody"
        assert update_readme(readme, section_v2) is False  # only the volatile line moved
        assert "2026-08-03" in readme.read_text()  # original kept, byte-identical

    def test_real_content_change_is_written(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(self.wrap())
        update_readme(readme, "**Last scan:** t1\n\nbody A")
        assert update_readme(readme, "**Last scan:** t2\n\nbody B") is True
        assert "body B" in readme.read_text()
