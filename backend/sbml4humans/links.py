"""The link graph of a report (built in Task 6)."""

from sbml4humans.model import LinkGraph, Report


def build_link_graph(report: Report, symbols: dict[str, set[str]]) -> LinkGraph:
    """The nodes and edges of the report."""
    return LinkGraph()
