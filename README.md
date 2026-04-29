# Construct-DCAT Visual Schema Editor

A Docker-first visual editor for building construction-domain DCAT / LinkML schema extensions.

The app lets you edit classes, properties, enums, and relationships in a React Flow diagram while generating LinkML YAML from the schema state.

## What You Need

1. Docker Desktop installed.
2. Docker Desktop running.
3. This repository checked out locally.

## Start The App

1. Open a terminal in this repository.

   ```bash
   cd ConstructDCAT-with-LinkML
   ```

2. Build and start the app.

   ```bash
   docker compose up --build -d
   ```

3. Open the editor in your browser.

   ```text
   http://localhost:8000/
   ```

4. Check that the backend is healthy.

   ```text
   http://localhost:8000/health
   ```

   Expected response:

   ```json
   {"status":"ok"}
   ```

## Edit A Schema

1. Open `http://localhost:8000/`.
2. Use the canvas to inspect the schema classes.
3. Double-click a class node to edit it directly in the diagram.
4. Add, rename, or delete properties inside the class node.
5. Change a property range with the dropdown.
6. Toggle `Req` for required properties.
7. Toggle `Multi` for multivalued properties.
8. Use the inspector panel for class, enum, and relationship details.
9. Watch the LinkML YAML panel update automatically.
10. Click `Save` to write the generated YAML back to:

    ```text
    schemas/construct_dcat.yaml
    ```
11. Click `RDF` or `SHACL` to download Turtle exports from the current schema.

## Generate Schema Artifacts

After saving schema changes, regenerate derived artifacts:

1. Run the generator.

   ```bash
   docker compose run --rm generator
   ```

2. Check the generated outputs.

   ```text
   generated/jsonschema/construct_dcat.schema.json
   generated/shacl/construct_dcat.shacl.ttl
   ```

## Validate Sample Data

1. Start the app with Docker.
2. Send the sample dataset to the validation endpoint.

   ```bash
   curl -X POST http://localhost:8000/validate \
     -H "Content-Type: application/json" \
     --data-binary @examples/dataset_minimal.json
   ```

3. Expected response:

   ```json
   {"valid":true,"errors":[]}
   ```

## Useful URLs

1. Editor: `http://localhost:8000/`
2. API docs: `http://localhost:8000/docs`
3. Health check: `http://localhost:8000/health`
4. JSON Schema: `http://localhost:8000/schema`
5. Schema model API: `http://localhost:8000/api/schema/model`
6. RDF export: `http://localhost:8000/schema/export/rdf`
7. SHACL export: `http://localhost:8000/schema/export/shacl`

## Developer Frontend Workflow

Use this only if you want to work on the React UI outside the Docker production build.

1. Start the FastAPI app on port 8000.

   ```bash
   docker compose up -d app
   ```

2. Open a second terminal.

3. Install frontend dependencies.

   ```bash
   cd frontend
   npm install
   ```

4. Start Vite.

   ```bash
   npm run dev
   ```

5. Open the Vite dev server.

   ```text
   http://localhost:5173/
   ```

Vite proxies API requests to the FastAPI backend on port 8000.

## Stop The App

1. Stop the running containers.

   ```bash
   docker compose down
   ```

## Project Structure

```text
ConstructDCAT-with-LinkML/
  backend/          FastAPI application and API endpoints
  frontend/         React + TypeScript visual schema editor
  schemas/          LinkML source schemas
  scripts/          Artifact generation scripts
  examples/         Example dataset payloads
  generated/        Generated JSON Schema and SHACL files
  docker-compose.yml
```

## Stack

1. FastAPI backend.
2. LinkML schema files.
3. React + TypeScript frontend.
4. React Flow diagram editor.
5. Zustand schema state.
6. Monaco YAML preview.
7. Docker Compose local runtime.

## Notes

1. The schema state is the source of truth.
2. React Flow is the visual editor, not the data model.
3. LinkML YAML is generated from schema state.
4. UI layout data should stay separate from LinkML schema data.
5. This is a local development scaffold, not a production deployment.
