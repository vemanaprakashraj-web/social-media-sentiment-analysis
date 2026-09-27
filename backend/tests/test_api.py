"""End-to-end API contract, demo mode, and export tests."""

from __future__ import annotations

import csv
import io

import openpyxl
import pytest


# ------------------------------------------------------------------ system

def test_database_url_is_normalized() -> None:
    """Provider URLs must not need manual driver editing.

    Render, Neon, Supabase and Railway all hand out ``postgresql://`` URLs,
    whose SQLAlchemy default driver is psycopg2 — not a dependency here. An
    un-normalised URL fails at import time, which took the whole service down.
    """
    from app.config import Settings

    base = {"DATABASE_URL": "postgresql://user:pass@host:5432/db"}
    assert Settings(**base).database_url == "postgresql+psycopg://user:pass@host:5432/db"
    # The legacy alias must be upgraded too.
    assert (
        Settings(DATABASE_URL="postgres://user:pass@host:5432/db").database_url
        == "postgresql+psycopg://user:pass@host:5432/db"
    )
    # An explicit driver is respected, not overwritten.
    assert (
        Settings(DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/db").database_url
        == "postgresql+psycopg2://user:pass@host:5432/db"
    )
    # SQLite is untouched.
    assert Settings(DATABASE_URL="sqlite:///./x.db").database_url == "sqlite:///./x.db"


def test_blank_database_url_falls_back_to_sqlite() -> None:
    from app.config import Settings

    assert Settings(DATABASE_URL="").database_url.startswith("sqlite:///")


def test_health_reports_configuration_without_secrets(client) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert {p["key"] for p in body["platforms"]} == {"youtube", "facebook", "instagram"}
    # No credential values may ever be returned.
    assert "YOUTUBE_API_KEY" not in str(body).upper().replace("YOUTUBE_API_KEY\": \"", "")


def test_platforms_endpoint(client) -> None:
    response = client.get("/api/platforms")
    assert response.status_code == 200
    body = response.json()
    assert len(body["platforms"]) == 3
    for platform in body["platforms"]:
        assert platform["credential_env_var"]
        assert platform["limitations"]


# ----------------------------------------------------------------- detect

def test_detect_endpoint(client) -> None:
    response = client.post("/api/detect", json={"url": "https://youtu.be/dQw4w9WgXcQ"})
    assert response.status_code == 200
    assert response.json()["platform"] == "youtube"


def test_detect_rejects_bad_url(client) -> None:
    response = client.post("/api/detect", json={"url": "nonsense"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_url"


def test_detect_rejects_unsupported_platform(client) -> None:
    response = client.post("/api/detect", json={"url": "https://twitter.com/a/status/1"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_platform"


def test_detect_rejects_empty_url(client) -> None:
    response = client.post("/api/detect", json={"url": "   "})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


# ------------------------------------------------------------- demo mode

def test_demo_analysis_completes(demo_analysis: dict) -> None:
    assert demo_analysis["status"] == "completed"
    assert demo_analysis["data_mode"] == "demo"
    assert demo_analysis["platform"] == "youtube"
    assert demo_analysis["total_records"] > 50
    assert demo_analysis["sentiment_summary"]["total"] == demo_analysis["total_records"]


def test_demo_analysis_is_clearly_labelled(demo_analysis: dict) -> None:
    assert "DEMO DATA" in demo_analysis["demo_notice"]
    assert demo_analysis["limitations"][0].upper().startswith("DEMO DATA")


def test_demo_analysis_covers_every_platform(client) -> None:
    for platform in ("youtube", "facebook", "instagram"):
        response = client.post("/api/demo", json={"platform": platform, "user_name": "Tester"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["platform"] == platform
        assert body["data_mode"] == "demo"
        assert body["total_records"] > 0


def test_demo_rejects_unknown_platform(client) -> None:
    response = client.post("/api/demo", json={"platform": "tiktok"})
    assert response.status_code == 422


def test_youtube_demo_reports_shares_unavailable(demo_analysis: dict) -> None:
    # The YouTube Data API has no share count; it must never be invented.
    assert demo_analysis["engagement"]["shares"] is None
    assert "shares" in demo_analysis["unavailable_fields"]


def test_demo_cleans_the_dataset(demo_analysis: dict) -> None:
    report = demo_analysis["cleaning_report"]
    assert report["input_count"] > report["output_count"]
    assert report["removed_duplicate"] >= 1
    assert report["output_count"] == demo_analysis["total_records"]


def test_demo_produces_statistics_and_charts(demo_analysis: dict) -> None:
    statistics = demo_analysis["statistics"]
    assert statistics["descriptive"]["Sentiment (compound)"]["count"] > 0
    assert len(statistics["correlations"]["matrix"]) > 0
    charts = demo_analysis["charts"]
    assert len(charts["sentiment_donut"]) == 3
    assert charts["sentiment_timeline"]["available"] is True


def test_demo_produces_insights_and_keywords(demo_analysis: dict) -> None:
    assert len(demo_analysis["insights"]) >= 3
    assert len(demo_analysis["keywords"]) > 0
    assert all(word["word"] and word["count"] > 0 for word in demo_analysis["keywords"])


def test_live_analysis_without_credentials_is_rejected(client) -> None:
    response = client.post("/api/analyze", json={"url": "https://youtu.be/dQw4w9WgXcQ"})
    if response.status_code == 200:
        pytest.skip("A live API key is configured in this environment")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "missing_credentials"


# ------------------------------------------------------------ read access

def test_get_analysis_by_id(demo_analysis: dict, client) -> None:
    response = client.get(f"/api/analysis/{demo_analysis['analysis_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["analysis_id"] == demo_analysis["analysis_id"]
    assert len(body["records"]) == body["total_records"]


def test_unknown_analysis_returns_404(client) -> None:
    response = client.get("/api/analysis/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_comments_endpoint_paginates(demo_analysis: dict, client) -> None:
    analysis_id = demo_analysis["analysis_id"]
    page = client.get(f"/api/analysis/{analysis_id}/comments?page=1&page_size=5").json()
    assert page["page_size"] == 5
    assert len(page["records"]) == 5
    assert page["pages"] > 1

    second = client.get(f"/api/analysis/{analysis_id}/comments?page=2&page_size=5").json()
    assert second["records"][0]["id"] != page["records"][0]["id"]


def test_comments_filter_by_sentiment(demo_analysis: dict, client) -> None:
    analysis_id = demo_analysis["analysis_id"]
    negative = client.get(f"/api/analysis/{analysis_id}/comments?sentiment=negative&page_size=100").json()
    assert negative["total"] > 0
    assert all(record["sentiment"] == "negative" for record in negative["records"])


def test_comments_search(demo_analysis: dict, client) -> None:
    analysis_id = demo_analysis["analysis_id"]
    result = client.get(f"/api/analysis/{analysis_id}/comments?search=audio&page_size=100").json()
    assert result["total"] > 0
    assert all("audio" in record["raw_text"].lower() for record in result["records"])


def test_comments_sort_by_likes(demo_analysis: dict, client) -> None:
    analysis_id = demo_analysis["analysis_id"]
    result = client.get(
        f"/api/analysis/{analysis_id}/comments?sort=likes&order=desc&page_size=10"
    ).json()
    likes = [r["like_count"] for r in result["records"] if r["like_count"] is not None]
    assert likes == sorted(likes, reverse=True)


def test_comments_rejects_bad_sort_order(demo_analysis: dict, client) -> None:
    response = client.get(f"/api/analysis/{demo_analysis['analysis_id']}/comments?order=sideways")
    assert response.status_code == 422


def test_sentiment_endpoint(demo_analysis: dict, client) -> None:
    response = client.get(f"/api/analysis/{demo_analysis['analysis_id']}/sentiment")
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["total"] > 0
    assert body["method"] in {"vader", "lexicon"}
    assert len(body["comparison"]) > 0
    row = body["comparison"][0]
    assert "vader_compound" in row and "textblob_polarity" in row


def test_engagement_endpoint(demo_analysis: dict, client) -> None:
    response = client.get(f"/api/analysis/{demo_analysis['analysis_id']}/engagement")
    assert response.status_code == 200
    body = response.json()
    assert body["engagement"]["views"] is not None
    assert body["engagement"]["shares"] is None  # YouTube
    assert "shares" in body["unavailable_fields"]


# ---------------------------------------------------------------- history

def test_history_lists_analyses(client) -> None:
    response = client.get("/api/history?user_name=Tester")
    assert response.status_code == 200
    assert len(response.json()["analyses"]) > 0


def test_profile_aggregates(client) -> None:
    body = client.get("/api/profile/Tester").json()
    assert body["total_analyses"] > 0
    assert body["total_records_analyzed"] > 0
    assert body["favorite_platform"] in {"youtube", "facebook", "instagram"}


def test_delete_analysis(client) -> None:
    created = client.post("/api/demo", json={"platform": "youtube", "user_name": "Deleter"}).json()
    analysis_id = created["analysis_id"]
    assert client.delete(f"/api/history/{analysis_id}").status_code == 200
    assert client.get(f"/api/analysis/{analysis_id}").status_code == 404
    # Deleting twice is a clean 404, not a 500.
    assert client.delete(f"/api/history/{analysis_id}").status_code == 404


# --------------------------------------------------------------- exports

def test_csv_export(demo_analysis: dict, client) -> None:
    response = client.get(f"/api/analysis/{demo_analysis['analysis_id']}/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    text = response.content.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    # The file must stay strictly tabular so pandas can load it directly.
    assert len(rows) == demo_analysis["total_records"]
    header = set(rows[0].keys())
    for column in ("platform", "comment_text", "cleaned_comment", "sentiment", "vader_compound"):
        assert column in header
    # The YouTube demo has no share count, so the cell must be empty, not "0".
    assert rows[0]["shares"] == ""
    # Every row carries its provenance mode.
    assert {row["data_mode"] for row in rows} == {"demo"}


def test_raw_csv_export_contains_original_text(demo_analysis: dict, client) -> None:
    response = client.get(f"/api/analysis/{demo_analysis['analysis_id']}/export/csv?dataset=raw")
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
    # Raw includes the duplicate/empty rows the cleaning step removed.
    assert len(rows) >= demo_analysis["total_records"]


def test_excel_export_has_all_sheets(demo_analysis: dict, client) -> None:
    response = client.get(f"/api/analysis/{demo_analysis['analysis_id']}/export/excel")
    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]

    workbook = openpyxl.load_workbook(io.BytesIO(response.content))
    for sheet in (
        "Summary",
        "Raw Data",
        "Clean Data",
        "Sentiment Analysis",
        "Engagement Analysis",
        "Keywords",
        "Hashtags",
        "Data Limitations",
    ):
        assert sheet in workbook.sheetnames, f"missing worksheet: {sheet}"

    clean = workbook["Clean Data"]
    assert clean.freeze_panes is not None
    assert clean.auto_filter.ref is not None


def test_html_report_contains_limitations(demo_analysis: dict, client) -> None:
    response = client.get(f"/api/analysis/{demo_analysis['analysis_id']}/export/report?format=html")
    assert response.status_code == 200
    body = response.content.decode("utf-8")
    assert "DEMO DATA" in body
    assert "Data Limitations" in body
    assert "SocialScope AI" in body


def test_pdf_report_is_a_pdf(demo_analysis: dict, client) -> None:
    response = client.get(f"/api/analysis/{demo_analysis['analysis_id']}/export/report?format=pdf")
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
    assert len(response.content) > 2000


def test_export_of_unknown_analysis_returns_404(client) -> None:
    assert client.get("/api/analysis/nope/export/csv").status_code == 404
    assert client.get("/api/analysis/nope/export/excel").status_code == 404


# ------------------------------------------------------- error hygiene

def test_errors_never_leak_stack_traces(client) -> None:
    response = client.get("/api/analysis/nope")
    payload = response.json()
    assert set(payload) == {"error"}
    assert "Traceback" not in str(payload)
    assert "File \"" not in str(payload)


def test_unknown_route_returns_friendly_404(client) -> None:
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert "error" in response.json()
