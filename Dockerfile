# -------------------------------------------------------------------------------------
# Container which serves the sbml4humans FastAPI backend
#   sudo docker build -t sbml4humans-backend .
#   sudo docker run -p 1444:1444 sbml4humans-backend
# -------------------------------------------------------------------------------------
FROM python:3.14-slim

WORKDIR /code

# libsbml links against libexpat, which the slim image does not ship
RUN apt-get update \
    && apt-get install -y --no-install-recommends libexpat1 \
    && rm -rf /var/lib/apt/lists/*

# the package is installed editable, docker compose mounts the repository over
# /code so that the container serves the working tree
COPY ./backend /code/backend
RUN pip install --no-cache-dir --upgrade -e /code/backend

EXPOSE 1444
CMD ["uvicorn", "sbml4humans.api:api", "--host", "0.0.0.0", "--port", "1444"]
