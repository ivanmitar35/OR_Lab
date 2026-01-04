from pathlib import Path

from flask import Response, render_template, send_file

from .blueprint import main

OPENAPI_PATH = Path(__file__).resolve().parents[1] / "openapi.json"


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/datatable")
def datatable():
    return render_template("datatable.html")


@main.route("/openapi.json")
def openapi_spec():
    return send_file(OPENAPI_PATH, mimetype="application/json")


@main.route("/docs")
def docs():
    html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Swagger UI</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    <style>
      body { margin: 0; background: #f4f5f7; }
      #swagger-ui { height: 100vh; }
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.onload = () => {
        SwaggerUIBundle({
          url: "/openapi.json",
          dom_id: "#swagger-ui",
          presets: [SwaggerUIBundle.presets.apis],
          layout: "BaseLayout"
        });
      };
    </script>
  </body>
</html>
"""
    return Response(html, mimetype="text/html")
