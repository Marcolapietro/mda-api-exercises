# OpenAPI End‑to‑End: Spec Authoring → Design Patterns → Contract‑First

## Overview

1) Author a clean spec for a Notes API (paths, schemas, examples)
2) Apply solid design patterns (pagination, filtering, error envelopes)
3) Use the spec as the contract to generate a server stub and client SDK

Work in `openapi.yaml` (with TODOs) and validate in Swagger tools. A complete reference is in `solution/openapi.yaml`.

## What You’ll Build
- Endpoints:
  - `GET /notes` — paginated list, optional `q` filter
  - `POST /notes` — create a note
  - `GET /notes/{id}` — fetch a note by id
- Reusable artifacts:
  - Schemas: `Note`, `NoteCreate`, `Error`, `ValidationError`, `Pagination`, `Links`, `NoteListResponse`
  - Parameters: `page`, `per_page`, `q`

## Files
- `openapi.yaml` — starter with TODO blanks
- `solution/openapi.yaml` — complete reference

## Part 1 — Spec Authoring (Basics)
- Fill `info` and `servers`
- Add `tags` for grouping
- Define `Note`, `NoteCreate`, `Error`
- Implement `POST /notes` and `GET /notes/{id}` with examples and proper codes

## Part 2 — Design Patterns (DX)
- Add shared query parameters: `page`, `per_page`, `q`
- Define `Pagination`, `Links`, `NoteListResponse`
- Make `GET /notes` return envelope: `{ data, pagination, links }`
- Standardize error responses across 4xx/5xx with `$ref`

## Part 3 — Contract‑First (Optional but recommended)
Use OpenAPI Generator (or similar) locally to generate:
- A Flask/FastAPI server stub
- A Python (or TypeScript) client SDK

Steps (example):
```
# Install (one option)
npx @openapitools/openapi-generator-cli@latest version-manager set 7.8.0

# Generate Flask server stub
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python-flask \
  -o generated-server

# Generate Python client
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python \
  -o generated-client
```
Then implement `GET /notes` in the server stub and call it with the generated client.

## Acceptance Criteria
- Spec validates in Swagger tools
- `$ref` reuse for schemas, parameters, and common responses
- `GET /notes` responds with `{ data, pagination, links }`
- Error schemas used across 4xx/5xx

## Validate With Swagger Editor

Use the online Swagger Editor to preview and validate your spec quickly:

- Open https://editor.swagger.io/
- Click File > Import File and select your `openapi.yaml`
- Fix any errors shown in the left panel until the UI renders as expected
- Tip: You can drag‑and‑drop the file into the editor as well
- To revalidate after edits, paste the updated YAML back into the editor

If you prefer VS Code, install an OpenAPI extension (e.g., “OpenAPI (Swagger) Editor”) and open `openapi.yaml` to see validation hints inline.
