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

REST_COLUMNS = [
    ("id", "z.id"),
    ("lokacija", "z.lokacija"),
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
    ("naziv_gc_id", "z.naziv_gc_id"),
    ("naziv_gc", "g.naziv_gc"),
]
REST_SELECT_COLUMNS = ", ".join([f"{sql} AS {key}" for key, sql in REST_COLUMNS])
REST_SEARCH_COLUMNS = [
    sql
    for key, sql in REST_COLUMNS
    if key not in {"id", "naziv_gc_id"}
]
REST_PAYLOAD_FIELDS = {
    "id": "int",
    "lokacija": "text",
    "tip_zdenca": "text",
    "status_odrz": "text",
    "aktivan_da_ne": "text",
    "teren_dane": "text",
    "vlasnik_ki": "text",
    "odrzava_ki": "text",
    "zkc_oznaka": "text",
    "broj_vodomjera": "text",
    "napomena_teren": "text",
    "pozicija_tocnost": "text",
    "lon": "num",
    "lat": "num",
    "naziv_gc_id": "int",
}
MAP_COLUMNS = [
    ("id", "z.id"),
    ("lokacija", "z.lokacija"),
    ("lon", "z.lon"),
    ("lat", "z.lat"),
    ("naziv_gc", "g.naziv_gc"),
]
MAP_SELECT_COLUMNS = ", ".join([f"{sql} AS {key}" for key, sql in MAP_COLUMNS])
