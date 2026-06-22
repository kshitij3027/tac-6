"""
Tests for CSV export functionality: the rows_to_csv helper and the
/api/export/table/{table_name} and /api/export/query endpoints.
"""

import csv
import io
import sqlite3

import pytest
from fastapi.testclient import TestClient

from server import app, rows_to_csv

client = TestClient(app)

EXPORT_TABLE = "export_test_table"


@pytest.fixture
def seeded_table():
    """Seed a known table into db/database.db and clean it up afterwards."""
    conn = sqlite3.connect("db/database.db")
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {EXPORT_TABLE}")
    cursor.execute(f'''
        CREATE TABLE {EXPORT_TABLE} (
            id INTEGER PRIMARY KEY,
            name TEXT,
            note TEXT
        )
    ''')
    cursor.execute(
        f"INSERT INTO {EXPORT_TABLE} (id, name, note) VALUES (?, ?, ?)",
        (1, "Alice", "hello, world"),
    )
    cursor.execute(
        f"INSERT INTO {EXPORT_TABLE} (id, name, note) VALUES (?, ?, ?)",
        (2, "Bob", None),
    )
    conn.commit()
    conn.close()

    yield EXPORT_TABLE

    conn = sqlite3.connect("db/database.db")
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {EXPORT_TABLE}")
    conn.commit()
    conn.close()


class TestRowsToCsv:

    def test_header_and_rows(self):
        columns = ["id", "name"]
        rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        result = rows_to_csv(columns, rows)

        parsed = list(csv.reader(io.StringIO(result)))
        assert parsed[0] == ["id", "name"]
        assert parsed[1] == ["1", "Alice"]
        assert parsed[2] == ["2", "Bob"]

    def test_empty_rows_yields_header_only(self):
        result = rows_to_csv(["id", "name"], [])
        parsed = list(csv.reader(io.StringIO(result)))
        assert parsed == [["id", "name"]]

    def test_none_values_render_as_empty_string(self):
        result = rows_to_csv(["id", "note"], [{"id": 1, "note": None}])
        parsed = list(csv.reader(io.StringIO(result)))
        assert parsed[1] == ["1", ""]

    def test_special_characters_are_quoted(self):
        result = rows_to_csv(
            ["id", "note"],
            [{"id": 1, "note": 'a, b "c"\nd'}],
        )
        # Round-trips correctly through the csv parser
        parsed = list(csv.reader(io.StringIO(result)))
        assert parsed[1] == ["1", 'a, b "c"\nd']


class TestExportTableEndpoint:

    def test_export_table_success(self, seeded_table):
        response = client.get(f"/api/export/table/{seeded_table}")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert (
            response.headers["content-disposition"]
            == f'attachment; filename="{seeded_table}.csv"'
        )

        parsed = list(csv.reader(io.StringIO(response.text)))
        assert parsed[0] == ["id", "name", "note"]
        assert parsed[1] == ["1", "Alice", "hello, world"]
        assert parsed[2] == ["2", "Bob", ""]

    def test_export_missing_table_returns_404(self):
        response = client.get("/api/export/table/no_such_table_xyz")
        assert response.status_code == 404

    def test_export_invalid_identifier_returns_400(self):
        # Identifier with invalid characters / injection attempt
        response = client.get("/api/export/table/users;DROP")
        assert response.status_code == 400


class TestExportQueryEndpoint:

    def test_export_query_success(self, seeded_table):
        response = client.post(
            "/api/export/query",
            json={"sql": f"SELECT id, name FROM {seeded_table} ORDER BY id"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert (
            response.headers["content-disposition"]
            == 'attachment; filename="query_results.csv"'
        )

        parsed = list(csv.reader(io.StringIO(response.text)))
        assert parsed[0] == ["id", "name"]
        assert parsed[1] == ["1", "Alice"]
        assert parsed[2] == ["2", "Bob"]

    def test_export_query_zero_rows_yields_header_only(self, seeded_table):
        response = client.post(
            "/api/export/query",
            json={"sql": f"SELECT id, name FROM {seeded_table} WHERE id > 1000"},
        )
        assert response.status_code == 200
        # No rows means columns cannot be derived -> empty/header-only CSV
        parsed = list(csv.reader(io.StringIO(response.text)))
        assert len(parsed) <= 1

    def test_export_query_dangerous_sql_rejected(self):
        response = client.post(
            "/api/export/query",
            json={"sql": "DROP TABLE users"},
        )
        assert response.status_code == 400
