JSONLD_CONTEXT = {
    "@vocab": "https://schema.org/",
    "lokacija": "address",
    "lat": "latitude",
    "lon": "longitude",
}
JSONLD_TYPE = "https://schema.org/Place"


def add_jsonld(item):
    if not isinstance(item, dict):
        return item

    enriched = dict(item)
    enriched["@context"] = JSONLD_CONTEXT
    enriched["@type"] = JSONLD_TYPE

    return enriched


def add_jsonld_list(items):
    if not items:
        return []
    return [add_jsonld(item) for item in items]
