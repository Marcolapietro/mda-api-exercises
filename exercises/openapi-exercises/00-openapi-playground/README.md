# OpenAPI Playground (Explore‑First)

Goal: get comfortable with Swagger Editor by tweaking a tiny spec and seeing instant changes — no heavy design required.

Quick Start
- Open https://editor.swagger.io/
- File > Import File > select `openapi-exercises/00-openapi-playground/openapi.yaml`
- Play! Make small changes and watch the UI update.

Try These (5–10 minutes)
- Change the API title and version in `info`
- Add a new tag name and assign it to the existing path
- Edit the response example for `GET /ping` and re‑run “Try it out”
- Add a `description` to the `200` response
- Add a simple `400` response using the provided `Error` schema

Next 10–15 minutes (optional)
- Add a new path `GET /hello` that returns `{ message: "Hello <name>" }`
  - Add a query parameter `name` (default `world`)
  - Include an example request/response
- Add a `POST /echo` that echoes `{ input: string }` and returns `{ output: string }`

Nice‑to‑Know
- The left panel validates YAML; fix red errors, reload if stuck
- You can paste YAML directly; the UI updates immediately
- Right‑click on properties to jump to `$ref` sources

Done? Head to `01-openapi-end-to-end` for a deeper, design‑focused exercise.

