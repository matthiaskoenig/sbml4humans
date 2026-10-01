# -------------------------------------------------------------------------------------
# Container which serves the sbml4humans FastAPI backend
#   sudo docker build -t sbml4humans-backend .
#   sudo docker run -p 127.0.0.1:1444:1444 sbml4humans-backend
# -------------------------------------------------------------------------------------
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

# libsbml links against libexpat, which the slim image does not ship
RUN apt-get update \
    && apt-get install -y --no-install-recommends libexpat1 \
    && rm -rf /var/lib/apt/lists/*

# the package is installed editable: the image carries the code, which is all production needs,
# and docker-compose-develop.yml mounts the repository over /code (read-only) so that the
# container serves the working tree
COPY ./backend /code/backend
RUN pip install --no-cache-dir --upgrade -e /code/backend

# the server runs as an unprivileged user which cannot change the code. It writes only to its
# home directory (the cache of pymetadata, ~/.cache/pymetadata), the temporary directory and
# /uploads, the mount point of the volume of the uploads, which a fresh named volume takes the
# owner of
RUN useradd --create-home --uid 1000 --user-group app \
    && mkdir -p /uploads \
    && chown app:app /uploads
USER app

EXPOSE 1444
CMD ["uvicorn", "sbml4humans.api:api", "--host", "0.0.0.0", "--port", "1444"]
