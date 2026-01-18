import json
from functools import wraps
from os import environ as env
from pathlib import Path

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import abort, flash, redirect, render_template, session, url_for

from .blueprint import main
from .data.snapshots import (
    build_csv_payload,
    build_grouped_json_payload,
    fetch_zdenci_data,
)

SNAPSHOT_DIR = Path(__file__).resolve().parent / "static" / "data"
CSV_SNAPSHOT_PATH = SNAPSHOT_DIR / "zdenci.csv"
JSON_SNAPSHOT_PATH = SNAPSHOT_DIR / "zdenci.json"


def _login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            abort(401)
        return func(*args, **kwargs)

    return wrapper


def _write_snapshot(path, payload):
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_text(payload, encoding="utf-8")
    temp_path.replace(path)


def _refresh_snapshots():
    data = fetch_zdenci_data(order_clause=" ORDER BY g.naziv_gc ASC, z.lokacija ASC")
    csv_payload = build_csv_payload(data)
    _write_snapshot(CSV_SNAPSHOT_PATH, csv_payload)
    json_payload = build_grouped_json_payload(data)
    _write_snapshot(JSON_SNAPSHOT_PATH, json_payload)


def _init_auth0(app):
    ENV_FILE = find_dotenv()
    if ENV_FILE:
        load_dotenv(ENV_FILE)
    app.config["SECRET_KEY"] = env.get("APP_SECRET_KEY")

    oauth = OAuth(app)

    oauth.register(
        "auth0",
        client_id=env.get("AUTH0_CLIENT_ID"),
        client_secret=env.get("AUTH0_CLIENT_SECRET"),
        client_kwargs={
            "scope": "openid profile email",
        },
        server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
    )

    @main.route("/login")
    def login():
        return oauth.auth0.authorize_redirect( # type: ignore
            redirect_uri=url_for("main.callback", _external=True)
        )

    @main.route("/callback", methods=["GET", "POST"])
    def callback():
        token = oauth.auth0.authorize_access_token() # type: ignore
        userinfo = oauth.auth0.get( # type: ignore
            f"https://{env.get('AUTH0_DOMAIN')}/userinfo", token=token
        ).json() # type: ignore
        session["user"] = userinfo
        return redirect(url_for("main.index"))

    @main.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("main.index"))
    
    @main.route("/profile")
    @_login_required
    def profile():
        user = session.get("user") or {}
        return render_template(
            "profile.html", user=user, pretty=json.dumps(user, ensure_ascii=False, indent=2)
        )

    @main.route("/refresh-snapshots")
    @_login_required
    def refresh_snapshots():
        _refresh_snapshots()
        flash("Preslike su uspješno osvježene.", "success")
        return redirect(url_for("main.index"))
