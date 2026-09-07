# -------------------------------------------------------------------------------------
# Container which serves the sbml4humans FastAPI backend
#   sudo docker build -t sbml4humans-backend .
#   sudo docker run -p 1444:1444 sbml4humans-backend
# -------------------------------------------------------------------------------------
FROM python:3.14-slim

WORKDIR /code

# git for the sbmlutils checkout
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# the report itself (`sbmlutils.report.sbmlinfo`) and the example models come
# from the latest develop branch of sbmlutils, the api only serves them over http.
# The checkout is installed editable, so that the curated biomodels served as
# examples are available (they are excluded from the sbmlutils wheel).
ARG SBMLUTILS_BRANCH=develop
# the current commit of the branch busts the build cache whenever develop moves,
# so that rebuilds pick up the latest version
ADD https://api.github.com/repos/matthiaskoenig/sbmlutils/git/refs/heads/${SBMLUTILS_BRANCH} /code/sbmlutils-ref.json
RUN git clone --depth 1 --branch ${SBMLUTILS_BRANCH} https://github.com/matthiaskoenig/sbmlutils.git /code/sbmlutils \
    && pip install --no-cache-dir --upgrade -e /code/sbmlutils

COPY ./backend /code/backend
RUN pip install --no-cache-dir --upgrade -e /code/backend

EXPOSE 1444
CMD ["uvicorn", "sbml4humans.api:api", "--host", "0.0.0.0", "--port", "1444"]
