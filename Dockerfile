# -------------------------------------------------------------------------------------
# Container which serves the sbml4humans FastAPI backend
#   sudo docker build -t sbml4humans-backend .
#   sudo docker run -p 1444:1444 sbml4humans-backend
# -------------------------------------------------------------------------------------
FROM python:3.14-slim

WORKDIR /code

# the report itself (`sbmlutils.report.sbmlinfo`) and the example models come
# from sbmlutils, the api only serves them over http
COPY ./backend/requirements.txt /code/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/backend/requirements.txt

COPY ./backend /code/backend
WORKDIR /code/backend

EXPOSE 1444
CMD ["uvicorn", "api:api", "--host", "0.0.0.0", "--port", "1444"]
