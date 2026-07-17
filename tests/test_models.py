from reqcon.models import Posting, synthetic_posting_id, tag_postings


def make_posting(title="Engineer", **kw):
    defaults = dict(board_id="b", posting_id="1", title=title, url="https://x/1")
    defaults.update(kw)
    return Posting(**defaults)


class TestSyntheticPostingId:
    def test_stable_across_whitespace_and_case(self):
        a = synthetic_posting_id("  Software   Intern ", "Boston,  MA")
        b = synthetic_posting_id("software intern", "boston, ma")
        assert a == b
        assert len(a) == 16

    def test_differs_on_title_or_location(self):
        base = synthetic_posting_id("Intern", "Boston")
        assert synthetic_posting_id("Intern II", "Boston") != base
        assert synthetic_posting_id("Intern", "NYC") != base

    def test_none_location(self):
        assert synthetic_posting_id("Intern", None) == synthetic_posting_id("Intern", "")


class TestTagging:
    KEYWORDS = ["intern", "internship", "co-op", "coop", "undergraduate", "co op"]

    def test_whole_word_only(self):
        postings = [
            make_posting("Business Operations, International"),
            make_posting("Internal Audit Manager"),
            make_posting("2027 Software Engineer Interns"),
            make_posting("CA0153: Internship - Space Applications"),
        ]
        tag_postings(postings, self.KEYWORDS)
        assert postings[0].tags == []
        assert postings[1].tags == []
        assert postings[2].tags == ["student-role"]
        assert postings[3].tags == ["student-role"]

    def test_case_insensitive_match(self):
        postings = [make_posting("Software INTERN"), make_posting("Fall Co-Op"), make_posting("Chief Engineer")]
        tag_postings(postings, self.KEYWORDS)
        assert postings[0].tags == ["student-role"]
        assert postings[1].tags == ["student-role"]
        assert postings[2].tags == []

    def test_no_double_tag(self):
        postings = [make_posting("Intern")]
        tag_postings(postings, self.KEYWORDS)
        tag_postings(postings, self.KEYWORDS)
        assert postings[0].tags == ["student-role"]

    def test_roundtrip_dict(self):
        p = make_posting("Intern", location="Boston", tags=["student-role"])
        assert Posting.from_dict(p.to_dict()) == p
