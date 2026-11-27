"""The native source reader must preserve reports and the application's isolation boundary."""

import gzip
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from sbml4humans import isolation, limits, native, report
from sbml4humans.resources import EXAMPLES_DIR, OMEX_COMPMODELS, OMEX_ICGMODEL


def test_native_validation_worker_does_not_call_the_python_validator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real native session validates inside the existing isolated-worker entrypoint."""
    pytest.importorskip("sbml4humans_core")
    monkeypatch.setenv("SBML4HUMANS_PARSER", "rust")
    monkeypatch.setattr(
        report, "_read", Mock(side_effect=AssertionError("Python source reader called"))
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
    "name", sorted(path.name for path in EXAMPLES_DIR.glob("*.xml"))
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
    core = SimpleNamespace(
        REPORT_CONTRACT="report/1",
        SOURCE_CONTRACT="source/1",
        SOURCE_PATH_CONTRACT="source-path/1",
    )
    monkeypatch.setattr(native.importlib, "import_module", Mock(return_value=core))
    assert (
        native.validation_source(
            EXAMPLES_DIR / "validation.xml",
            limits.ContentLimits.current(),
            10000,
            "auto",
        )
        is None
    )
    with pytest.raises(RuntimeError, match="validation feature"):
        native.validation_source(
            EXAMPLES_DIR / "validation.xml",
            limits.ContentLimits.current(),
            10000,
            "rust",
        )


def test_native_validation_errors_never_retry_the_python_validator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A selected native validator's failure reaches the existing error boundary."""
    fail = Mock(side_effect=ValueError("native validation failure"))
    monkeypatch.setattr(native, "validation_source", fail)
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
    monkeypatch.setenv("SBML4HUMANS_PARSER", "python")
    expected = report.report_for_path(path).model_dump_json(by_alias=True).encode()
    actual = native.report_json(path, limits.ContentLimits.current(), 10000, "rust")
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


@pytest.mark.parametrize(
    "format", ["python", "diffrax", "julia", "r", "latex", "markdown", "typst"]
)
@pytest.mark.parametrize("path", [EXAMPLES_DIR / "reaction.xml", OMEX_COMPMODELS])
def test_native_ode_download_preserves_the_shared_generator_output(
    path: Path, format: str
) -> None:
    """Source selection, metadata and every generated byte match the compatibility path."""
    pytest.importorskip("sbml4humans_core")
    expected = report.ode_for_path(path, format, trusted=True, parser="python")
    actual = report.ode_for_path(path, format, trusted=True, parser="rust")
    assert actual == expected


def test_trusted_native_sources_do_not_prepare_any_python_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Trusted reports and ODE downloads use the same native source admission as uploads."""
    pytest.importorskip("sbml4humans_core")
    monkeypatch.setattr(
        report, "_read", Mock(side_effect=AssertionError("Python source reader called"))
    )
    path = EXAMPLES_DIR / "minimal_model_comp.xml"
    assert report.report_for_path(path, trusted=True, parser="rust").reports
    assert report.ode_for_path(
        path, "python", trusted=True, parser="rust"
    ).filename.endswith(".py")


@pytest.mark.parametrize("budget", [1, 20, 10000])
def test_native_comp_work_gate_matches_python(budget: int) -> None:
    """Repeated instances share the report's expansion estimate before native validation."""
    pytest.importorskip("sbml4humans_core")
    path = EXAMPLES_DIR / "minimal_model_comp.xml"

    def run(parser: native.Parser) -> list:
        return list(
            report.validate_source(
                report.SourceJob(
                    str(path), True, budget, limits.ContentLimits.current(), parser
                )
            )
        )

    assert run("rust") == run("python")


@pytest.mark.parametrize("path", [OMEX_COMPMODELS, OMEX_ICGMODEL])
def test_native_archive_validation_preserves_entry_order_and_diagnostics(
    path: Path,
) -> None:
    """Closed comp resolution uses canonical archive locations without Python extraction."""
    pytest.importorskip("sbml4humans_core")

    def run(parser: native.Parser) -> list:
        return list(
            report.validate_source(
                report.SourceJob(
                    str(path), False, 10000, limits.ContentLimits.current(), parser
                )
            )
        )

    assert run("rust") == run("python")


@pytest.mark.skipif(
    sys.platform != "linux", reason="requires Linux address-space limits"
)
def test_native_source_allocation_failure_keeps_the_memory_status(
    tmp_path: Path,
) -> None:
    """Exercise the actual Rust allocator termination and its worker status."""
    pytest.importorskip("sbml4humans_core")
    path = tmp_path / "large.xml"
    with path.open("w") as stream:
        stream.write(
            '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2"><model id="m"><listOfParameters>'
        )
        for index in range(100000):
            stream.write(f'<parameter id="p{index}" value="1" constant="true"/>')
        stream.write("</listOfParameters></model></sbml>")
    code = """
import resource, sys
from pathlib import Path
import sbml4humans_core as core
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
size = int(next(line.split()[1] for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('VmSize:'))) * 1024
resource.setrlimit(resource.RLIMIT_AS, (size + 16 * 1024 * 1024,) * 2)
core.validation_source(sys.argv[1])
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert (
        isolation._abnormal_end(result.returncode, result.stderr, "validation")
        == "memory"
    )


@pytest.mark.parametrize(
    "case", ["model-list", "reaction-list", "unicode-one-line", "multiline-attributes"]
)
def test_native_issue_positions_include_plain_lists_and_unusual_columns(
    case: str, tmp_path: Path
) -> None:
    """Preserve issue links for unreported containers and authored XML coordinates."""
    pytest.importorskip("sbml4humans_core")
    content = (EXAMPLES_DIR / "validation.xml").read_text()
    if case == "model-list":
        content = content.replace("<listOfParameters>", '<listOfParameters foo="1">')
    elif case == "reaction-list":
        content = content.replace("<listOfReactants>", '<listOfReactants foo="1">')
    elif case == "unicode-one-line":
        content = " ".join(
            content.replace('name="model with', 'name="αβ model with').split()
        )
    else:
        content = content.replace('<parameter id="k1"', '<parameter\n id="k1"')
    path = tmp_path / "input.xml"
    path.write_text(content)

    def run(parser: native.Parser) -> list:
        return list(
            report.validate_source(
                report.SourceJob(
                    str(path), False, 10000, limits.ContentLimits.current(), parser
                )
            )
        )

    assert run("rust") == run("python")
