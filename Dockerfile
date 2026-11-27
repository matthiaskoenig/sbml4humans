# -------------------------------------------------------------------------------------
# Container which serves the sbml4humans FastAPI backend
#   sudo docker build -t sbml4humans-backend .
#   sudo docker run -p 127.0.0.1:1444:1444 sbml4humans-backend
# -------------------------------------------------------------------------------------
# Native parsing is compiled from the same reviewed revision as the browser package.
FROM rust:1.100-slim-trixie AS native-parser
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 gcc g++ cmake libc6-dev git libexpat1-dev zlib1g-dev libbz2-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY parser-source.json /build/parser-source.json
COPY scripts/build_parser.py /build/scripts/build_parser.py
RUN python3 scripts/build_parser.py --wheel-out /wheels

FROM python:3.14-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /code

# libsbml links against libexpat, which the slim image does not ship
RUN apt-get update \
    && apt-get install -y --no-install-recommends libexpat1 zlib1g libbz2-1.0 \
    && rm -rf /var/lib/apt/lists/*

# the package is installed editable: the image carries the code, which is all production needs,
# and docker-compose-develop.yml mounts the repository over /code (read-only) so that the
# container serves the working tree
COPY ./backend /code/backend
RUN uv sync --project /code/backend --locked --no-dev --no-cache
COPY --from=native-parser /wheels /wheels
RUN uv pip install --python /opt/venv/bin/python --no-deps /wheels/*.whl \
    && rm -rf /wheels

# the server runs as an unprivileged user which cannot change the code. It writes only to its
# home directory, the temporary directory, /uploads and /cache, the mount points of the volumes
# of the uploads and of the cache of pymetadata (SBML4HUMANS_CACHE), which a fresh named volume
# takes the owner of
RUN useradd --create-home --uid 1000 --user-group app \
    && mkdir -p /uploads /cache \
    && chown app:app /uploads /cache
USER app

EXPOSE 1444
CMD ["uvicorn", "sbml4humans.api:api", "--host", "0.0.0.0", "--port", "1444"]
