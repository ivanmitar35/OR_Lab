from .blueprint import main
from .api.datatable_api import api_zdenci, api_zdenci_export
from .api.rest_api import (
    api_v1_gradske_cetvrti,
    api_v1_zdenci_create,
    api_v1_zdenci_delete,
    api_v1_zdenci_get,
    api_v1_zdenci_koordinate,
    api_v1_zdenci_list,
    api_v1_zdenci_statusi,
    api_v1_zdenci_update,
)
from .web.web_routes import datatable, docs, index, openapi_spec

__all__ = [
    "main",
    "datatable",
    "index",

    # DataTables UI
    "api_zdenci",
    "api_zdenci_export",

    # REST API
    "api_v1_gradske_cetvrti",
    "api_v1_zdenci_create",
    "api_v1_zdenci_delete",
    "api_v1_zdenci_get",
    "api_v1_zdenci_koordinate",
    "api_v1_zdenci_list",
    "api_v1_zdenci_statusi",
    "api_v1_zdenci_update",
    "docs",
    "openapi_spec",
]
