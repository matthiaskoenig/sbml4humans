"""COMBINE archives with their entries in the order of the manifest.

pymetadata extracts an archive and adds its entries in the order of `os.walk`,
which is the order of the file system and differs between machines. The order
of the entries is what a report shows, so it is restored from the manifest.
"""

import logging
import zipfile
from pathlib import Path

import lxml.etree as ET  # ty: ignore[unresolved-import]
from pymetadata.omex import Omex


logger = logging.getLogger(__name__)

MANIFEST_NAME = "manifest.xml"


def manifest_locations(omex_path: Path) -> list[str]:
    """Read the locations of the entries of an archive in the order of its manifest.

    The locations are written as pymetadata writes them, with a leading `./`.
    An archive without a manifest which can be read has no order, its list is
    empty.
    """
    # the archive holds the content of a request: no entities, no network
    parser = ET.XMLParser(resolve_entities=False, no_network=True)
    try:
        with zipfile.ZipFile(omex_path) as zf:
            root = ET.fromstring(zf.read(MANIFEST_NAME), parser=parser)
    except (KeyError, zipfile.BadZipFile, ET.XMLSyntaxError) as err:
        logger.warning("No manifest could be read from '%s': %s", omex_path, err)
        return []

    locations: list[str] = []
    for element in root.iter("{*}content"):
        location: str | None = element.get("location")
        if location is None:
            continue
        locations.append(location if location.startswith(".") else f"./{location}")
    return locations


def read_omex(omex_path: Path) -> Omex:
    """Read an archive with its entries in the order of its manifest.

    A file which the manifest does not list follows the listed ones, sorted by
    its location.
    """
    omex = Omex.from_omex(omex_path)
    order = {
        location: position
        for position, location in enumerate(manifest_locations(omex_path))
    }
    omex.manifest.entries.sort(
        key=lambda entry: (order.get(entry.location, len(order)), entry.location)
    )
    return omex
