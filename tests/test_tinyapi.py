"""
Testy pro TinyAPI
=================
Testy jsou jako kontrolní seznam letecké posádky před odletem.
Každý test zkontroluje, jestli jedna věc funguje správně.

Jak spustit:
  uv run pytest tests/            (doporučeno)
  uv run python tests/test_tinyapi.py  (bez pytest)
"""

import asyncio
from tinyapi import TinyAPI, Request, Response, Depends
from tinyapi.routing import Route, Router
from tinyapi.params import coerce


# ============================================================
# POMOCNÁ FUNKCE — spustí async handler synchronně v testech
# ============================================================
def run(coro):
    """Zkratka pro asyncio.run() v testech."""
    return asyncio.run(coro)


def make_request(method="GET", path="/", query_string="", body=b"", headers=None):
    """Vytvoří testovací Request objekt."""
    return Request(method, path, query_string, body, headers or {})


# ============================================================
# TESTY: Route matching
# ============================================================


def test_route_match_jednoducha_cesta():
    """Route bez parametrů."""

    def handler():
        pass

    route = Route("/domov", "GET", handler)

    assert route.match("/domov", "GET") == {}  # Shoda -> prázdný dict
    assert route.match("/jinde", "GET") is None  # Neshoda -> None
    assert route.match("/domov", "POST") is None  # Špatná metoda


def test_route_match_s_parametrem():
    """Route s {id} parametrem."""

    def handler():
        pass

    route = Route("/uzivatele/{id}", "GET", handler)

    assert route.match("/uzivatele/42", "GET") == {"id": "42"}
    assert route.match("/uzivatele/abc", "GET") == {"id": "abc"}
    assert route.match("/uzivatele/", "GET") is None  # Chybí id


def test_route_match_vice_parametru():
    """Route s více parametry."""

    def handler():
        pass

    route = Route("/produkty/{kategorie}/{id}", "GET", handler)

    result = route.match("/produkty/ovoce/5", "GET")
    assert result == {"kategorie": "ovoce", "id": "5"}


# ============================================================
# TESTY: Router
# ============================================================


def test_router_resolve():
    """Router najde správnou route."""
    router = Router()

    @router.get("/")
    def domov():
        return "ahoj"

    @router.get("/uzivatele/{id}")
    def uzivatel(id: int):
        return id

    route, params = router.resolve("/", "GET")
    assert route is not None
    assert route.handler == domov

    route, params = router.resolve("/uzivatele/42", "GET")
    assert params == {"id": "42"}

    route, params = router.resolve("/neexistuje", "GET")
    assert route is None


# ============================================================
# TESTY: Typová konverze (coerce)
# ============================================================


def test_coerce_int():
    assert coerce("42", int) == 42
    assert coerce("0", int) == 0


def test_coerce_float():
    assert coerce("3.14", float) == 3.14


def test_coerce_bool():
    assert coerce("true", bool) is True
    assert coerce("1", bool) is True
    assert coerce("ano", bool) is True
    assert coerce("false", bool) is False
    assert coerce("ne", bool) is False


def test_coerce_str():
    assert coerce("ahoj", str) == "ahoj"


# ============================================================
# TESTY: TinyAPI app (end-to-end)
# ============================================================


def test_app_get_handler():
    """Základní GET endpoint."""
    app = TinyAPI()

    @app.get("/")
    def domov():
        return {"zprava": "ok"}

    req = make_request("GET", "/")
    resp = run(app.handle_request(req))

    assert resp.status_code == 200
    import json

    data = json.loads(resp.body)
    assert data["zprava"] == "ok"


def test_app_404():
    """Neexistující URL vrátí 404."""
    app = TinyAPI()
    req = make_request("GET", "/neexistuje")
    resp = run(app.handle_request(req))
    assert resp.status_code == 404


def test_app_path_param_konverze():
    """Path parametr se správně převede na int."""
    app = TinyAPI()

    @app.get("/nasobit/{a}/{b}")
    def nasob(a: int, b: int):
        return {"vysledek": a * b}

    req = make_request("GET", "/nasobit/6/7")
    resp = run(app.handle_request(req))

    import json

    data = json.loads(resp.body)
    assert data["vysledek"] == 42


def test_app_query_params():
    """Query parametry jsou správně parsovány."""
    app = TinyAPI()

    @app.get("/pocitej")
    def pocitej(start: int = 1, konec: int = 10):
        return {"soucet": sum(range(start, konec + 1))}

    req = make_request("GET", "/pocitej", query_string="start=1&konec=4")
    resp = run(app.handle_request(req))

    import json

    data = json.loads(resp.body)
    assert data["soucet"] == 10  # 1+2+3+4 = 10


def test_app_dependency_injection():
    """Depends() správně injektuje závislost."""
    app = TinyAPI()

    def get_cislo():
        return 42

    @app.get("/cislo")
    def vrат_cislo(cislo=Depends(get_cislo)):
        return {"cislo": cislo}

    req = make_request("GET", "/cislo")
    resp = run(app.handle_request(req))

    import json

    data = json.loads(resp.body)
    assert data["cislo"] == 42


def test_app_async_handler():
    """Async handlery fungují stejně jako sync."""
    app = TinyAPI()

    @app.get("/async")
    async def async_handler():
        import asyncio

        await asyncio.sleep(0)  # Simulace async operace
        return {"typ": "async"}

    req = make_request("GET", "/async")
    resp = run(app.handle_request(req))

    import json

    data = json.loads(resp.body)
    assert data["typ"] == "async"


def test_response_json():
    """Response správně serializuje slovník na JSON."""
    resp = Response({"klic": "hodnota"})
    assert resp.status_code == 200
    assert b'"klic"' in resp.body
    assert resp.headers["Content-Type"] == "application/json"


def test_response_text():
    """Response správně zpracuje text."""
    resp = Response("Ahoj!")
    assert resp.body == b"Ahoj!"


# ============================================================
# SPUŠTĚNÍ BEZ PYTEST
# ============================================================
if __name__ == "__main__":
    testy = [
        test_route_match_jednoducha_cesta,
        test_route_match_s_parametrem,
        test_route_match_vice_parametru,
        test_router_resolve,
        test_coerce_int,
        test_coerce_float,
        test_coerce_bool,
        test_coerce_str,
        test_app_get_handler,
        test_app_404,
        test_app_path_param_konverze,
        test_app_query_params,
        test_app_dependency_injection,
        test_app_async_handler,
        test_response_json,
        test_response_text,
    ]

    prosel = 0
    selhal = 0

    for test in testy:
        try:
            test()
            print(f"  OK  {test.__name__}")
            prosel += 1
        except AssertionError as e:
            print(f"  CHYBA {test.__name__}: {e}")
            selhal += 1
        except Exception as e:
            print(f"  VÝJIMKA {test.__name__}: {type(e).__name__}: {e}")
            selhal += 1

    print()
    print(f"Výsledek: {prosel} prošlo, {selhal} selhalo")
