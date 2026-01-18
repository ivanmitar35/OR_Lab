import csv
import io
import json

from .db import conn, fetch_rows_with_cols
from .jsonld import add_jsonld
from .zdenci_constants import BASE_FROM, CSV_COLUMNS, JSON_COLUMNS, SELECT_COLUMNS


def fetch_zdenci_data(where_clause="", params=None, order_clause=""):
    if params is None:
        params = []
    cur = conn.cursor()
    cur.execute(
        f"SELECT {SELECT_COLUMNS} {BASE_FROM}{where_clause}{order_clause}",
        params,
    )
    rows, cols = fetch_rows_with_cols(cur)
    cur.close()
    return [dict(zip(cols, row)) for row in rows] if cols else []


def build_csv_payload(data, columns=CSV_COLUMNS):
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(columns)
    for row in data:
        writer.writerow([row.get(key, "") if row.get(key) is not None else "" for key in columns])
    return output.getvalue()


def build_grouped_json_payload(data, json_columns=JSON_COLUMNS):
    grouped = {}
    for row in data:
        gc = row.get("naziv_gc") or "Nepoznato"
        items = grouped.setdefault(gc, [])
        entry = {}
        for key in json_columns:
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
        items.append(add_jsonld(entry))
    result = [{"naziv_gc": gc, "zdenci": grouped[gc]} for gc in grouped]
    return json.dumps(result, ensure_ascii=False, indent=2)
