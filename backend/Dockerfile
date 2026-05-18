FROM node:22-slim AS frontend-build

WORKDIR /frontend

COPY construct-dcat-docker/frontend/package.json construct-dcat-docker/frontend/package-lock.json /frontend/
RUN npm ci

COPY construct-dcat-docker/frontend /frontend
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

COPY General-Ontology-Editor/pyproject.toml /general-ontology-editor/pyproject.toml
COPY General-Ontology-Editor/src /general-ontology-editor/src
COPY construct-dcat-docker/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt && pip install --no-cache-dir -e /general-ontology-editor

COPY construct-dcat-docker/backend/app /app/app
COPY construct-dcat-docker/scripts /app/scripts
COPY construct-dcat-docker/schemas /app/schemas
COPY construct-dcat-docker/profiles /app/profiles
COPY construct-dcat-docker/examples /app/examples
COPY --from=frontend-build /frontend/dist /app/frontend-dist
RUN chmod +x /app/scripts/generate.sh && mkdir -p /app/generated/jsonschema /app/generated/shacl

EXPOSE 8000
