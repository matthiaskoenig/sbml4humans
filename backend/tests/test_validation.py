"""Tests of the validation of a document and the mapping of its issues."""

import functools
import http.server
import os
import signal
import sys
import tempfile
import threading
import time
import zipfile
from collections.abc import Callable, Generator, Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from conftest import SLOW_CONTENT_WORK

from sbml4humans import isolation, limits, report
from sbml4humans.limits import MAX_EXPANDED_ELEMENTS
from sbml4humans.model import EntryValidation, ValidationResponse
from sbml4humans.report import (
    SourceJob,
    report_for_bytes,
    report_for_path,
    validate_source,
    validation_for_bytes,
    validation_for_path,
)
from sbml4humans.resources import EXAMPLES_DIR


COMP_DELETION = EXAMPLES_DIR / "comp_deletion.xml"


def test_unit_warnings_of_the_reaction_example() -> None:
    """The units of the compartment and of the species of the example are missing."""
    entry = _entry(validation_for_path(EXAMPLES_DIR / "reaction.xml"))
    units = {
        (issue.rule, issue.severity, issue.pk)
        for issue in entry.issues
        if issue.rule in {20513, 20616}
    }
    assert units == {
        (20513, "warning", "reaction/Compartment:c"),
        (20616, "warning", "reaction/Species:x"),
        (20616, "warning", "reaction/Species:y"),
    }


def test_unresolved_comp_example_marks_its_submodels_and_definitions() -> None:
    """Without the file they name, the definitions and the submodels are errors."""
    content = (EXAMPLES_DIR / "minimal_model_comp.xml").read_bytes()
    entry = _entry(validation_for_bytes(content))
    comp = {
        (issue.rule, issue.severity, issue.pk)
        for issue in entry.issues
        if issue.rule in {1020615, 1090101}
    }
    assert comp == {
        *(
            (1020615, "error", f"minimal_model_comp/Submodel:submodel{k}")
            for k in range(5)
        ),
        *(
            (1090101, "error", f"document/ExternalModelDefinition:emd{k}")
            for k in range(5)
        ),
    }


def _entry(
    response: ValidationResponse, location: str | None = None
) -> EntryValidation:
    """An entry of a validation response, the first by default."""
    entries = response.entries
    return entries[location] if location else next(iter(entries.values()))


def _rules(response: ValidationResponse, location: str | None = None) -> set[int]:
    """The rules of the issues of an entry of a response, the first by default."""
    return {issue.rule for issue in _entry(response, location).issues}


def test_untrusted_source_is_not_read() -> None:
    """An absolute path or a url of an untrusted document is never resolved."""
    requests: list[str] = []

    class Handler(http.server.BaseHTTPRequestHandler):
        """A server which records every request."""

        def do_GET(self) -> None:
            """Record the request and answer that nothing is there."""
            requests.append(self.path)
            self.send_response(404)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            """Log nothing."""

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        target = (EXAMPLES_DIR / "unit_definitions.xml").resolve()
        sbml = COMP_DELETION.read_text()
        for source in (str(target), f"http://127.0.0.1:{server.server_port}/u.xml"):
            content = sbml.replace(
                'comp:source="unit_definitions.xml"', f'comp:source="{source}"'
            )
            response = validation_for_bytes(content.encode())
            assert 1090101 in _rules(response), source
        assert requests == []
    finally:
        server.shutdown()


def _in_process(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate in this process rather than in a child process."""

    def run_here(
        function: Callable[[Any], Iterable[tuple[str, Any]]],
        argument: Any,
        budget: isolation.Budget,
    ) -> isolation.IsolatedRun:
        """The results of the function, without a child process."""
        return isolation.IsolatedRun(results=list(function(argument)))

    monkeypatch.setattr(isolation, "run_isolated", run_here)


_COMP = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" '
    'xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" '
    'level="3" version="1" comp:required="true">{}</sbml>'
)


def _emds(*emds: tuple[str, str, str]) -> str:
    """A list of external model definitions of id, source and model."""
    return (
        "<comp:listOfExternalModelDefinitions>"
        + "".join(
            f'<comp:externalModelDefinition comp:id="{i}" comp:source="{source}" '
            f'comp:modelRef="{ref}"/>'
            for i, source, ref in emds
        )
        + "</comp:listOfExternalModelDefinitions>"
    )


# m.xml names Bx of sub/b.xml, which is an external model definition of
# sub/b.xml naming c.xml, relative to sub/; ./c.xml is another document
_CHAIN = {
    "m.xml": _COMP.format(
        '<model id="M"><comp:listOfSubmodels>'
        '<comp:submodel comp:id="s" comp:modelRef="Bx"/>'
        '<comp:submodel comp:id="w" comp:modelRef="Wx"/>'
        "</comp:listOfSubmodels></model>"
        + _emds(("Bx", "sub/b.xml", "Bx"), ("Wx", "c.xml", "W"))
    ),
    "sub/b.xml": _COMP.format('<model id="B"/>' + _emds(("Bx", "c.xml", "C"))),
    "sub/c.xml": _COMP.format('<model id="C"/>'),
    "c.xml": _COMP.format('<model id="W"/>'),
}
_UNRESOLVED = {1090101, 1090104, 1020615}


def _check_chain(
    response: ValidationResponse, found: list[tuple[str, str | None, str]] | None
) -> None:
    """The chain is resolved within the report, each source against its base."""
    assert {"./m.xml", "./sub/b.xml", "./sub/c.xml", "./c.xml"} <= set(response.entries)
    for location, entry in response.entries.items():
        assert entry.skipped is None, location
        rules = {issue.rule for issue in entry.issues}
        assert not rules & _UNRESOLVED, location
    if found is None:
        return
    assert ("c.xml", "sub/b.xml", "C") in found
    assert ("c.xml", "./m.xml", "W") in found
    assert {model for source, _, model in found if source == "c.xml"} == {"C", "W"}


def test_every_entry_is_validated() -> None:
    """The neighbour which a trusted file names is validated as well."""
    response = validation_for_path(COMP_DELETION, trusted=True)
    assert len(response.entries) > 1
    for entry in response.entries.values():
        assert entry.skipped is None
        assert all(issue.pk for issue in entry.issues)


def test_the_entries_are_those_of_the_report(tmp_path: Path) -> None:
    """The validation has an entry per report of the source, in its order."""
    path = _archive(tmp_path / "chain.omex", _CHAIN, master="m.xml")
    assert list(validation_for_path(path).entries) == list(
        report_for_path(path).reports
    )


def test_the_report_carries_no_validation() -> None:
    """The report is built without the validation, which has endpoints of its own."""
    response = report_for_path(EXAMPLES_DIR / "validation.xml")
    data = response.model_dump(mode="json", by_alias=True)
    for entry in data["reports"].values():
        assert "validation" not in entry["report"]
        assert "validationSkipped" not in entry["report"]


def _sbml(model_id: str) -> str:
    """A document of an empty model."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" '
        f'version="1"><model id="{model_id}"/></sbml>'
    )


# -------------------------------------------------------------------------------------
# the expanded-size budget
# -------------------------------------------------------------------------------------
# a parameter without units, which only the check of consistency reports
_UNITLESS = (
    '<listOfParameters><parameter id="p" value="1" constant="true"/></listOfParameters>'
)


def _submodels(model_ref: str, n: int) -> str:
    """A list of `n` submodels of one model."""
    return (
        "<comp:listOfSubmodels>"
        + "".join(
            f'<comp:submodel comp:id="s{i}" comp:modelRef="{model_ref}"/>'
            for i in range(n)
        )
        + "</comp:listOfSubmodels>"
    )


def test_submodel_fan_out_beyond_the_budget_is_skipped(
    fan_out_document: Callable[..., bytes],
) -> None:
    """A document which expands to 111,110 instances is answered at once."""
    entry = _entry(validation_for_bytes(fan_out_document(5)))
    assert entry.skipped == "expandedSize"
    assert 80701 not in {issue.rule for issue in entry.issues}


def test_read_errors_are_reported_without_validation(
    fan_out_document: Callable[..., bytes],
) -> None:
    """A document which is not validated still has the read errors of libsbml."""
    content = fan_out_document(5).replace(b'<model id="m">', b'<model id="m" foo="1">')
    entry = _entry(validation_for_bytes(content))
    assert entry.skipped == "expandedSize"
    assert 20222 in {issue.rule for issue in entry.issues}


def test_submodel_fan_out_within_the_budget_is_validated(
    fan_out_document: Callable[..., bytes],
) -> None:
    """A document which expands to 110 instances is validated."""
    entry = _entry(validation_for_bytes(fan_out_document(2)))
    assert entry.skipped is None
    assert 80701 in {issue.rule for issue in entry.issues}


def _archive(path: Path, documents: dict[str, str], master: str | None = None) -> Path:
    """A COMBINE archive of SBML documents, the first one the master by default."""
    master = master or next(iter(documents))
    entries = "".join(
        f'<content location="./{name}" '
        'format="http://identifiers.org/combine.specifications/sbml" '
        f'master="{str(name == master).lower()}"/>'
        for name in documents
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "manifest.xml",
            '<omexManifest xmlns="http://identifiers.org/combine.specifications/'
            f'omex-manifest">{entries}</omexManifest>',
        )
        for name, content in documents.items():
            archive.writestr(name, content)
    return path


def test_archive_chain_beyond_the_budget_is_not_validated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Instances through external model definitions of other entries count."""

    def link(target: str) -> str:
        """A main model of 10 submodels of the main model of `target`."""
        return f'<model id="m">{_UNITLESS}{_submodels("x", 10)}</model>' + _emds(
            ("x", target, "m")
        )

    documents = {
        "a.xml": _COMP.format(link("b.xml")),
        "b.xml": _COMP.format(link("c.xml")),
        "c.xml": _COMP.format(link("d.xml")),
        "d.xml": _COMP.format(f'<model id="m">{_UNITLESS}</model>'),
    }
    path = _archive(tmp_path / "chain.omex", documents)
    # the submodels of a instantiate about 4,300 elements, of b 400, of c 20
    monkeypatch.setattr(limits, "MAX_EXPANDED_ELEMENTS", 1000)
    response = validation_for_path(path)
    skipped = {location: entry.skipped for location, entry in response.entries.items()}
    assert skipped == {
        "./a.xml": "expandedSize",
        "./b.xml": None,
        "./c.xml": None,
        "./d.xml": None,
    }
    assert 80701 in {i.rule for i in response.entries["./b.xml"].issues}


def test_validate_source_in_this_process() -> None:
    """What the child process runs: the entries, then each with its issues."""
    job = SourceJob(
        path=str(EXAMPLES_DIR / "validation.xml"),
        trusted=False,
        budget=MAX_EXPANDED_ELEMENTS,
        limits=limits.ContentLimits.current(),
    )
    results = list(validate_source(job))
    assert results[0] == ("", ["./model.xml"])
    assert [key for key, _ in results[1:]] == ["./model.xml"]
    assert 10601 in {issue.rule for issue in results[1][1].issues}


# -------------------------------------------------------------------------------------
# the child process: timeout, memory and concurrency
# -------------------------------------------------------------------------------------
def _gone(pid: int) -> bool:
    """Whether no process of the pid runs any more."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


@contextmanager
def _leaves_nothing(root: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Check that the server and its children leave no temporary file behind.

    The temporary directory of the server is `root` within the context, which
    has to be empty after it, and no directory of an archive may be left in the
    temporary directory of the system, which the forkserver uses.
    """
    # the forkserver keeps its socket in the temporary directory it started with
    isolation.start_forkserver()
    system = Path(tempfile.gettempdir())
    before = set(system.glob("pymetadata_omex_*"))
    root.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(root))
    yield
    assert list(root.iterdir()) == []
    assert set(system.glob("pymetadata_omex_*")) - before == set()


def _tempdir(_: object) -> Iterator[tuple[str, str | None]]:
    """The temporary directory of the child process, of python and of the system."""
    yield "tempdir", tempfile.gettempdir()
    for variable in ("TMPDIR", "TEMP", "TMP"):
        yield variable, os.environ.get(variable)


def test_a_child_has_a_temporary_directory_of_its_own(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The server makes the temporary directory of a child and removes it."""
    with _leaves_nothing(tmp_path / "tmp", monkeypatch):
        run = isolation.run_isolated(_tempdir, None, isolation.VALIDATION_BUDGET)
    results = dict(run.results)
    tempdir = Path(results["tempdir"])
    assert tempdir.parent == tmp_path / "tmp"
    assert not tempdir.exists()
    # native libraries which make temporary files find it in the environment
    for variable in ("TMPDIR", "TEMP", "TMP"):
        assert results[variable] == str(tempdir)


def _cpu_limit(_: object) -> Iterator[tuple[str, int]]:
    """The soft limit of the cpu time of the child process, in seconds."""
    import resource

    yield "cpu", resource.getrlimit(resource.RLIMIT_CPU)[0]


@pytest.mark.skipif(sys.platform == "win32", reason="no resource limits on Windows")
def test_a_child_has_a_cpu_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """A child ends itself after twice the timeout, if the server did not end it."""
    monkeypatch.setattr(isolation.VALIDATION_BUDGET, "timeout", 10.0)
    run = isolation.run_isolated(_cpu_limit, None, isolation.VALIDATION_BUDGET)
    assert dict(run.results)["cpu"] == 20


def test_timeout_terminates_the_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    slow_content: bytes,
    spy_children: list[int],
) -> None:
    """A validation beyond the timeout is ended and every entry of it skipped.

    The child is killed, the server removes what it left of the source. The
    child is killed wherever the timeout of one second finds it: an entry it
    reported is skipped for the timeout, and an entry it did not reach is
    missing from the response, which on a loaded machine is every entry of the
    source, since the child is killed before it could name them.
    """
    timeout = 1.0
    # the bound below says nothing where the deadline outlasts the work
    assert timeout < SLOW_CONTENT_WORK
    monkeypatch.setattr(isolation, "MIN_CHILD_TIME", 0.1)
    monkeypatch.setattr(isolation.VALIDATION_BUDGET, "timeout", timeout)
    start = time.perf_counter()
    with _leaves_nothing(tmp_path / "tmp", monkeypatch):
        response = validation_for_bytes(slow_content)
    elapsed = time.perf_counter() - start
    # that the timeout ended the run, and not the work of the child, is what
    # `skipped` says: a child which had finished would have sent the issues of
    # its entry instead
    assert response.skipped == "timeout"
    # the one entry of the source, or none of it, and nothing else
    assert set(response.entries) <= {"./model.xml"}
    assert all(
        entry == EntryValidation(skipped="timeout")
        for entry in response.entries.values()
    )
    assert len(spy_children) == 1
    assert _gone(spy_children[0])
    # the run does not wait for the work, which is the one thing a clock can
    # say here: the bound is the work of the source and no wall clock of its
    # own, which measured the machine and not the server (the five seconds
    # here before failed on a machine loaded with the rest of the suite, which
    # ends this run in under two)
    assert elapsed < SLOW_CONTENT_WORK


def test_timeout_keeps_the_entries_validated_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, slow_content: bytes
) -> None:
    """The entries the child validated before the timeout keep their issues."""
    monkeypatch.setattr(isolation, "MIN_CHILD_TIME", 0.1)
    monkeypatch.setattr(isolation.VALIDATION_BUDGET, "timeout", 3.0)
    documents = {
        "a.xml": (EXAMPLES_DIR / "validation.xml").read_text(),
        "b.xml": slow_content.decode(),
    }
    response = validation_for_path(_archive(tmp_path / "slow.omex", documents))
    assert response.entries["./a.xml"].skipped is None
    assert 10601 in {i.rule for i in response.entries["./a.xml"].issues}
    assert response.entries["./b.xml"].skipped == "timeout"


def _flat(species: int, submodel: bool = False) -> bytes:
    """A document of a model with many species, which take memory to read.

    With `submodel` the model has one submodel of a definition of one parameter.
    """
    model = (
        '<listOfCompartments><compartment id="c" constant="true"/>'
        "</listOfCompartments><listOfSpecies>"
        + "".join(
            f'<species id="x{k}" compartment="c" initialAmount="1" '
            'hasOnlySubstanceUnits="true" boundaryCondition="false" '
            'constant="false"/>'
            for k in range(species)
        )
        + "</listOfSpecies>"
    )
    if submodel:
        return _COMP.format(
            f'<model id="m">{model}{_submodels("d", 1)}</model>'
            '<comp:listOfModelDefinitions><comp:modelDefinition id="d">'
            f"{_UNITLESS}</comp:modelDefinition></comp:listOfModelDefinitions>"
        ).encode()
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" '
        f'version="1"><model id="m">{model}</model></sbml>'
    ).encode()


def test_memory_limit_skips_the_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, spy_children: list[int]
) -> None:
    """A validation beyond the memory limit is skipped, the parent answers.

    The child may be aborted, the server removes what it left of the source.
    """
    content = _flat(20_000)
    # the address space of the child is far beyond the limit already, so every
    # page it maps from now on fails
    monkeypatch.setattr(isolation.VALIDATION_BUDGET, "memory", 1024 * 1024)
    monkeypatch.setattr(isolation.VALIDATION_BUDGET, "timeout", 20.0)
    with _leaves_nothing(tmp_path / "tmp", monkeypatch):
        response = validation_for_bytes(content)
    assert response.skipped == "memory"
    # the child may run out of memory before it read which entries there are
    for entry in response.entries.values():
        assert entry == EntryValidation(skipped="memory")
    assert _gone(spy_children[0])


def test_validation_within_the_memory_limit() -> None:
    """The default limit leaves room for the validation."""
    entry = _entry(validation_for_path(EXAMPLES_DIR / "validation.xml"))
    assert entry.skipped is None
    assert entry.issues


@pytest.mark.parametrize("limit", [1, 2])
def test_semaphore_bounds_the_children(
    monkeypatch: pytest.MonkeyPatch, limit: int
) -> None:
    """At most as many children run at a time as the concurrency of the budget."""
    monkeypatch.setattr(isolation.VALIDATION_BUDGET, "concurrency", limit)
    running = 0
    most = 0
    lock = threading.Lock()
    run_child = isolation._run_child

    def spy(*args: Any) -> Any:
        """Count the children which run, each for at least a little while."""
        nonlocal running, most
        with lock:
            running += 1
            most = max(most, running)
        try:
            time.sleep(0.5)
            return run_child(*args)
        finally:
            with lock:
                running -= 1

    monkeypatch.setattr(isolation, "_run_child", spy)
    content = (EXAMPLES_DIR / "validation.xml").read_bytes()
    results: list[ValidationResponse] = []
    threads = [
        threading.Thread(target=lambda: results.append(validation_for_bytes(content)))
        for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert most == limit
    assert [_entry(r).skipped for r in results] == [None, None]


def test_waiting_beyond_the_timeout_is_busy(
    monkeypatch: pytest.MonkeyPatch, spy_children: list[int]
) -> None:
    """A request which gets no child before its timeout is busy, not slow."""
    monkeypatch.setattr(isolation.VALIDATION_BUDGET, "concurrency", 1)
    timeout = 1.0
    monkeypatch.setattr(isolation.VALIDATION_BUDGET, "timeout", timeout)
    # another request holds the one child
    semaphore = isolation._semaphore(isolation.VALIDATION_BUDGET)
    semaphore.acquire()
    try:
        start = time.perf_counter()
        response = validation_for_path(EXAMPLES_DIR / "validation.xml")
        elapsed = time.perf_counter() - start
    finally:
        semaphore.release()
    assert response.skipped == "busy"
    assert response.entries == {}
    # the request waited for its whole timeout, which no load shortens; how
    # much longer it took is the load of the machine and no behaviour
    assert elapsed >= timeout
    assert spy_children == []


def test_a_child_free_too_late_is_busy(
    monkeypatch: pytest.MonkeyPatch, spy_children: list[int]
) -> None:
    """A child which gets free shortly before the timeout is not started."""
    monkeypatch.setattr(isolation.VALIDATION_BUDGET, "concurrency", 1)
    timeout, min_child_time, frees = 2.0, 1.0, 1.5
    # the child is free in time for the timeout, and too late for a child
    assert timeout - min_child_time < frees < timeout
    monkeypatch.setattr(isolation.VALIDATION_BUDGET, "timeout", timeout)
    monkeypatch.setattr(isolation, "MIN_CHILD_TIME", min_child_time)
    # another request holds the one child and frees it `frees` seconds from now
    semaphore = isolation._semaphore(isolation.VALIDATION_BUDGET)
    semaphore.acquire()
    release = threading.Timer(frees, semaphore.release)
    start = time.perf_counter()
    release.start()
    response = validation_for_path(EXAMPLES_DIR / "validation.xml")
    elapsed = time.perf_counter() - start
    release.join()
    assert response.skipped == "busy"
    assert response.entries == {}
    # the request waited for the child, which no load shortens
    assert elapsed >= frees
    assert spy_children == []
    # the child is free again
    assert semaphore.acquire(timeout=0)
    semaphore.release()


def _validations_admitted() -> int:
    """The validations the server admitted, running or waiting for a child."""
    return isolation._admitted.get(isolation.VALIDATION_BUDGET.name, 0)


def test_a_client_which_leaves_ends_its_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    slow_content: bytes,
    spy_children: list[int],
    live_server: int,
    post_and_leave: Callable[..., None],
    eventually: Callable[..., bool],
) -> None:
    """A client which disconnects mid-validation frees the child and the admission."""
    # the live server of the fixture started before this context, so that it
    # keeps its uploads in the temporary directory of the system and not in `root`
    with _leaves_nothing(tmp_path / "tmp", monkeypatch):
        post_and_leave(
            live_server,
            "/api/validation/content",
            slow_content,
            lambda: bool(spy_children),
        )
        left = time.monotonic()
        assert eventually(lambda: _gone(spy_children[0]), 3.0)
        assert eventually(lambda: _validations_admitted() == 0, 3.0)
        assert time.monotonic() - left < 3.0
        # the run directory of the child is gone with it
        assert eventually(lambda: list((tmp_path / "tmp").iterdir()) == [], 3.0)


def test_a_client_which_leaves_while_waiting_frees_its_admission(
    monkeypatch: pytest.MonkeyPatch,
    spy_children: list[int],
    live_server: int,
    post_and_leave: Callable[..., None],
    eventually: Callable[..., bool],
) -> None:
    """A validation waiting for a child ends when its client disconnects."""
    monkeypatch.setattr(isolation.VALIDATION_BUDGET, "concurrency", 1)
    content = (EXAMPLES_DIR / "validation.xml").read_bytes()
    # another request holds the one child
    semaphore = isolation._semaphore(isolation.VALIDATION_BUDGET)
    semaphore.acquire()
    try:
        post_and_leave(
            live_server,
            "/api/validation/content",
            content,
            lambda: _validations_admitted() == 1,
        )
        assert eventually(lambda: _validations_admitted() == 0, 3.0)
    finally:
        semaphore.release()
    assert spy_children == []


def test_a_document_without_a_model_is_an_error() -> None:
    """The validation of a source without a model fails like its report."""
    content = _COMP.format("").encode()
    with pytest.raises(ValueError, match="No SBML model") as raised:
        validation_for_bytes(content)
    # the traceback of the child is a note of the exception
    assert any("child process" in note for note in raised.value.__notes__)
    with pytest.raises(ValueError, match="No SBML model"):
        report_for_bytes(content)


def _ends_after_first_entry(end: str, job: SourceJob) -> Iterator[tuple[str, Any]]:
    """Validate the source, end the child abnormally after its first entry."""
    for n, result in enumerate(validate_source(job)):
        yield result
        # the locations come first, then the first entry
        if n == 1:
            break
    if end == "kill":
        # what the OOM killer of the kernel does
        os.kill(os.getpid(), signal.SIGKILL)
    elif end == "abort":
        # an abort of another cause than memory, e.g. a failed assertion
        os.write(2, b"python: assertion failed\n")
        os.abort()
    elif end == "bad_alloc":
        # what libstdc++ writes when libsbml does not catch a std::bad_alloc
        os.write(
            2,
            b"terminate called after throwing an instance of 'std::bad_alloc'\n"
            b"  what():  std::bad_alloc\n",
        )
        os.abort()
    elif end == "segv":
        os.kill(os.getpid(), signal.SIGSEGV)
    elif end == "exit":
        os._exit(3)
    elif end == "silent":
        # ends without an error and without saying it is done
        os._exit(0)


@pytest.mark.skipif(sys.platform == "win32", reason="no signals on Windows")
@pytest.mark.parametrize(
    ("end", "reason"),
    [
        ("kill", "crashed"),
        ("abort", "crashed"),
        ("segv", "crashed"),
        ("exit", "crashed"),
        ("silent", "crashed"),
        ("bad_alloc", "memory"),
    ],
)
def test_an_abnormal_end_keeps_the_entries_validated_before(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    end: str,
    reason: str,
) -> None:
    """A child which ends abnormally keeps what it sent, the rest is skipped.

    Only an abort for a `std::bad_alloc` is for lack of memory, any other
    abnormal end of the child is `crashed`.
    """
    monkeypatch.setattr(
        report, "validate_source", functools.partial(_ends_after_first_entry, end)
    )
    documents = {
        "a.xml": (EXAMPLES_DIR / "validation.xml").read_text(),
        "b.xml": (EXAMPLES_DIR / "validation.xml").read_text(),
    }
    with _leaves_nothing(tmp_path / "tmp", monkeypatch):
        response = validation_for_path(_archive(tmp_path / "two.omex", documents))
    assert response.skipped == reason
    assert response.entries["./a.xml"].skipped is None
    assert 10601 in {i.rule for i in response.entries["./a.xml"].issues}
    assert response.entries["./b.xml"] == EntryValidation(skipped=reason)
    # what the child wrote before its end is in the log of the server
    written = {"abort": "assertion failed", "bad_alloc": "std::bad_alloc"}
    if end in written:
        assert written[end] in caplog.text


def _noisy(_: object) -> Iterator[tuple[str, int]]:
    """Write much and control characters to the standard error, then end well."""
    os.write(2, b"x" * 10_000 + b"\x1b[31m\r\nforged line\n" + b"the end")
    yield "done", 1


def test_the_standard_error_of_a_child_is_logged_escaped(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The log gets the end of what a child wrote, its control characters escaped."""
    run = isolation.run_isolated(_noisy, None, isolation.VALIDATION_BUDGET)
    assert run.results == [("done", 1)]
    [record] = [r for r in caplog.records if "wrote" in r.getMessage()]
    message = record.getMessage()
    assert "the end" in message
    assert "\x1b" not in message
    assert "\r" not in message
    assert "\n" not in message
    assert "\\x1b" in message
    assert len(message) < 4096 + 200


def _crash(job: SourceJob) -> Iterator[tuple[str, list[Any]]]:
    """End the child process by a signal no limit sends, before any result."""
    os.kill(os.getpid(), signal.SIGSEGV)
    yield from ()


@pytest.mark.skipif(sys.platform == "win32", reason="no signals on Windows")
def test_a_crash_before_the_entries_skips_the_validation(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A child which crashes before it read the source answers no entry."""
    monkeypatch.setattr(report, "validate_source", _crash)
    response = validation_for_path(EXAMPLES_DIR / "validation.xml")
    assert response == ValidationResponse(skipped="crashed")
    assert "signal 11 SIGSEGV" in caplog.text


def _status(_: object) -> Iterator[tuple[str, int]]:
    """The address space of the child process, in kB."""
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmSize:"):
                yield "VmSize", int(line.split()[1])


@pytest.mark.skipif(not Path("/proc/self/status").exists(), reason="Linux only")
def test_a_child_starts_with_a_small_address_space() -> None:
    """The forkserver has no thread pool of numpy whose stacks a child inherits."""
    run = isolation.run_isolated(_status, None, isolation.VALIDATION_BUDGET)
    assert dict(run.results)["VmSize"] < 600 * 1024
