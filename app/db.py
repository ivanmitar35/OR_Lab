import psycopg2

conn = psycopg2.connect(
    dbname="zdenci_test", user="postgres", password="123", host="localhost"
)


# Safely read a single COUNT(*) result.
def fetch_count(cur):
    row = cur.fetchone()
    if not row:
        return 0
    return row[0]


# Fetch rows plus column names when available.
def fetch_rows_with_cols(cur):
    rows = cur.fetchall()
    if not cur.description:
        return rows, []
    cols = [desc[0] for desc in cur.description]
    return rows, cols


def fetch_row_with_cols(cur):
    row = cur.fetchone()
    if not row or not cur.description:
        return None, []
    cols = [desc[0] for desc in cur.description]
    return row, cols
