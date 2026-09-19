"""Tests of the resolution of external model definitions."""

import hashlib

import pytest

from sbml4humans.external import ExternalModels, normalize_location, resolve_source
from sbml4humans.model import (
    ExternalModelDefinition,
    ExternalModelResolution,
    Model,
    Report,
    ResolutionStatus,
    SBMLDocument,
)


@pytest.mark.parametrize(
    ("location", "normalized"),
    [
        ("./models/a.xml", "models/a.xml"),
        ("models/a.xml", "models/a.xml"),
        ("/models/a.xml", "models/a.xml"),
        ("./models/../a.xml", "a.xml"),
        ("./model.xml", "model.xml"),
        ("../a.xml", None),
        ("./models/../../a.xml", None),
        (".", None),
    ],
)
def test_normalize_location(location: str, normalized: str | None) -> None:
    """Two spellings of one entry are one location, none leaves the archive."""
    assert normalize_location(location) == normalized


@pytest.mark.parametrize(
    ("location", "source", "resolved"),
    [
        # next to the referencing entry
        ("./models/body.xml", "liver.xml", "models/liver.xml"),
        ("./models/body.xml", "./liver.xml", "models/liver.xml"),
        ("./body.xml", "organs/liver.xml", "organs/liver.xml"),
        ("./models/body.xml", "../organs/liver.xml", "organs/liver.xml"),
        # a leading slash names the root of the archive
        ("./models/body.xml", "/organs/liver.xml", "organs/liver.xml"),
        # a uri is percent encoded
        ("./body.xml", "my%20liver.xml", "my liver.xml"),
        # nothing outside of the archive
        ("./body.xml", "../liver.xml", None),
        ("./models/body.xml", "../../liver.xml", None),
        # nothing with a scheme
        ("./body.xml", "https://example.org/liver.xml", None),
        ("./body.xml", "urn:miriam:biomodels.db:BIOMD0000000001", None),
        ("./body.xml", "file:///etc/passwd", None),
        ("./body.xml", "", None),
    ],
)
def test_resolve_source(location: str, source: str, resolved: str | None) -> None:
    """A source is resolved against the directory of the entry which names it."""
    assert resolve_source(location, source) == resolved


def _report(
    models: list[str], emds: list[ExternalModelDefinition] | None = None
) -> Report:
    """A report with the models of the ids, the first one being the main model."""
    return Report(
        document=SBMLDocument(pk="_/SBMLDocument:_", level=3, version=1),
        models=[
            Model(
                pk=f"{model}/Model:{model}",
                id=model,
                kind="model" if k == 0 else "modelDefinition",
            )
            for k, model in enumerate(models)
        ],
        external_model_definitions=emds or [],
    )


def _emd(
    id_: str, source: str, model_ref: str | None = None, md5: str | None = None
) -> ExternalModelDefinition:
    """An external model definition."""
    return ExternalModelDefinition(
        pk=f"_/ExternalModelDefinition:{id_}",
        id=id_,
        source=source,
        model_ref=model_ref,
        md5=md5,
    )


def test_a_model_of_another_entry_is_resolved() -> None:
    """The source names the entry and the modelRef the model inside it."""
    emd = _emd("liver", "liver.xml", "liver_def")
    models = ExternalModels(
        {
            "./models/body.xml": _report(["body"], [emd]),
            "./models/liver.xml": _report(["liver", "liver_def"]),
        }
    )
    assert models.resolve("./models/body.xml", emd) == ExternalModelResolution(
        status=ResolutionStatus.RESOLVED,
        entry="./models/liver.xml",
        model="liver_def/Model:liver_def",
    )


def test_without_model_ref_the_main_model_is_meant() -> None:
    """The model of the document, not one of its model definitions (comp §3.3.2)."""
    emd = _emd("liver", "liver.xml")
    models = ExternalModels(
        {
            "./body.xml": _report(["body"], [emd]),
            "./liver.xml": _report(["liver", "liver_def"]),
        }
    )
    resolution = models.resolve("./body.xml", emd)
    assert resolution.status == ResolutionStatus.RESOLVED
    assert resolution.model == "liver/Model:liver"


def test_the_manifest_may_spell_a_location_in_another_way() -> None:
    """The entry is found and named the way the manifest names it."""
    emd = _emd("liver", "./liver.xml", "liver")
    models = ExternalModels(
        {"./body.xml": _report(["body"], [emd]), "liver.xml": _report(["liver"])}
    )
    assert models.resolve("./body.xml", emd).entry == "liver.xml"


def test_a_remote_source_is_not_fetched() -> None:
    """A source with a scheme is remote, whatever the archive holds."""
    emd = _emd("liver", "https://example.org/liver.xml", "liver")
    models = ExternalModels({"./body.xml": _report(["body"], [emd])})
    assert models.resolve("./body.xml", emd) == ExternalModelResolution(
        status=ResolutionStatus.REMOTE_SOURCE
    )


def test_a_missing_entry_is_not_found() -> None:
    """Neither a file which is not there nor one outside of the archive."""
    missing = _emd("liver", "liver.xml", "liver")
    outside = _emd("kidney", "../kidney.xml", "kidney")
    models = ExternalModels({"./body.xml": _report(["body"], [missing, outside])})
    for emd in (missing, outside):
        assert models.resolve("./body.xml", emd) == ExternalModelResolution(
            status=ResolutionStatus.NOT_FOUND
        )


def test_an_entry_without_report_is_not_sbml() -> None:
    """The entry is there and named, but the report has no model of it."""
    emd = _emd("readme", "README.md")
    models = ExternalModels(
        {"./body.xml": _report(["body"], [emd])}, locations=["./README.md"]
    )
    assert models.resolve("./body.xml", emd) == ExternalModelResolution(
        status=ResolutionStatus.NOT_SBML, entry="./README.md"
    )


def test_an_unknown_model_ref_is_model_not_found() -> None:
    """The entry is named, the model is not."""
    emd = _emd("liver", "liver.xml", "kidney")
    models = ExternalModels(
        {"./body.xml": _report(["body"], [emd]), "./liver.xml": _report(["liver"])}
    )
    assert models.resolve("./body.xml", emd) == ExternalModelResolution(
        status=ResolutionStatus.MODEL_NOT_FOUND, entry="./liver.xml"
    )
    # a document without a model has no main model either
    empty = _emd("empty", "empty.xml")
    models = ExternalModels(
        {"./body.xml": _report(["body"], [empty]), "./empty.xml": _report([])}
    )
    assert models.resolve("./body.xml", empty).status == (
        ResolutionStatus.MODEL_NOT_FOUND
    )


def test_a_chain_of_external_model_definitions_is_followed() -> None:
    """A modelRef may name an external model definition of the other document."""
    emd = _emd("liver", "liver.xml", "hepatocyte")
    hop = _emd("hepatocyte", "cells/hepatocyte.xml", "cell")
    models = ExternalModels(
        {
            "./body.xml": _report(["body"], [emd]),
            "./liver.xml": _report(["liver"], [hop]),
            "./cells/hepatocyte.xml": _report(["cell"]),
        }
    )
    assert models.resolve("./body.xml", emd) == ExternalModelResolution(
        status=ResolutionStatus.RESOLVED,
        entry="./cells/hepatocyte.xml",
        model="cell/Model:cell",
    )


def test_a_chain_which_ends_nowhere_says_where() -> None:
    """The status is the one of the last definition, the entry the last one found."""
    emd = _emd("liver", "liver.xml", "hepatocyte")
    hop = _emd("hepatocyte", "https://example.org/hepatocyte.xml")
    models = ExternalModels(
        {"./body.xml": _report(["body"], [emd]), "./liver.xml": _report([], [hop])}
    )
    assert models.resolve("./body.xml", emd) == ExternalModelResolution(
        status=ResolutionStatus.REMOTE_SOURCE, entry="./liver.xml"
    )


def test_a_circle_is_found() -> None:
    """Two definitions which name each other resolve to no model."""
    a = _emd("a", "b.xml", "b")
    b = _emd("b", "a.xml", "a")
    models = ExternalModels(
        {"./a.xml": _report(["main_a"], [a]), "./b.xml": _report(["main_b"], [b])}
    )
    assert models.resolve("./a.xml", a).status == ResolutionStatus.CIRCULAR


def test_the_md5_is_compared_with_the_entry() -> None:
    """A mismatch is stated and does not stop the resolution."""
    content = b"<sbml/>"
    md5 = hashlib.md5(content, usedforsecurity=False).hexdigest()
    right = _emd("right", "liver.xml", "liver", md5=md5.upper())
    wrong = _emd("wrong", "liver.xml", "liver", md5="0" * 32)
    unset = _emd("unset", "liver.xml", "liver")
    models = ExternalModels(
        {
            "./body.xml": _report(["body"], [right, wrong, unset]),
            "./liver.xml": _report(["liver"]),
        },
        checksums={"./liver.xml": md5},
    )
    models.resolve_all()
    assert right.resolution.md5_matches is True
    assert wrong.resolution.md5_matches is False
    assert wrong.resolution.status == ResolutionStatus.RESOLVED
    assert unset.resolution.md5_matches is None


def test_resolve_all_writes_every_resolution() -> None:
    """Every definition of every report carries its resolution afterwards."""
    emd = _emd("liver", "liver.xml", "liver")
    models = ExternalModels(
        {"./body.xml": _report(["body"], [emd]), "./liver.xml": _report(["liver"])}
    )
    assert emd.resolution.status == ResolutionStatus.NOT_FOUND
    models.resolve_all()
    assert emd.resolution.status == ResolutionStatus.RESOLVED
    target = models.model("./body.xml", emd)
    assert target is not None
    assert (target.location, target.model.pk) == ("./liver.xml", "liver/Model:liver")
