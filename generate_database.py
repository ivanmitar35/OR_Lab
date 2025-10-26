import json
import psycopg2
from psycopg2.extras import execute_values

DB_NAME = "zdenci"
DB_USER = "postgres"
DB_PASS = "123"
DB_HOST = "localhost"
JSON_FILE = "zdenci.json"

conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST
)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS gradska_cetvrt (
    id SERIAL PRIMARY KEY,
    naziv_gc TEXT UNIQUE NOT NULL
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS zdenac (
    id SERIAL PRIMARY KEY,
    lokacija TEXT,
    tip_zdenca TEXT,
    status_odrz TEXT,
    aktivan_da_ne TEXT,
    teren_dane TEXT,
    vlasnik_ki TEXT,
    odrzava_ki TEXT,
    zkc_oznaka TEXT,
    broj_vodomjera TEXT,
    napomena_teren TEXT,
    pozicija_tocnost TEXT,
    lon DECIMAL,
    lat DECIMAL,
    naziv_gc_id INTEGER REFERENCES gradska_cetvrt(id) ON DELETE SET NULL
);
""")
conn.commit()

with open(JSON_FILE, encoding="utf-8") as f:
    data = json.load(f)

for item in data:
    gc_name = item["naziv_gc"].strip() if item["naziv_gc"] else "Nepoznato"

    cur.execute("""
        INSERT INTO gradska_cetvrt (naziv_gc)
        VALUES (%s)
        ON CONFLICT (naziv_gc) DO NOTHING
        RETURNING id;
    """, (gc_name,))
    row = cur.fetchone()
    if row:
        gc_id = row[0]
    else:
        cur.execute("SELECT id FROM gradska_cetvrt WHERE naziv_gc = %s;", (gc_name,))
        gc_id = cur.fetchone()[0]

    values = [
        (
            z.get("lokacija"),
            z.get("tip_zdenca"),
            z.get("status_odrz"),
            z.get("aktivan_da_ne"),
            z.get("teren_dane"),
            z.get("vlasnik_ki"),
            z.get("odrzava_ki"),
            z.get("zkc_oznaka"),
            z.get("broj_vodomjera"),
            z.get("napomena_teren"),
            z.get("pozicija_tocnost"),
            z.get("lon"),
            z.get("lat"),
            gc_id
        )
        for z in item["zdenci"]
    ]

    execute_values(cur, """
        INSERT INTO zdenac (
            lokacija, tip_zdenca, status_odrz, aktivan_da_ne, teren_dane,
            vlasnik_ki, odrzava_ki, zkc_oznaka, broj_vodomjera,
            napomena_teren, pozicija_tocnost, lon, lat, naziv_gc_id
        )
        VALUES %s;
    """, values)

conn.commit()
cur.close()
conn.close()
print("uspješno")
