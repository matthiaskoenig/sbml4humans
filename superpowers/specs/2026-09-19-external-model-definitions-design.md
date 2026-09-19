# External model definitions resolved against the entries of the archive

**Issue:** [#36](https://github.com/matthiaskoenig/sbml4humans/issues/36) - "Resolve an external model definition against the other entries of its COMBINE archive". Follows [#11](https://github.com/matthiaskoenig/sbml4humans/issues/11) and its design, [the complete SBML data model in the report](2026-09-18-complete-data-model-design.md).

**Goal:** a replacement, a deletion and a port of a comp model end at the element they name also where the submodel instantiates an external model definition, as long as the document it names is part of what the report was given: another entry of the same COMBINE archive, or a file next to a single SBML file which was read from a trusted directory. Where the document is not available the report says why, at the external model definition.

## What is wrong today

A comp `Submodel` instantiates a `ModelDefinition` of its document or an `ExternalModelDefinition`, which names another document by its `source`, optionally the `modelRef` of a model in it and the `md5` of the file (comp §3.3.2). The link graph resolves a reference through its `SBaseRef` chain only inside one document: `LinkGraphBuilder._submodel_index` finds no model for an external model definition, logs it, and the edge ends at the submodel.

Every comp model which ships with the backend instantiates external model definitions only, so none of their 78 references reaches an element. The sources are all bare relative file names with a `modelRef`:

| example | referencing entry | sources | available |
| --- | --- | --- | --- |
| `CompModels.omex` | `./models/omex_comp.xml` | `omex_minimal.xml` (5 definitions) | entry of the archive |
| `icg_model.omex` | `./models/icg_body.xml` | `icg_liver.xml` | entry of the archive |
| `omeprazole_model.omex` | `./models/omeprazole_body.xml` | `omeprazole_liver.xml`, `omeprazole_kidney.xml`, `omeprazole_stomach.xml` | entries of the archive |
| `minimal_model_comp.xml` | single file | `minimal_model.xml` (5 definitions) | file next to it in `resources/examples/` |
| `comp_deletion.xml` | single file | `unit_definitions.xml`, with `md5` | file next to it in `resources/examples/` |
| `icg_body.xml`, `dex_body.xml`, `spt_body.xml` | single files of `resources/models/comp/` | organ models | not shipped |

## Decisions

1. **Nothing is fetched.** A `source` with a URI scheme (`http:`, `https:`, `urn:`, ...) is never downloaded: the time of a report must not depend on a foreign server, and an uploaded model must not make the server request a url. The external model definition says that its source is remote.
2. **Files next to a single SBML file are read only from a trusted directory.** The shipped examples and the Python interface of [#33](https://github.com/matthiaskoenig/sbml4humans/issues/33) read a path the operator or the user chose, so a relative `source` is looked up next to it. An upload, a url and pasted content have no directory, they resolve nothing outside themselves. A source which leaves the trusted directory (`../`, an absolute path) is refused.
3. **A primary key stays local to its entry.** `pk = "<model id>/<type>:<id>"` is unchanged, and the route of the report page already addresses an element as `entry` plus `pk`. An edge which leaves its entry names the entry of its target.
4. **A wrong `md5` is reported and does not stop the resolution.** The document in the archive is the document the model will be run with, whatever the checksum says, so the report follows it and states the mismatch.

## The data model

`Edge` gains `target_entry: str | None` (`targetEntry`), the manifest location of the entry which holds the target, `None` for an edge inside one entry, which is every edge of today. The invariant of the link graph becomes: the target of an edge is a node of the graph of `targetEntry`, or of the own graph where it is not set.

`ExternalModelDefinition` gains `resolution: ExternalModelResolution`:

| field | type | meaning |
| --- | --- | --- |
| `status` | `ResolutionStatus` | see below |
| `entry` | `str \| None` | manifest location of the entry the source names, set as soon as the entry exists |
| `model` | `str \| None` | pk of the model in that entry, set for `resolved` |
| `md5_matches` | `bool \| None` | `None` without `md5` or without an entry to compare with |

`ResolutionStatus` (a `StrEnum`, camelCase values as `EdgeKind`):

| status | when |
| --- | --- |
| `resolved` | the entry and the model are found; a chain of external model definitions is followed to the model at its end |
| `remoteSource` | the source has a URI scheme, it is never fetched |
| `notFound` | no entry at the location the source names, which is the case of every external source of an upload of a single file |
| `notSbml` | an entry is there, but it has no report: not an SBML entry, or without a readable model |
| `modelNotFound` | the document has no model with the id `modelRef`, or no model at all where `modelRef` is not set |
| `circular` | the `modelRef` names an external model definition of the other document and the chain comes back to where it started |

`modelRef` follows comp §3.3.2: it names a model, a model definition or an external model definition of the referenced document; without it the main model of that document is meant.

## Backend

**`external.py` (new), the resolution.** `resolve_source(location, source) -> str | None` resolves a `source` against the location of the referencing entry with `posixpath` on percent-decoded paths: relative to the directory of that entry, a leading `/` relative to the root of the archive, `None` for a source with a scheme or one which leaves the root. Locations are compared normalised (`./models/a.xml` and `models/a.xml` are one entry). `ExternalModels` holds the reports and the md5 checksums of all entries by location and resolves an external model definition to `(location, model pk)`, following chains with a guard against circles; `resolve_all()` writes the `resolution` of every external model definition of every report.

**`links.py`, the graph across entries.** The per report state of the builder which a foreign builder has to see moves into `EntryIndex` (location, report, the `ModelIndex` of every model, `model_refs`); a `ModelIndex` knows its `EntryIndex`. `_submodel_index` answers for an external model definition with the `ModelIndex` of the resolved model of the other entry, and `_resolve_into`, `_resolve_element` and `_port_target` return a `Target(entry, pk)`, so that a chain which enters another entry goes on inside it, through its ports and into its own external model definitions. An edge to a target of another entry carries `target_entry`. Two edges are new: the external model definition names the model it resolves to (`modelRef`, across entries), which is what makes the other document reachable from the definition itself.

**`sbmlinfo.py` and `report.py`, two phases.** `SBMLDocumentInfo.build_report()` builds the report without its graph; `build()` keeps its meaning for one document (a report set of one). `report.link_reports(infos, checksums)` resolves the external model definitions and builds the graph of every entry. `report_for_path(path, trusted=False)` builds the reports of all SBML entries, and with `trusted=True` for a single file it then adds every file which an external model definition names next to it, and which exists inside the directory of the file, as a further entry of the wrapping archive (format SBML, not master), transitively, before linking. The master entry of a trusted single file is named after the file (`./minimal_model_comp.xml`) instead of `./model.xml`, so that the entries of such a report read as the files they are; uploads keep `./model.xml`. The examples are read trusted, the upload, url and content endpoints are not.

## Frontend

- `ReportIndex` stays one per entry and learns its `location`. The report store builds all indexes and then hands every edge with a `targetEntry` to the index of that entry as an incoming edge with its `sourceEntry`, so that the element in `omex_minimal.xml` lists the replacement in `omex_comp.xml` which names it.
- The links of the inspector and the cells which render a reference resolve the node of such an edge in the index of the other entry, and show the file name of the entry next to the element. A click navigates to `entry`, `model` and `pk` of the target.
- The inspector of an `ExternalModelDefinition` shows the resolution: the status as a sentence, the entry and the model as a link, and the result of the md5 check. The status text is an entry of the glossary (`report.toml`), as every explanation is.
- The schema, the generated types, the glossary outputs and the fixtures are regenerated; a screenshot which becomes wrong is retaken.

## Tests and the measure

- `tests/test_external.py`: `resolve_source` (relative, nested directories, root, scheme, escape, percent encoding), every status, chains and circles, md5 match and mismatch.
- `tests/test_links.py`: the invariant of `targetEntry`; a replacement, a deletion and a port which end at an element of another entry; the incoming side.
- `tests/test_report.py`: the sibling entries of a trusted single file, none for an untrusted one, the refusal of `../`.
- The walk of the issue becomes `tests/test_examples.py::test_comp_references_reach_elements`: over all shipped examples it counts the replacements, deletions and ports and how many of them end at an element. Every reference of the three archives and of the two single files with their files next to them has to resolve; the three single files without them stay at `notFound`.
- Frontend unit tests of the index and the store (incoming edges across entries), an end to end test which follows a replaced element of `omex_comp.xml` of `CompModels` to the element of `omex_minimal.xml` and back.

## Out of scope

Fetching remote sources, resolving a relative source of a model loaded by url against that url, and flattening.
