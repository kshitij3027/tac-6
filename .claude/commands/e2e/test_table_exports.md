# E2E Test: One Click Table & Query Result Exports

Test the one-click CSV export functionality for tables and query results in the Natural Language SQL Interface application.

## User Story

As a data analyst
I want to download tables and query results as CSV files with one click
So that I can use the data in spreadsheets and other tools without manually copying it

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the page title is "Natural Language SQL Interface"
4. Click the "Upload Data" button to open the upload modal
5. Click the "Users Data" sample button to load sample data
6. **Verify** a table appears in the "Available Tables" section (e.g. a "users" table)
7. **Verify** a download button (download icon) is present in the table row directly to the left of the `×` remove button
8. Take a screenshot of the table row showing the download button next to the `×` button
9. Set up a download listener, click the table download button, and **Verify** a CSV file download is initiated (the downloaded filename ends in `.csv`)
10. Enter the query: "Show me all users"
11. Click the Query button
12. **Verify** the query results appear in the "Query Results" section
13. **Verify** a download button (download icon) is present in the results header directly to the left of the "Hide" button
14. Take a screenshot of the results header showing the download button next to the "Hide" button
15. Set up a download listener, click the results download button, and **Verify** a CSV file download is initiated (the downloaded filename ends in `.csv`, e.g. `query_results.csv`)

## Success Criteria
- A download button appears directly to the left of the `×` button on each table row
- Clicking the table download button initiates a `.csv` file download
- A download button appears directly to the left of the "Hide" button in the results header
- Clicking the results download button initiates a `.csv` file download
- Both download buttons use a download icon
- At least 3 screenshots are taken

## Output Format

```json
{
  "test_name": "One Click Table & Query Result Exports",
  "status": "passed|failed",
  "screenshots": [
    "<absolute path to codebase>/agents/<adw_id>/<agent_name>/img/table_exports/01_initial_state.png",
    "<absolute path to codebase>/agents/<adw_id>/<agent_name>/img/table_exports/02_table_download_button.png",
    "<absolute path to codebase>/agents/<adw_id>/<agent_name>/img/table_exports/03_results_download_button.png"
  ],
  "error": null
}
```
