import json

import httpx
import pytest

from reqcon.adapters import greenhouse, workday
from reqcon.adapters.base import AdapterError, USER_AGENT

from conftest import load_fixture_json

GH_BOARD = {"id": "str", "name": "STR", "adapter": "greenhouse", "board_token": "example"}
WD_BOARD = {
    "id": "draper", "name": "Draper", "adapter": "workday",
    "tenant": "draper", "wd_host": "draper.wd5.myworkdayjobs.com", "site": "Draper_Careers",
}


def mock_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


class TestGreenhouse:
    def test_maps_fields(self):
        fixture = load_fixture_json("greenhouse_jobs.json")

        def handler(request):
            assert request.url.path == "/v1/boards/example/jobs"
            assert request.headers["user-agent"] == USER_AGENT
            return httpx.Response(200, json=fixture)

        postings = greenhouse.fetch(GH_BOARD, client=mock_client(handler))
        assert len(postings) == 3
        first = postings[0]
        assert first.posting_id == "4650304006"
        assert first.title == "Chief Engineer"
        assert first.url.endswith("/jobs/4650304006")
        assert first.location == "Woburn, MA"
        assert first.raw_updated_at == "2026-07-01T12:00:00-04:00"
        assert postings[2].location is None  # null location handled

    def test_http_error_raises_adapter_error(self):
        client = mock_client(lambda req: httpx.Response(404))
        with pytest.raises(AdapterError):
            greenhouse.fetch(GH_BOARD, client=client)

    def test_missing_jobs_key_raises(self):
        client = mock_client(lambda req: httpx.Response(200, json={"unexpected": True}))
        with pytest.raises(AdapterError):
            greenhouse.fetch(GH_BOARD, client=client)


class TestWorkday:
    def test_single_page_stops_at_total(self):
        fixture = load_fixture_json("workday_jobs_page1.json")  # total 3, so one request
        calls = []

        def handler(request):
            calls.append(json.loads(request.content)["offset"])
            assert request.url.path == "/wday/cxs/draper/Draper_Careers/jobs"
            return httpx.Response(200, json=fixture)

        workday.fetch(WD_BOARD, client=mock_client(handler))
        assert calls == [0]

    def test_paginates_and_maps_fields(self):
        page1 = {"total": 21, "jobPostings": load_fixture_json("workday_jobs_page1.json")["jobPostings"]}
        page2 = {"total": 21, "jobPostings": load_fixture_json("workday_jobs_page2.json")["jobPostings"]}

        def handler(request):
            offset = json.loads(request.content)["offset"]
            return httpx.Response(200, json=page1 if offset == 0 else page2)

        postings = workday.fetch(WD_BOARD, client=mock_client(handler))
        ids = [p.posting_id for p in postings]
        assert ids == ["JR002362", "JR002187", "JR002663"]
        assert postings[0].url == (
            "https://draper.wd5.myworkdayjobs.com/en-US/Draper_Careers"
            "/job/Cambridge-MA/Integration-and-Test-Engineer_JR002362"
        )
        assert postings[0].location == "Cambridge, MA"

    def test_later_pages_reporting_total_zero_still_paginate(self):
        # Real Workday behavior: only the first page carries the true total.
        page1 = {"total": 21, "jobPostings": load_fixture_json("workday_jobs_page1.json")["jobPostings"]}
        page2 = {"total": 0, "jobPostings": load_fixture_json("workday_jobs_page2.json")["jobPostings"]}

        def handler(request):
            offset = json.loads(request.content)["offset"]
            if offset == 0:
                return httpx.Response(200, json=page1)
            if offset == 20:
                return httpx.Response(200, json=page2)
            return httpx.Response(200, json={"total": 0, "jobPostings": []})

        postings = workday.fetch(WD_BOARD, client=mock_client(handler))
        assert len(postings) == 3

    def test_schema_drift_raises_adapter_error(self):
        client = mock_client(lambda req: httpx.Response(200, json={"total": "?", "oops": []}))
        with pytest.raises(AdapterError):
            workday.fetch(WD_BOARD, client=client)

    def test_http_error_raises_adapter_error(self):
        client = mock_client(lambda req: httpx.Response(500))
        with pytest.raises(AdapterError):
            workday.fetch(WD_BOARD, client=client)
