import pytest

from reqcon.adapters import html_scrape
from reqcon.adapters.base import AdapterError

from conftest import load_fixture_text

MERL_BOARD = {
    "id": "merl", "adapter": "html",
    "url": "https://www.merl.com/employment/internship-openings",
    "item_selector": "li.publication-source",
    "title_selector": "header.preview-header h2 a",
    "url_selector": "header.preview-header h2 a",
}
UBICEPT_BOARD = {
    "id": "ubicept", "adapter": "html",
    "url": "https://www.ubicept.com/careers",
    "item_selector": "#open-positions .w-dyn-item",
    "title_selector": "h3",
    "url_selector": "a",
    "location_selector": ".top-career-tile > div",
}


def test_missing_selector_fails_clearly():
    with pytest.raises(AdapterError, match="selector not configured"):
        html_scrape.fetch({"id": "x", "url": "https://x", "item_selector": None})


def parse(html: str):
    scrapling = pytest.importorskip("scrapling")
    parser_mod = pytest.importorskip("scrapling.parser")
    cls = getattr(parser_mod, "Selector", None) or getattr(parser_mod, "Adaptor")
    return cls(html)  # first positional arg: `content` in 0.4+, `text` in 0.2


class TestExtraction:
    def test_merl_fixture(self):
        page = parse(load_fixture_text("merl.html"))
        postings = html_scrape.extract_postings(page, MERL_BOARD)
        assert len(postings) == 2
        first = postings[0]
        assert first.title.startswith("CA0153: Internship")
        assert first.url == "https://www.merl.com/employment/internship-openings#CA0153"
        assert first.posting_id == first.url  # absolute URL is the identity

    def test_ubicept_fixture(self):
        page = parse(load_fixture_text("ubicept.html"))
        postings = html_scrape.extract_postings(page, UBICEPT_BOARD)
        assert [p.title for p in postings] == ["Fall Co-op / Internship", "Other Positions"]
        assert postings[0].url == "https://www.ubicept.com/careers/fall-co-op-internship"
        assert postings[0].location == "Boston, MA"

    def test_stable_ids_across_reparses(self):
        html = load_fixture_text("merl.html")
        ids1 = [p.posting_id for p in html_scrape.extract_postings(parse(html), MERL_BOARD)]
        ids2 = [p.posting_id for p in html_scrape.extract_postings(parse(html), MERL_BOARD)]
        assert ids1 == ids2

    def test_empty_match_raises(self):
        page = parse("<html><body><p>redesigned page</p></body></html>")
        with pytest.raises(AdapterError, match="matched nothing"):
            html_scrape.extract_postings(page, MERL_BOARD)
