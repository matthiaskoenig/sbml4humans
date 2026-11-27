"""The native source reader must preserve reports and the application's isolation boundary."""

import gzip
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from sbml4humans import limits, native, report
from sbml4humans.resources import EXAMPLES_DIR, OMEX_COMPMODELS


def test_native_validation_worker_does_not_call_the_python_validator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real native session validates inside the existing isolated-worker entrypoint."""
    pytest.importorskip("sbml4humans_core")
    monkeypatch.setenv("SBML4HUMANS_PARSER", "rust")
    monkeypatch.setattr(
        report, "validate", Mock(side_effect=AssertionError("Python validator called"))
    )
    job = report.SourceJob(
        path=str(EXAMPLES_DIR / "validation.xml"),
        trusted=False,
        budget=10000,
        limits=limits.ContentLimits.current(),
    )
    results = list(report.validate_source(job))
    assert results[0] == ("", ["./model.xml"])
    assert 10601 in {issue.rule for issue in results[1][1].issues}


@pytest.mark.parametrize(
    "name",
    [
        "validation.xml",
        "reaction.xml",
        "minimal_model_comp.xml",
        "comp_deletion.xml",
        "fbc_constraints_v3.xml",
        "qual_example.xml",
        "distrib_comp.xml",
    ],
)
def test_native_validation_preserves_every_diagnostic(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep rule IDs, messages, order, severities, source positions and element keys."""
    pytest.importorskip("sbml4humans_core")
    path = EXAMPLES_DIR / name
    monkeypatch.setenv("SBML4HUMANS_PARSER", "python")
    expected = report.validation_for_path(path, trusted=True)
    monkeypatch.setenv("SBML4HUMANS_PARSER", "rust")
    actual = report.validation_for_path(path, trusted=True)
    assert actual == expected


def test_explicit_native_validation_requires_the_validation_feature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A report-only wheel is optional in auto mode and actionable in Rust mode."""
    core = SimpleNamespace(REPORT_CONTRACT="report/1", SOURCE_CONTRACT="source/1")
    monkeypatch.setattr(native.importlib, "import_module", Mock(return_value=core))
    assert native.validator("auto") is None
    with pytest.raises(RuntimeError, match="validation feature"):
        native.validator("rust")


def test_native_validation_errors_never_retry_the_python_validator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A selected native validator's failure reaches the existing error boundary."""
    fail = Mock(side_effect=ValueError("native validation failure"))
    monkeypatch.setattr(native, "validator", Mock(return_value=fail))
    python = Mock(side_effect=AssertionError("Python validator called"))
    monkeypatch.setattr(report, "validate", python)
    job = report.SourceJob(
        path=str(EXAMPLES_DIR / "validation.xml"),
        trusted=False,
        budget=10000,
        limits=limits.ContentLimits.current(),
    )
    with pytest.raises(ValueError, match="native validation failure"):
        list(report.validate_source(job))
    python.assert_not_called()


def test_native_validation_runs_through_the_http_api(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A request captures native validation selection before entering its worker."""
    pytest.importorskip("sbml4humans_core")
    content = (EXAMPLES_DIR / "validation.xml").read_bytes()
    monkeypatch.setenv("SBML4HUMANS_PARSER", "python")
    expected = report.validation_for_bytes(content).model_dump(by_alias=True)
    monkeypatch.setenv("SBML4HUMANS_PARSER", "rust")
    response = client.post(
        "/api/validation/content",
        content=content,
        headers={"Content-Type": "application/xml"},
    )
    assert response.status_code == 200
    assert response.json() == expected


def _normalized(content: bytes) -> dict:
    """Normalize request identity and diagnostics, preserving every report field."""
    response = json.loads(content)
    response["uid"] = ""
    for entry in response["reports"].values():
        entry["debug"]["jsonReportTime"] = ""
    return response


def test_python_selection_does_not_import_the_native_extension(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Python path remains usable without a native wheel."""
    monkeypatch.setenv("SBML4HUMANS_PARSER", "python")
    loader = Mock(side_effect=AssertionError("unexpected native import"))
    monkeypatch.setattr(native.importlib, "import_module", loader)
    assert native._reader() is None
    loader.assert_not_called()


def test_an_explicit_native_request_never_silently_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing or incompatible native builds produce an actionable error."""
    monkeypatch.setenv("SBML4HUMANS_PARSER", "rust")
    missing = ModuleNotFoundError("missing", name="sbml4humans_core")
    monkeypatch.setattr(native.importlib, "import_module", Mock(side_effect=missing))
    with pytest.raises(RuntimeError, match="not installed"):
        native._reader()
    monkeypatch.setattr(native.importlib, "import_module", Mock(return_value=object()))
    with pytest.raises(RuntimeError):
        native._reader()


@pytest.mark.parametrize(
    "path",
    [
        EXAMPLES_DIR / "minimal_model.xml",
        EXAMPLES_DIR / "distrib_uncertainties.xml",
        OMEX_COMPMODELS,
    ],
)
def test_native_sources_preserve_the_complete_python_response(
    path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test the real installed extension across core, packages and external models."""
    pytest.importorskip("sbml4humans_core")
    monkeypatch.setenv("SBML4HUMANS_PARSER", "rust")
    expected = report.report_for_path(path).model_dump_json(by_alias=True).encode()
    actual = native.report_json(path, limits.ContentLimits.current(), 10000)
    assert actual is not None
    assert _normalized(actual) == _normalized(expected)


def test_native_report_child_entrypoint_does_not_rebuild_in_python(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use the actual binding, proving the worker path preserves serialized native bytes."""
    pytest.importorskip("sbml4humans_core")
    monkeypatch.setenv("SBML4HUMANS_PARSER", "rust")
    path = tmp_path / "model"
    path.write_bytes((EXAMPLES_DIR / "minimal_model.xml").read_bytes())
    monkeypatch.setattr(
        report,
        "report_for_path",
        Mock(side_effect=AssertionError("Python report builder called")),
    )
    job = report.ReportJob(
        path=str(path),
        trusted=False,
        limits=limits.ContentLimits.current(),
        budget=10000,
    )
    [(key, content)] = list(report.report_gzip(job))
    assert key == report._REPORT
    assert (
        json.loads(gzip.decompress(content))["reports"]["./model.xml"]["report"][
            "models"
        ][0]["id"]
        == "minimal_model"
    )


def test_the_selected_native_parser_reaches_the_isolated_api_child(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A forkserver child uses the parser captured by its request, not stale server environment."""
    core = pytest.importorskip("sbml4humans_core")
    content = b"<not-sbml/>"
    with pytest.raises(ValueError) as expected:
        core.source_json(content)
    monkeypatch.setenv("SBML4HUMANS_PARSER", "rust")
    response = client.post(
        "/api/content", content=content, headers={"Content-Type": "application/xml"}
    )
    assert response.status_code == 200
    assert response.json()["errors"] == [str(expected.value)]
