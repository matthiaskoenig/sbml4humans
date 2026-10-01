"""The limits of what the content of a request may make the server do.

The content of a request is a model of somebody else: the body of an upload or
of pasted content, the download behind a url. It is read up to
`MAX_CONTENT_SIZE`, which is the `client_max_body_size` of the nginx in front of
sbml4humans.de, and it unpacks to at most as much: a gzipped model is
decompressed up to the limit, and a COMBINE archive is refused before it is
extracted when it holds more than `MAX_ARCHIVE_ENTRIES` entries, more than
`MAX_CONTENT_SIZE` uncompressed or an entry which is compressed more than
`MAX_COMPRESSION_RATIO` times (a zip bomb). A download ends after
`DOWNLOAD_TIMEOUT` and follows at most `MAX_REDIRECTS` redirects.

The modules read the limits from this module when they apply them, so that a
test can lower them.
"""

# the most bytes of the content of a request, before and after decompression
MAX_CONTENT_SIZE = 100 * 1024 * 1024  # [byte]
# the most entries of a COMBINE archive
MAX_ARCHIVE_ENTRIES = 1000
# the most an entry of a COMBINE archive may be compressed, a model compresses
# by a factor of 10 to 30
MAX_COMPRESSION_RATIO = 200
# the size below which an entry is never refused for its compression ratio
COMPRESSION_RATIO_MIN_SIZE = 1024 * 1024  # [byte]

# the time a download may take in total, from the first request to the last byte
DOWNLOAD_TIMEOUT = 60.0  # [s]
# the time a single step of a download may take (connect, read, write)
DOWNLOAD_STEP_TIMEOUT = 15.0  # [s]
# the most redirects a download follows
MAX_REDIRECTS = 5


class ContentTooLargeError(ValueError):
    """Raised for content beyond the limits of this module."""


def format_size(size: int) -> str:
    """A size in bytes as the user reads it, in MB from one MB on."""
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):g} MB"
    return f"{size} bytes"
