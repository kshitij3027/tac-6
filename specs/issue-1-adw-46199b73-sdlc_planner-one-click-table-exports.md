# Feature: One Click Table & Query Result Exports

## Metadata
issue_number: `1`
adw_id: `46199b73`
issue_json: `{"number":1,"title":"One Click Table Exports","body":"Using adw_plan_build_review add one click table exports and one click result export feature to get results as csv files.\n\nCreate two new endpoints to support these features. One exporting tables, one for exporting query results.\n\nPlace a download button directly to the left of the 'x' icon for available tables.\nPlace a download button directly to the left of the 'hide' button for query results.\n\nUse the appropriate download icon."}`

## Feature Description
Add a "one click export" capability to the Natural Language SQL Interface so users can download data as CSV files with a single click. There are two distinct export targets:

1. **Table export** — Each table listed in the "Available Tables" section gets a download button (placed directly to the left of the existing `×` remove icon). Clicking it downloads the entire contents of that table as a `.csv` file.
2. **Query result export** — The "Query Results" section gets a download button (placed directly to the left of the existing "Hide"/"Show" toggle button). Clicking it downloads the currently displayed query result set as a `.csv` file.

Both buttons use an appropriate download icon (a downward arrow into a tray, rendered as inline SVG to match the icon-based styling of the existing `×` button). This delivers immediate value: users can pull their uploaded data and AI-generated query results into spreadsheets and other tools without copy/paste or manual SQL.

## User Story
As a data analyst using the Natural Language SQL Interface
I want to download tables and query results as CSV files with one click
So that I can use the data in spreadsheets and other tools without manually copying or re-querying it

## Problem Statement
Currently the application can display tables and query results in the browser, but there is no way to get that data back out. Users who want to work with their data elsewhere (Excel, Google Sheets, pandas, etc.) have no export path — they would have to manually copy values from the rendered HTML table, which is error-prone and impractical for large result sets.

## Solution Statement
Add two new backend endpoints that stream CSV files using Python's standard `csv` module, reusing the existing SQL security utilities (`validate_identifier`, `check_table_exists`, `execute_query_safely`, `execute_sql_safely`) so no new injection surface is introduced:

1. `GET /api/export/table/{table_name}` — validates the table identifier, confirms the table exists, runs `SELECT * FROM {table}`, and returns the rows as a CSV download.
2. `POST /api/export/query` — accepts the previously generated SQL string, re-executes it through the existing `execute_sql_safely` path (which validates against dangerous operations), and returns the rows as a CSV download.

On the frontend, add a download icon button to each table row (left of the `×` button) and to the results header (left of the toggle button). Both trigger a browser file download via a small fetch-to-blob helper that respects the server-provided `Content-Disposition` filename.

Re-executing the SQL for the query export (rather than re-serializing the in-memory result array) keeps the request payload tiny and reuses the existing, already-tested security validation layer.

## Relevant Files
Use these files to implement the feature:

- `README.md` — Project overview, commands, API endpoint list, and security guidance. Must be read first; the new endpoints should be added to the "API Endpoints" section.
- `app/server/server.py` — FastAPI app and all HTTP endpoints. The two new export endpoints are added here, following the existing endpoint patterns (logging, try/except, security validation as in `delete_table`).
- `app/server/core/data_models.py` — Pydantic request/response models. Add a `QueryExportRequest` model for the query export endpoint body.
- `app/server/core/sql_processor.py` — `execute_sql_safely` and `get_database_schema`. Reused for executing the query-export SQL.
- `app/server/core/sql_security.py` — Security helpers (`validate_identifier`, `check_table_exists`, `execute_query_safely`, `SQLSecurityError`). Reused for the table-export endpoint. No changes expected.
- `app/client/index.html` — Static markup for the results header (`results-header` with `toggle-results` button) and tables section. The export buttons are created dynamically in `main.ts`, but the results header structure is referenced here.
- `app/client/src/api/client.ts` — Typed API client. Add `exportTable(tableName)` and `exportQueryResults(sql)` methods plus a blob-download helper.
- `app/client/src/main.ts` — UI logic. `displayTables()` builds each table row (add the download button before `removeButton`); `displayResults()` builds the results header toggle (add the download button before the toggle button). Keep a reference to the last query response so the results export knows which SQL to send.
- `app/client/src/style.css` — Styling. Add `.download-table-button` / `.download-results-button` (or a shared `.icon-button` / `.download-button`) styles consistent with `.remove-table-button` and `.toggle-button`.
- `app/server/tests/core/test_sql_processor.py` — Existing server test patterns for SQL execution; model new export-related server tests on these.
- `.claude/commands/test_e2e.md` — Read to understand how the E2E test runner consumes a test file and what output format is expected.
- `.claude/commands/e2e/test_basic_query.md` — Read as the canonical example for authoring the new E2E test file (structure: User Story, Test Steps, Success Criteria).
- `.claude/commands/conditional_docs.md` — Confirms that operating under `app/server` and `app/client` requires reading `README.md` (already covered) and `app/client/src/style.css` (covered when editing styles).

### New Files
- `.claude/commands/e2e/test_table_exports.md` — New E2E test file validating that the table download button and the query-results download button appear in the correct positions and trigger CSV downloads. Modeled on `.claude/commands/e2e/test_basic_query.md`.

## Implementation Plan
### Phase 1: Foundation
Establish the backend CSV export capability. Add a shared CSV-building helper (using `csv` + `io.StringIO`) and the request model for the query export. This phase is purely additive and introduces no new dependencies (Python's `csv` and `io` are in the standard library).

### Phase 2: Core Implementation
Implement the two FastAPI endpoints (`GET /api/export/table/{table_name}` and `POST /api/export/query`) returning CSV via `fastapi.responses.Response`/`StreamingResponse` with a `Content-Disposition: attachment` header. Reuse existing security helpers for identifier validation and safe execution. Add server unit tests.

### Phase 3: Integration
Wire the frontend: add API client methods and a blob-download helper, render the download buttons in the exact required positions, style them with the download icon, and track the last query's SQL so the results export works. Add the E2E test and run the full validation suite.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Read project documentation and conventions
- Read `README.md` (project overview, commands, API endpoints, security guidance).
- Read `.claude/commands/conditional_docs.md` and confirm `README.md` and `app/client/src/style.css` apply (they do — we touch `app/server`, `app/client`, and styles).
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_basic_query.md` to understand how to author the new E2E test file.

### 2. Add the query export request model
- In `app/server/core/data_models.py`, add a Pydantic model:
  - `class QueryExportRequest(BaseModel)` with field `sql: str = Field(..., description="The SQL query to execute and export as CSV")`.
- Keep it simple and consistent with existing models (no decorators, plain Pydantic).

### 3. Add a CSV serialization helper on the server
- In `app/server/server.py` (or a small helper near the new endpoints), add a function that converts a list of row dicts + ordered column list into a CSV string using `csv.DictWriter` and `io.StringIO`.
  - Signature suggestion: `def rows_to_csv(columns: list[str], rows: list[dict]) -> str`.
  - Write the header row from `columns`, then each row. Handle `None` values gracefully (empty string).
- Import `csv` and `io` at the top of `server.py`, and `Response` / `StreamingResponse` from `fastapi.responses`.

### 4. Implement the table export endpoint
- In `app/server/server.py`, add `GET /api/export/table/{table_name}`:
  - Validate the identifier with `validate_identifier(table_name, "table")`; on `SQLSecurityError` raise `HTTPException(400, ...)`.
  - Open a `sqlite3` connection to `db/database.db`, and use `check_table_exists`; if not found raise `HTTPException(404, ...)`.
  - Use `execute_query_safely(conn, "SELECT * FROM {table}", identifier_params={'table': table_name})` with `conn.row_factory = sqlite3.Row` to fetch all rows; derive columns from the cursor description or first row keys.
  - Build the CSV via the helper and return a `Response` (or `StreamingResponse`) with `media_type="text/csv"` and header `Content-Disposition: attachment; filename="{table_name}.csv"`.
  - Wrap in try/except with the same `logger.info`/`logger.error` + `traceback` pattern used by other endpoints. Close the connection in all paths.

### 5. Implement the query result export endpoint
- In `app/server/server.py`, add `POST /api/export/query` accepting `QueryExportRequest`:
  - Re-execute the supplied SQL via `execute_sql_safely(request.sql)` (this validates against dangerous operations and returns `results`, `columns`, `error`).
  - If `result['error']` is set, raise `HTTPException(400, result['error'])`.
  - Build the CSV via the helper from `result['columns']` and `result['results']` and return a `Response`/`StreamingResponse` with `media_type="text/csv"` and header `Content-Disposition: attachment; filename="query_results.csv"`.
  - Use the same logging/try-except pattern as the other endpoints.

### 6. Add server unit tests for exports
- Create or extend a test module (e.g. `app/server/tests/core/test_export.py` or extend `test_sql_processor.py`) covering the CSV helper and the endpoints via FastAPI `TestClient`:
  - `rows_to_csv` produces a correct header + rows, handles empty result sets and `None` values.
  - `GET /api/export/table/{table_name}` returns `200`, `text/csv`, an `attachment` `Content-Disposition`, and CSV content matching seeded data; returns `404` for a missing table and `400` for an invalid identifier.
  - `POST /api/export/query` returns CSV for a valid `SELECT`, and an error status for SQL that fails validation/execution.
- Follow existing test setup conventions (seed a temp table in `db/database.db`, then clean up), mirroring `app/server/tests/core/test_sql_processor.py`.

### 7. Update the README API documentation
- In `README.md`, add the two new endpoints under the "API Endpoints" section:
  - `GET /api/export/table/{table_name}` - Export a table as CSV
  - `POST /api/export/query` - Export query results as CSV

### 8. Add TypeScript types and API client methods
- In `app/client/src/types.d.ts`, add `interface QueryExportRequest { sql: string; }`.
- In `app/client/src/api/client.ts`:
  - Add a private helper that performs a fetch, reads the response as a `Blob`, extracts the filename from the `Content-Disposition` header (fallback to a sensible default), and triggers a browser download via a temporary `<a>` element + `URL.createObjectURL` (revoking the object URL afterward). Reuse `API_BASE_URL`.
  - Add `async exportTable(tableName: string): Promise<void>` → `GET /export/table/{encodeURIComponent(tableName)}`.
  - Add `async exportQueryResults(sql: string): Promise<void>` → `POST /export/query` with JSON body `{ sql }`.
  - Note: these download endpoints return CSV, not JSON, so they must NOT go through the JSON-parsing `apiRequest`; use the new blob helper.

### 9. Add the download button to each table row
- In `app/client/src/main.ts` `displayTables()`:
  - Create a `downloadButton` (`button`) with class `download-table-button`, `title="Download table as CSV"`, and the download icon as inline SVG (`innerHTML`).
  - Wire `downloadButton.onclick = () => exportTable(table.name)` (add an `exportTable` wrapper that calls `api.exportTable` and surfaces errors via `displayError`).
  - Insert it into `tableHeader` directly before `removeButton` so the order left→right is: download button, then `×` button. (Wrap `downloadButton` + `removeButton` in a `table-actions` flex container if needed to preserve the `space-between` layout.)

### 10. Add the download button to the query results header
- In `app/client/src/main.ts` `displayResults()`:
  - Store the current response's SQL in a module-scoped variable (e.g. `lastQuerySql`) when results are displayed, so the export knows what to re-run.
  - Create a `downloadButton` (`button`) with class `download-results-button`, `title="Download results as CSV"`, and the same download icon SVG.
  - Wire its click to call `api.exportQueryResults(lastQuerySql)` (with error handling via `displayError`).
  - Insert it into the `results-header` directly before the `toggle-results` button so the order left→right is: download button, then "Hide"/"Show" button. (Wrap the two in a `results-actions` flex container if needed.)
  - Only show/enable the results download button when there are results (no error and `row_count > 0`).

### 11. Style the download buttons with the download icon
- In `app/client/src/style.css`, add styles for `.download-table-button` and `.download-results-button` (or a shared `.download-button`/`.icon-button`) consistent with `.remove-table-button` (icon-sized, transparent background, hover highlight) and aligned with the toggle/remove buttons.
- Ensure the inline SVG icon inherits color via `currentColor` and is sized appropriately (e.g. `width/height: 1rem`).
- If wrapper containers (`table-actions`, `results-actions`) are introduced, add `display: flex; align-items: center; gap` styles so the download button sits immediately to the left of the `×` / toggle button.

### 12. Create the E2E test file
- Create `.claude/commands/e2e/test_table_exports.md` modeled on `.claude/commands/e2e/test_basic_query.md`, with the minimal steps to validate the feature:
  - Navigate to the `Application URL` and screenshot the initial state.
  - Load sample data (e.g. click the "Users Data" sample button) and **Verify** a table appears in "Available Tables".
  - **Verify** a download button is present directly to the left of the `×` button on the table row; screenshot it.
  - Click the table download button and **Verify** a CSV file download is initiated (capture the Playwright download event / filename ends in `.csv`).
  - Enter and run a query (e.g. "Show me all users"), **Verify** results appear.
  - **Verify** a download button is present directly to the left of the "Hide" button in the results header; screenshot it.
  - Click the results download button and **Verify** a CSV file download is initiated.
  - Include a Success Criteria section and the JSON `Output Format` (status/screenshots/error) consistent with the example test.

### 13. Run the validation suite
- Run every command in the `Validation Commands` section below and ensure each passes with zero errors and zero regressions. Fix any failures before considering the feature complete.

## Testing Strategy
### Unit Tests
- **CSV helper (`rows_to_csv`)**: correct header and row ordering; empty result set yields header-only (or empty) output; `None` values render as empty strings; values containing commas/quotes/newlines are properly quoted (verified via the standard `csv` module behavior).
- **`GET /api/export/table/{table_name}`** (FastAPI `TestClient`): returns `200`, `Content-Type: text/csv`, `Content-Disposition: attachment; filename="<table>.csv"`, and body matching seeded rows; `404` for non-existent table; `400` for an invalid/injection identifier.
- **`POST /api/export/query`** (FastAPI `TestClient`): returns CSV for a valid `SELECT`; returns an error status for SQL that fails `validate_sql_query` (e.g. `DROP TABLE`); returns header-only CSV for a query with zero rows.
- **Frontend type check & build**: `bun tsc --noEmit` and `bun run build` confirm the new client code compiles.

### Edge Cases
- Empty table / query with zero rows — export should still produce a valid CSV (header row only) and not error.
- Table or column names containing spaces (allowed by `validate_identifier`) — header and `Content-Disposition` handled correctly.
- Invalid / injection-style table name in the export URL — rejected with `400`, no SQL executed.
- Query export attempted with SQL containing dangerous operations — rejected by `execute_sql_safely`/`validate_sql_query`.
- Special characters in cell values (commas, quotes, newlines) — correctly escaped by the `csv` module.
- Clicking the results download before any query has run — button is absent/disabled (results section hidden until a query runs).
- `Content-Disposition` filename parsing failure on the client — falls back to a default filename (`<table>.csv` / `query_results.csv`).

## Acceptance Criteria
- A `GET /api/export/table/{table_name}` endpoint exists and returns the full table as a downloadable CSV with an `attachment` `Content-Disposition` header.
- A `POST /api/export/query` endpoint exists and returns the current query's results as a downloadable CSV.
- Both endpoints reuse the existing SQL security layer; invalid identifiers and dangerous SQL are rejected.
- In "Available Tables", every table row shows a download icon button positioned directly to the left of the `×` remove button; clicking it downloads that table as `<table_name>.csv`.
- In "Query Results", a download icon button appears directly to the left of the "Hide"/"Show" toggle button; clicking it downloads the displayed results as `query_results.csv`.
- The download buttons use an appropriate download icon (inline SVG download glyph) and are visually consistent with existing buttons.
- All server tests pass (`uv run pytest`), the client type-checks (`bun tsc --noEmit`), and the client builds (`bun run build`).
- The new E2E test (`.claude/commands/e2e/test_table_exports.md`) passes, demonstrating both download buttons in the correct positions and triggering CSV downloads.

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd app/server && uv run pytest` - Run all server tests (including new export tests) to validate the feature works with zero regressions.
- `cd app/server && uv run pytest tests/test_sql_injection.py -v` - Confirm SQL injection protections still pass after adding export endpoints.
- `cd app/client && bun tsc --noEmit` - Type-check the frontend to validate the new client code compiles with zero errors.
- `cd app/client && bun run build` - Build the frontend to validate the feature builds with zero regressions.
- `Read .claude/commands/test_e2e.md`, then read and execute the new E2E test file `.claude/commands/e2e/test_table_exports.md` to validate this functionality works end-to-end (both download buttons present in the correct positions and triggering CSV downloads).

## Notes
- **No new dependencies required**: CSV generation uses Python's standard-library `csv` and `io` modules, and `fastapi.responses.Response`/`StreamingResponse` are already available via FastAPI. No `uv add` is needed.
- **Why re-execute SQL for the query export** instead of POSTing the already-rendered result array: it keeps the request payload minimal and reuses the existing, tested `execute_sql_safely` security validation, avoiding a second code path that serializes arbitrary client-supplied data. The trade-off is a re-query; acceptable for this app's scale.
- **Security**: both endpoints route through the existing `validate_identifier` / `execute_query_safely` / `validate_sql_query` helpers, so they inherit the project's SQL-injection protections (per the README "Security Best Practices for Development").
- **Download icon**: use an inline SVG download glyph (downward arrow into a tray) with `currentColor` so it adopts the surrounding text color and hover styles, matching the icon-button styling of the existing `×` button.
- **Future considerations**: could add export-format options (e.g. JSON/Excel), a "download all tables" action, and respect very large tables via true streaming (`StreamingResponse` with a generator) if data sizes grow.
