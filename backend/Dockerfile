FROM node:22-slim AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json /frontend/
RUN npm ci

COPY frontend /frontend
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/app /app/app
COPY scripts /app/scripts
COPY schemas /app/schemas
COPY profiles /app/profiles
COPY examples /app/examples
COPY --from=frontend-build /frontend/dist /app/frontend-dist
RUN chmod +x /app/scripts/generate.sh && mkdir -p /app/generated/jsonschema /app/generated/shacl

EXPOSE 8000
