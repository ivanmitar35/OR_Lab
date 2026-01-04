import csv
import io
import json

from flask import Response, jsonify, request

from .blueprint import main
from .db import conn, fetch_count, fetch_rows_with_cols
from .zdenci_constants import (
    BASE_FROM,
    COLUMN_SQL,
    CSV_COLUMNS,
    DATA_KEYS,
    JSON_COLUMNS,
    NUMERIC_KEYS,
    SEARCH_COLUMNS,
    SELECT_COLUMNS,
)


# Build WHERE clause and params for global and column filters
def _build_search_clause(search_value, column_filters):
    clauses = []
    params = []

    if search_value:
        like = f"%{search_value}%"
        global_clauses = [
            f"LOWER(CAST({col} AS TEXT)) LIKE %s" for col in SEARCH_COLUMNS
        ]
        clauses.append("(" + " OR ".join(global_clauses) + ")")
        params.extend([like] * len(global_clauses))

    for column_filter in column_filters:
        clause, clause_params = _build_column_clause(column_filter)
        if clause:
            clauses.append(clause)
            params.extend(clause_params)

    if clauses:
        return " WHERE " + " AND ".join(clauses), params

    return "", []


# Map DataTables ordering to SQL ORDER BY
def _get_order_clause(order_index, order_dir, default_clause):
    if order_index is None or order_index < 0 or order_index >= len(DATA_KEYS):
        return default_clause

    direction = "DESC" if str(order_dir).lower() == "desc" else "ASC"
    col_key = DATA_KEYS[order_index]
    col_sql = COLUMN_SQL.get(col_key)
    if not col_sql:
        return default_clause

    return f" ORDER BY {col_sql} {direction}"


# Read column-level filters from request parameters
def _get_column_filters():
    filters = []
    for idx, key in enumerate(DATA_KEYS):
        col_sql = COLUMN_SQL[key]
        value = request.args.get(f"columns[{idx}][search][value]", "").strip()
        cc_value = request.args.get(
            f"columns[{idx}][columnControl][search][value]", ""
        ).strip()
        cc_logic = request.args.get(
            f"columns[{idx}][columnControl][search][logic]", ""
        ).strip()
        cc_type = request.args.get(
            f"columns[{idx}][columnControl][search][type]", ""
        ).strip()

        if cc_logic:
            if cc_value or cc_logic in {"empty", "notEmpty"}:
                filters.append(
                    {
                        "key": key,
                        "col_sql": col_sql,
                        "logic": cc_logic,
                        "value": cc_value,
                        "type": cc_type or "text",
                    }
                )
            continue

        if value:
            filters.append(
                {
                    "key": key,
                    "col_sql": col_sql,
                    "logic": "contains",
                    "value": value,
                    "type": "text",
                }
            )
    return filters


# Convert a single column filter to SQL and params
def _build_column_clause(column_filter):
    col_sql = column_filter["col_sql"]
    logic = (column_filter.get("logic") or "contains").strip()
    value = (column_filter.get("value") or "").strip()
    filter_type = (column_filter.get("type") or "text").strip().lower()
    col_expr = f"LOWER(CAST({col_sql} AS TEXT))"

    if logic == "empty":
        return f"({col_sql} IS NULL OR TRIM(CAST({col_sql} AS TEXT)) = '')", []
    if logic == "notEmpty":
        return f"({col_sql} IS NOT NULL AND TRIM(CAST({col_sql} AS TEXT)) <> '')", []
    if not value:
        return None, []

    value = value.lower()

    if (
        filter_type == "num"
        and column_filter.get("key") in NUMERIC_KEYS
        and logic in {"equal", "notEqual", "greater", "greaterOrEqual", "less", "lessOrEqual"}
    ):
        try:
            numeric_value = float(value)
        except ValueError:
            return None, []

        op_map = {
            "equal": "=",
            "notEqual": "<>",
            "greater": ">",
            "greaterOrEqual": ">=",
            "less": "<",
            "lessOrEqual": "<=",
        }
        return f"CAST({col_sql} AS NUMERIC) {op_map[logic]} %s", [numeric_value]

    if logic == "equal":
        return f"{col_expr} = %s", [value]
    if logic == "notEqual":
        return f"{col_expr} <> %s", [value]
    if logic == "starts":
        return f"{col_expr} LIKE %s", [f"{value}%"]
    if logic == "ends":
        return f"{col_expr} LIKE %s", [f"%{value}"]
    if logic == "notContains":
        return f"{col_expr} NOT LIKE %s", [f"%{value}%"]

    return f"{col_expr} LIKE %s", [f"%{value}%"]


@main.route("/api/zdenci")
def api_zdenci():
    draw = request.args.get("draw", 0, type=int)
    start = request.args.get("start", 0, type=int)
    length = request.args.get("length", 50, type=int)
    search_value = request.args.get("search[value]", "", type=str).strip().lower()
    column_filters = _get_column_filters()

    where_clause, params = _build_search_clause(search_value, column_filters)
    order_index = request.args.get("order[0][column]", type=int)
    order_dir = request.args.get("order[0][dir]", "asc")
    default_order = f" ORDER BY {COLUMN_SQL[DATA_KEYS[0]]} ASC"
    order_clause = _get_order_clause(order_index, order_dir, default_order)

    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) {BASE_FROM}")
    total_count = fetch_count(cur)

    if where_clause:
        cur.execute(f"SELECT COUNT(*) {BASE_FROM}{where_clause}", params)
        filtered_count = fetch_count(cur)
    else:
        filtered_count = total_count

    limit_clause = ""
    limit_params = []
    if length != -1:
        limit_clause = " LIMIT %s OFFSET %s"
        limit_params = [length, start]

    cur.execute(
        f"SELECT {SELECT_COLUMNS} {BASE_FROM}{where_clause}{order_clause}{limit_clause}",
        params + limit_params,
    )
    rows, cols = fetch_rows_with_cols(cur)
    data = [dict(zip(cols, row)) for row in rows] if cols else []
    cur.close()

    return jsonify(
        {
            "draw": draw,
            "recordsTotal": total_count,
            "recordsFiltered": filtered_count,
            "data": data,
        }
    )


@main.route("/api/zdenci/export")
def api_zdenci_export():
    fmt = request.args.get("format", "csv").strip().lower()
    if fmt not in {"csv", "json"}:
        fmt = "csv"

    search_value = request.args.get("search", None, type=str)
    if search_value is None:
        search_value = request.args.get("search[value]", "", type=str)
    search_value = search_value.strip().lower()
    column_filters = _get_column_filters()
    where_clause, params = _build_search_clause(search_value, column_filters)
    order_clause = " ORDER BY g.naziv_gc ASC, z.lokacija ASC"

    cur = conn.cursor()
    cur.execute(
        f"SELECT {SELECT_COLUMNS} {BASE_FROM}{where_clause}{order_clause}",
        params,
    )
    rows, cols = fetch_rows_with_cols(cur)
    data = [dict(zip(cols, row)) for row in rows] if cols else []
    cur.close()

    if fmt == "json":
        grouped = {}
        for row in data:
            gc = row.get("naziv_gc") or "Nepoznato"
            items = grouped.setdefault(gc, [])
            entry = {}
            for key in JSON_COLUMNS:
                value = row.get(key)
                if value == "":
                    value = None
                if key in {"lon", "lat"}:
                    if value is None:
                        entry[key] = None
                    else:
                        try:
                            entry[key] = float(value)
                        except (TypeError, ValueError):
                            entry[key] = None
                else:
                    entry[key] = value
            items.append(entry)

        result = [{"naziv_gc": gc, "zdenci": grouped[gc]} for gc in grouped]
        payload = json.dumps(result, ensure_ascii=False, indent=2)
        return Response(
            payload,
            mimetype="application/json",
            headers={
                "Content-Disposition": "attachment; filename=zdenci_filtered.json"
            },
        )

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for row in data:
        writer.writerow(
            [row.get(key, "") if row.get(key) is not None else "" for key in CSV_COLUMNS]
        )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=zdenci_filtered.csv"},
    )
