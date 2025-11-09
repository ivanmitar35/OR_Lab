from flask import Blueprint, jsonify, render_template, request
import psycopg2

main = Blueprint("main", __name__)

conn = psycopg2.connect(
    dbname="zdenci", user="postgres", password="123", host="localhost"
)

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/datatable")
def datatable():
    return render_template("datatable.html")

@main.route("/api/zdenci")
def api_zdenci():
    q = request.args.get("query", "").lower()
    cur = conn.cursor()
    if q:
        cur.execute("""
            SELECT *
            FROM zdenac z
            LEFT JOIN gradska_cetvrt g ON z.naziv_gc_id = g.id
            WHERE LOWER(lokacija) LIKE %s OR LOWER(naziv_gc) LIKE %s;
        """, (f"%{q}%", f"%{q}%"))
    else:
        cur.execute("""
            SELECT *
            FROM zdenac z
            LEFT JOIN gradska_cetvrt g ON z.naziv_gc_id = g.id;
        """)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    return jsonify([dict(zip(cols, r)) for r in rows])
