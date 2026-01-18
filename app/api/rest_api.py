from decimal import Decimal
from flask import request
import psycopg2

from ..blueprint import main
from .api_response import json_response
from ..data.db import conn, fetch_count, fetch_row_with_cols, fetch_rows_with_cols
from ..data.jsonld import add_jsonld, add_jsonld_list
from ..data.zdenci_constants import (
    BASE_FROM,
    MAP_SELECT_COLUMNS,
    REST_PAYLOAD_FIELDS,
    REST_SEARCH_COLUMNS,
    REST_SELECT_COLUMNS,
)


def _normalize_value(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def _normalize_row(row):
    return {key: _normalize_value(value) for key, value in row.items()}


def _rows_to_dicts(rows, cols):
    if not cols:
        return []
    return [_normalize_row(dict(zip(cols, row))) for row in rows]


def _fetch_row_dict(cur):
    row, cols = fetch_row_with_cols(cur)
    if not row:
        return None
    return _normalize_row(dict(zip(cols, row)))


def _parse_payload(payload, required_fields=None):
    if not isinstance(payload, dict):
        return None, ["Invalid JSON payload."]

    errors = []
    unknown = [key for key in payload.keys() if key not in REST_PAYLOAD_FIELDS]
    if unknown:
        errors.append(f"Unknown fields: {', '.join(sorted(unknown))}.")

    normalized = {}
    for key, field_type in REST_PAYLOAD_FIELDS.items():
        if key not in payload:
            continue
        value = payload.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            normalized[key] = None
            continue

        if field_type == "text":
            if not isinstance(value, str):
                errors.append(f"{key} must be a string.")
                continue
            normalized[key] = value.strip()
        elif field_type == "int":
            try:
                normalized[key] = int(value)
            except (TypeError, ValueError):
                errors.append(f"{key} must be an integer.")
        elif field_type == "num":
            try:
                normalized[key] = float(value)
            except (TypeError, ValueError):
                errors.append(f"{key} must be a number.")

    if required_fields:
        for field in required_fields:
            if field not in normalized or normalized[field] in (None, ""):
                errors.append(f"{field} is required.")

    if errors:
        return None, errors

    return normalized, []


def _gc_exists(gc_id):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM gradska_cetvrt WHERE id = %s", (gc_id,))
    exists = cur.fetchone() is not None
    cur.close()
    return exists


def _build_rest_filters():
    clauses = []
    params = []

    search_value = request.args.get("search", "", type=str).strip().lower()
    if search_value:
        like = f"%{search_value}%"
        search_clauses = [
            f"LOWER(CAST({col} AS TEXT)) LIKE %s" for col in REST_SEARCH_COLUMNS
        ]
        clauses.append("(" + " OR ".join(search_clauses) + ")")
        params.extend([like] * len(search_clauses))

    gc_raw = request.args.get("naziv_gc_id", None, type=str)
    if gc_raw is not None and gc_raw.strip() != "":
        try:
            gc_id = int(gc_raw)
        except ValueError:
            raise ValueError("naziv_gc_id must be an integer.")
        clauses.append("z.naziv_gc_id = %s")
        params.append(gc_id)

    status_raw = request.args.get("status_odrz", None, type=str)
    if status_raw is not None and status_raw.strip() != "":
        clauses.append("LOWER(z.status_odrz) = %s")
        params.append(status_raw.strip().lower())

    active_raw = request.args.get("aktivan_da_ne", None, type=str)
    if active_raw is not None and active_raw.strip() != "":
        clauses.append("LOWER(z.aktivan_da_ne) = %s")
        params.append(active_raw.strip().lower())

    if clauses:
        return " WHERE " + " AND ".join(clauses), params

    return "", []


def _get_paging():
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    if limit is None or offset is None:
        raise ValueError("limit and offset must be integers.")
    if limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200.")
    if offset < 0:
        raise ValueError("offset must be zero or greater.")
    return limit, offset


def _get_zdenac_by_id(cur, zdenac_id):
    cur.execute(
        f"SELECT {REST_SELECT_COLUMNS} {BASE_FROM} WHERE z.id = %s",
        (zdenac_id,),
    )
    return _fetch_row_dict(cur)


@main.route("/api/v1/zdenci", methods=["GET"])
def api_v1_zdenci_list():
    try:
        limit, offset = _get_paging()
        where_clause, params = _build_rest_filters()
    except ValueError as exc:
        return json_response(400, "Invalid query parameters.", {"detail": str(exc)})

    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COUNT(*) {BASE_FROM}{where_clause}", params)
        total_count = fetch_count(cur)

        cur.execute(
            f"SELECT {REST_SELECT_COLUMNS} {BASE_FROM}{where_clause} ORDER BY z.id ASC LIMIT %s OFFSET %s",
            params + [limit, offset],
        )
        rows, cols = fetch_rows_with_cols(cur)
        data = add_jsonld_list(_rows_to_dicts(rows, cols))
    except psycopg2.Error as exc:
        conn.rollback()
        cur.close()
        return json_response(500, "Database error.", {"detail": str(exc)})

    cur.close()
    return json_response(
        200,
        "Fetched zdenac collection.",
        {"items": data, "limit": limit, "offset": offset, "total": total_count},
    )


@main.route("/api/v1/zdenci/<int:zdenac_id>", methods=["GET"])
def api_v1_zdenci_get(zdenac_id):
    cur = conn.cursor()
    try:
        data = _get_zdenac_by_id(cur, zdenac_id)
    except psycopg2.Error as exc:
        conn.rollback()
        cur.close()
        return json_response(500, "Database error.", {"detail": str(exc)})

    cur.close()
    if not data:
        return json_response(
            404,
            f"Zdenac {zdenac_id} not found.",
            {"detail": f"Zdenac {zdenac_id} does not exist."},
        )
    return json_response(200, "Fetched zdenac.", add_jsonld(data))


@main.route("/api/v1/zdenci", methods=["POST"])
def api_v1_zdenci_create():
    payload = request.get_json(silent=True)
    data, errors = _parse_payload(payload, required_fields=["lokacija"])
    if errors:
        return json_response(400, "Invalid request payload.", {"errors": errors})
    if not data:
        return json_response(400, "Request payload is empty.", {"detail": "No data provided."})
    if "id" in data:
        return json_response(
            400,
            "ID must not be provided when creating.",
            {"detail": "Remove id from the request body."},
        )

    if data.get("naziv_gc_id") is not None:
        try:
            if not _gc_exists(data["naziv_gc_id"]):
                return json_response(
                    400,
                    "Invalid naziv_gc_id.",
                    {"detail": "naziv_gc_id does not exist."},
                )
        except psycopg2.Error as exc:
            conn.rollback()
            return json_response(500, "Database error.", {"detail": str(exc)})

    columns = list(data.keys())
    values = [data[key] for key in columns]
    placeholders = ", ".join(["%s"] * len(columns))
    col_sql = ", ".join(columns)

    cur = conn.cursor()
    try:
        cur.execute(
            f"INSERT INTO zdenac ({col_sql}) VALUES ({placeholders}) RETURNING id",
            values,
        )
        new_id = fetch_count(cur)
        conn.commit()
        data = _get_zdenac_by_id(cur, new_id)
    except psycopg2.IntegrityError as exc:
        conn.rollback()
        cur.close()
        return json_response(400, "Integrity error.", {"detail": str(exc)})
    except psycopg2.Error as exc:
        conn.rollback()
        cur.close()
        return json_response(500, "Database error.", {"detail": str(exc)})

    cur.close()
    return json_response(201, "Zdenac created.", add_jsonld(data))


@main.route("/api/v1/zdenci/<int:zdenac_id>", methods=["PUT"])
def api_v1_zdenci_update(zdenac_id):
    payload = request.get_json(silent=True)
    data, errors = _parse_payload(payload)
    if errors:
        return json_response(400, "Invalid request payload.", {"errors": errors})
    if not data:
        return json_response(400, "Request payload is empty.", {"detail": "No data provided."})

    if "id" in data:
        if data["id"] != zdenac_id:
            return json_response(
                400,
                "ID in body does not match path parameter.",
                {"detail": "Use the same id as in the URL."},
            )
        data.pop("id")
        if not data:
            return json_response(
                400,
                "No updatable fields provided.",
                {"detail": "Provide at least one field to update."},
            )

    if data.get("naziv_gc_id") is not None:
        try:
            if not _gc_exists(data["naziv_gc_id"]):
                return json_response(
                    400,
                    "Invalid naziv_gc_id.",
                    {"detail": "naziv_gc_id does not exist."},
                )
        except psycopg2.Error as exc:
            conn.rollback()
            return json_response(500, "Database error.", {"detail": str(exc)})

    set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
    values = list(data.values()) + [zdenac_id]

    cur = conn.cursor()
    try:
        cur.execute(
            f"UPDATE zdenac SET {set_clause} WHERE id = %s RETURNING id",
            values,
        )
        updated = cur.fetchone()
        if not updated:
            conn.rollback()
            cur.close()
            return json_response(
                404,
                f"Zdenac {zdenac_id} not found.",
                {"detail": f"Zdenac {zdenac_id} does not exist."},
            )
        conn.commit()
        data = _get_zdenac_by_id(cur, zdenac_id)
    except psycopg2.IntegrityError as exc:
        conn.rollback()
        cur.close()
        return json_response(400, "Integrity error.", {"detail": str(exc)})
    except psycopg2.Error as exc:
        conn.rollback()
        cur.close()
        return json_response(500, "Database error.", {"detail": str(exc)})

    cur.close()
    return json_response(200, "Zdenac updated.", add_jsonld(data))


@main.route("/api/v1/zdenci/<int:zdenac_id>", methods=["DELETE"])
def api_v1_zdenci_delete(zdenac_id):
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM zdenac WHERE id = %s RETURNING id", (zdenac_id,))
        deleted = cur.fetchone()
        if not deleted:
            conn.rollback()
            cur.close()
            return json_response(
                404,
                f"Zdenac {zdenac_id} not found.",
                {"detail": f"Zdenac {zdenac_id} does not exist."},
            )
        conn.commit()
    except psycopg2.Error as exc:
        conn.rollback()
        cur.close()
        return json_response(500, "Database error.", {"detail": str(exc)})

    cur.close()
    return json_response(200, "Zdenac deleted.", {"id": zdenac_id})


@main.route("/api/v1/zdenci/statusi", methods=["GET"])
def api_v1_zdenci_statusi():
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT COALESCE(status_odrz, 'Unknown') AS status, COUNT(*) AS total
            FROM zdenac
            GROUP BY status
            ORDER BY total DESC
            """
        )
        rows, cols = fetch_rows_with_cols(cur)
        data = add_jsonld_list(_rows_to_dicts(rows, cols))
    except psycopg2.Error as exc:
        conn.rollback()
        cur.close()
        return json_response(500, "Database error.", {"detail": str(exc)})

    cur.close()
    return json_response(200, "Fetched status summary.", {"items": data})


@main.route("/api/v1/zdenci/koordinate", methods=["GET"])
def api_v1_zdenci_koordinate():
    try:
        limit, offset = _get_paging()
    except ValueError as exc:
        return json_response(400, "Invalid query parameters.", {"detail": str(exc)})

    cur = conn.cursor()
    try:
        cur.execute(
            f"""
            SELECT {MAP_SELECT_COLUMNS} {BASE_FROM}
            WHERE z.lon IS NOT NULL AND z.lat IS NOT NULL
            ORDER BY z.id ASC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        rows, cols = fetch_rows_with_cols(cur)
        data = add_jsonld_list(_rows_to_dicts(rows, cols))
    except psycopg2.Error as exc:
        conn.rollback()
        cur.close()
        return json_response(500, "Database error.", {"detail": str(exc)})

    cur.close()
    return json_response(
        200,
        "Fetched coordinate list.",
        {"items": data, "limit": limit, "offset": offset},
    )


@main.route("/api/v1/gradske-cetvrti", methods=["GET"])
def api_v1_gradske_cetvrti():
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT g.id AS id, g.naziv_gc AS naziv_gc, COUNT(z.id) AS total_zdenci
            FROM gradska_cetvrt g
            LEFT JOIN zdenac z ON z.naziv_gc_id = g.id
            GROUP BY g.id, g.naziv_gc
            ORDER BY g.naziv_gc ASC
            """
        )
        rows, cols = fetch_rows_with_cols(cur)
        data = _rows_to_dicts(rows, cols)
    except psycopg2.Error as exc:
        conn.rollback()
        cur.close()
        return json_response(500, "Database error.", {"detail": str(exc)})

    cur.close()
    return json_response(200, "Fetched city districts.", {"items": data})
