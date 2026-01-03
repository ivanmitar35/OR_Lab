from flask import Blueprint, Response, jsonify, render_template, request
import csv
import io
import json
import psycopg2

main = Blueprint("main", __name__)

conn = psycopg2.connect(
    dbname="zdenci", user="postgres", password="123", host="localhost"
)

DATA_COLUMNS = [
    ("lokacija", "z.lokacija"),
    ("naziv_gc", "g.naziv_gc"),
    ("tip_zdenca", "z.tip_zdenca"),
    ("status_odrz", "z.status_odrz"),
    ("aktivan_da_ne", "z.aktivan_da_ne"),
    ("teren_dane", "z.teren_dane"),
    ("vlasnik_ki", "z.vlasnik_ki"),
    ("odrzava_ki", "z.odrzava_ki"),
    ("zkc_oznaka", "z.zkc_oznaka"),
    ("broj_vodomjera", "z.broj_vodomjera"),
    ("napomena_teren", "z.napomena_teren"),
    ("pozicija_tocnost", "z.pozicija_tocnost"),
    ("lon", "z.lon"),
    ("lat", "z.lat"),
]
DATA_KEYS = [key for key, _ in DATA_COLUMNS]
COLUMN_SQL = {key: sql for key, sql in DATA_COLUMNS}
SELECT_COLUMNS = ", ".join([f"{sql} AS {key}" for key, sql in DATA_COLUMNS])
BASE_FROM = "FROM zdenac z LEFT JOIN gradska_cetvrt g ON z.naziv_gc_id = g.id"
SEARCH_COLUMNS = [sql for _, sql in DATA_COLUMNS]
CSV_COLUMNS = [
    "naziv_gc",
    "lokacija",
    "tip_zdenca",
    "status_odrz",
    "aktivan_da_ne",
    "teren_dane",
    "vlasnik_ki",
    "odrzava_ki",
    "zkc_oznaka",
    "broj_vodomjera",
    "napomena_teren",
    "pozicija_tocnost",
    "lon",
    "lat",
]
JSON_COLUMNS = [
    "lokacija",
    "tip_zdenca",
    "status_odrz",
    "aktivan_da_ne",
    "teren_dane",
    "vlasnik_ki",
    "odrzava_ki",
    "zkc_oznaka",
    "broj_vodomjera",
    "napomena_teren",
    "pozicija_tocnost",
    "lon",
    "lat",
]
NUMERIC_KEYS = {"lon", "lat"}


def _fetch_count(cur):
    row = cur.fetchone()
    if not row:
        return 0
    return row[0]


def _fetch_rows_with_cols(cur):
    rows = cur.fetchall()
    if not cur.description:
        return rows, []
    cols = [desc[0] for desc in cur.description]
    return rows, cols


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


def _get_order_clause(order_index, order_dir, default_clause):
    if order_index is None or order_index < 0 or order_index >= len(DATA_KEYS):
        return default_clause

    direction = "DESC" if str(order_dir).lower() == "desc" else "ASC"
    col_key = DATA_KEYS[order_index]
    col_sql = COLUMN_SQL.get(col_key)
    if not col_sql:
        return default_clause

    return f" ORDER BY {col_sql} {direction}"


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

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/datatable")
def datatable():
    return render_template("datatable.html")

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
    total_count = _fetch_count(cur)

    if where_clause:
        cur.execute(f"SELECT COUNT(*) {BASE_FROM}{where_clause}", params)
        filtered_count = _fetch_count(cur)
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
    rows, cols = _fetch_rows_with_cols(cur)
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
    rows, cols = _fetch_rows_with_cols(cur)
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
