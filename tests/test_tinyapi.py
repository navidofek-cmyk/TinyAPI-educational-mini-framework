"""
Testy pro TinyAPI
=================
Jak spustit:
  uv run pytest tests/ -v
  uv run pytest tests/ --cov=tinyapi --cov-report=term-missing
"""

import asyncio
import io
import json
from unittest.mock import MagicMock, patch

import pytest

from tinyapi import Depends, Request, Response, TinyAPI
from tinyapi.dependencies import Depends as DependsClass
from tinyapi.params import coerce, resolve_handler_params
from tinyapi.routing import Route, Router
from tinyapi.server import make_wsgi_app, run_server


# ============================================================
# POMOCNÉ FUNKCE
# ============================================================


def run(coro):
    """Zkratka pro asyncio.run() v testech."""
    return asyncio.run(coro)


def make_request(method="GET", path="/", query_string="", body=b"", headers=None):
    """Vytvoří testovací Request objekt."""
    return Request(method, path, query_string, body, headers or {})


def make_wsgi_environ(method="GET", path="/", query_string="", body=b"", headers=None):
    """Vytvoří WSGI environ slovník pro testování server.py."""
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query_string,
        "CONTENT_LENGTH": str(len(body)) if body else "",
        "wsgi.input": io.BytesIO(body),
    }
    # Přidáme HTTP hlavičky ve WSGI formátu (HTTP_NAZEV)
    for key, value in (headers or {}).items():
        environ[f"HTTP_{key.upper().replace('-', '_')}"] = value
    return environ


# ============================================================
# TESTY: Response — všechny typy obsahu
# ============================================================


def test_response_json():
    resp = Response({"klic": "hodnota"})
    assert resp.status_code == 200
    assert b'"klic"' in resp.body
    assert resp.headers["Content-Type"] == "application/json"


def test_response_list():
    """Response umí serializovat seznam na JSON."""
    resp = Response([1, 2, 3])
    assert json.loads(resp.body) == [1, 2, 3]
    assert resp.headers["Content-Type"] == "application/json"


def test_response_text():
    resp = Response("Ahoj!")
    assert resp.body == b"Ahoj!"
    assert "text/plain" in resp.headers["Content-Type"]


def test_response_bytes():
    """Response s bytes obsahem se uloží beze změny."""
    resp = Response(b"\x00\x01\x02")
    assert resp.body == b"\x00\x01\x02"


def test_response_none():
    """Response s None vytvoří prázdné tělo."""
    resp = Response(None)
    assert resp.body == b""


def test_response_jine_typy():
    """Response převede číslo na text přes str()."""
    resp = Response(42)
    assert resp.body == b"42"


def test_response_vlastni_status():
    resp = Response({"ok": True}, status_code=201)
    assert resp.status_code == 201


def test_response_vlastni_headers():
    resp = Response("ok", headers={"X-Vlastni": "hodnota"})
    assert resp.headers["X-Vlastni"] == "hodnota"


def test_response_status_text_zname():
    """status_text vrátí správný popis pro známé kódy."""
    assert Response(status_code=200).status_text == "OK"
    assert Response(status_code=404).status_text == "Not Found"
    assert Response(status_code=500).status_text == "Internal Server Error"
    assert Response(status_code=201).status_text == "Created"
    assert Response(status_code=422).status_text == "Unprocessable Entity"


def test_response_status_text_nezname():
    """status_text vrátí 'Unknown' pro neznámý kód."""
    assert Response(status_code=999).status_text == "Unknown"


def test_response_repr():
    resp = Response("hi")
    r = repr(resp)
    assert "Response(" in r
    assert "200" in r


# ============================================================
# TESTY: Request — všechny metody
# ============================================================


def test_request_query_params_jednoduche():
    req = Request("GET", "/", query_string="a=1&b=2")
    assert req.query_params == {"a": "1", "b": "2"}


def test_request_query_params_vicenasobne():
    """Více hodnot pro jeden klíč vrátí seznam."""
    req = Request("GET", "/", query_string="tag=a&tag=b")
    assert req.query_params["tag"] == ["a", "b"]


def test_request_query_params_prazdne():
    req = Request("GET", "/")
    assert req.query_params == {}


def test_request_query_params_cache():
    """Lazy loading — query_params se parsuje jen jednou."""
    req = Request("GET", "/", query_string="x=1")
    first = req.query_params
    second = req.query_params
    assert first is second  # stejný objekt (ne přepočítaný)


def test_request_json():
    """Request.json() přečte tělo jako Python slovník."""
    body = b'{"jmeno": "Honza", "vek": 10}'
    req = Request("POST", "/", body=body)
    data = req.json()
    assert data["jmeno"] == "Honza"
    assert data["vek"] == 10


def test_request_text():
    """Request.text() přečte tělo jako string."""
    req = Request("POST", "/", body="Ahoj světe!".encode("utf-8"))
    assert req.text() == "Ahoj světe!"


def test_request_repr():
    req = Request("DELETE", "/uzivatele/5")
    r = repr(req)
    assert "DELETE" in r
    assert "/uzivatele/5" in r


def test_request_method_upper():
    """Metoda se vždy uloží jako velká písmena."""
    req = Request("get", "/")
    assert req.method == "GET"


# ============================================================
# TESTY: Route matching
# ============================================================


def test_route_match_jednoducha_cesta():
    def handler():
        pass

    route = Route("/domov", "GET", handler)
    assert route.match("/domov", "GET") == {}
    assert route.match("/jinde", "GET") is None
    assert route.match("/domov", "POST") is None


def test_route_match_s_parametrem():
    def handler():
        pass

    route = Route("/uzivatele/{id}", "GET", handler)
    assert route.match("/uzivatele/42", "GET") == {"id": "42"}
    assert route.match("/uzivatele/abc", "GET") == {"id": "abc"}
    assert route.match("/uzivatele/", "GET") is None


def test_route_match_vice_parametru():
    def handler():
        pass

    route = Route("/produkty/{kategorie}/{id}", "GET", handler)
    result = route.match("/produkty/ovoce/5", "GET")
    assert result == {"kategorie": "ovoce", "id": "5"}


def test_route_match_method_case_insensitive():
    """match() funguje s malými i velkými písmeny metody."""

    def handler():
        pass

    route = Route("/test", "GET", handler)
    assert route.match("/test", "get") == {}
    assert route.match("/test", "GET") == {}


# ============================================================
# TESTY: Router — všechny HTTP metody
# ============================================================


def test_router_resolve():
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


def test_router_post():
    router = Router()

    @router.post("/data")
    def handler():
        return "created"

    route, _ = router.resolve("/data", "POST")
    assert route is not None
    assert route.method == "POST"


def test_router_put():
    router = Router()

    @router.put("/data/{id}")
    def handler(id: int):
        return id

    route, params = router.resolve("/data/5", "PUT")
    assert route is not None
    assert params == {"id": "5"}


def test_router_delete():
    router = Router()

    @router.delete("/data/{id}")
    def handler(id: int):
        return id

    route, _ = router.resolve("/data/3", "DELETE")
    assert route is not None


def test_router_patch():
    router = Router()

    @router.patch("/data/{id}")
    def handler(id: int):
        return id

    route, _ = router.resolve("/data/1", "PATCH")
    assert route is not None


def test_router_repr():
    """Router.__repr__ obsahuje metodu a cestu."""
    router = Router()

    @router.get("/test")
    def h():
        pass

    r = repr(router)
    assert "GET" in r
    assert "/test" in r
    assert "h()" in r


# ============================================================
# TESTY: Depends
# ============================================================


def test_depends_repr():
    """Depends.__repr__ obsahuje název závislosti."""

    def moje_zavislost():
        pass

    d = DependsClass(moje_zavislost)
    assert "moje_zavislost" in repr(d)


# ============================================================
# TESTY: coerce — typová konverze
# ============================================================


def test_coerce_int():
    assert coerce("42", int) == 42
    assert coerce("0", int) == 0


def test_coerce_float():
    assert coerce("3.14", float) == 3.14


def test_coerce_bool_true():
    assert coerce("true", bool) is True
    assert coerce("1", bool) is True
    assert coerce("ano", bool) is True
    assert coerce("yes", bool) is True


def test_coerce_bool_false():
    assert coerce("false", bool) is False
    assert coerce("0", bool) is False
    assert coerce("ne", bool) is False


def test_coerce_str():
    assert coerce("ahoj", str) == "ahoj"


def test_coerce_invalid_int():
    """Převod nečíselného textu na int vyhodí TypeError."""
    with pytest.raises(TypeError, match="Nelze převést"):
        coerce("abc", int)


def test_coerce_invalid_float():
    """Převod nečíselného textu na float vyhodí TypeError."""
    with pytest.raises(TypeError):
        coerce("xyz", float)


# ============================================================
# TESTY: resolve_handler_params — introspekce parametrů
# ============================================================


def test_params_request_objekt():
    """Parametr s type hintem Request dostane celý objekt."""

    async def handler(req: Request):
        return req

    request = make_request("GET", "/")
    kwargs = run(resolve_handler_params(handler, request, {}))
    assert kwargs["req"] is request


def test_params_path_param():
    """Path parametry se načtou z path_params slovníku."""

    async def handler(id: int):
        return id

    request = make_request("GET", "/")
    kwargs = run(resolve_handler_params(handler, request, {"id": "42"}))
    assert kwargs["id"] == 42


def test_params_query_param():
    """Query parametry se načtou z URL za otazníkem."""

    async def handler(q: str):
        return q

    request = make_request("GET", "/", query_string="q=hello")
    kwargs = run(resolve_handler_params(handler, request, {}))
    assert kwargs["q"] == "hello"


def test_params_default_hodnota():
    """Parametr s výchozí hodnotou dostane default pokud není v URL."""

    async def handler(limit: int = 10):
        return limit

    request = make_request("GET", "/")
    kwargs = run(resolve_handler_params(handler, request, {}))
    assert kwargs["limit"] == 10


def test_params_chybejici_povinny():
    """Povinný parametr bez hodnoty vyhodí TypeError."""

    async def handler(povinny: str):
        return povinny

    request = make_request("GET", "/")
    with pytest.raises(TypeError, match="Chybí povinný parametr"):
        run(resolve_handler_params(handler, request, {}))


def test_params_bad_type_hints():
    """Funkce s neresolvovatelnými type hinty se nezhroutí."""

    # forward reference na neexistující typ — get_type_hints selže
    def handler(x: "TypKteryNeexistuje"):  # noqa: F821
        return x

    request = make_request("GET", "/", query_string="x=hello")
    kwargs = run(resolve_handler_params(handler, request, {}))
    assert kwargs["x"] == "hello"


def test_params_sync_depends():
    """Sync Depends se správně vyřeší."""

    def get_hodnota():
        return 99

    async def handler(val=Depends(get_hodnota)):
        return val

    request = make_request("GET", "/")
    kwargs = run(resolve_handler_params(handler, request, {}))
    assert kwargs["val"] == 99


def test_params_async_depends():
    """Async Depends se správně vyřeší pomocí await."""

    async def async_dep():
        return "async_hodnota"

    async def handler(val=Depends(async_dep)):
        return val

    request = make_request("GET", "/")
    kwargs = run(resolve_handler_params(handler, request, {}))
    assert kwargs["val"] == "async_hodnota"


# ============================================================
# TESTY: TinyAPI app — end-to-end
# ============================================================


def test_app_get_handler():
    app = TinyAPI()

    @app.get("/")
    def domov():
        return {"zprava": "ok"}

    req = make_request("GET", "/")
    resp = run(app.handle_request(req))
    assert resp.status_code == 200
    assert json.loads(resp.body)["zprava"] == "ok"


def test_app_404():
    app = TinyAPI()
    req = make_request("GET", "/neexistuje")
    resp = run(app.handle_request(req))
    assert resp.status_code == 404


def test_app_path_param_konverze():
    app = TinyAPI()

    @app.get("/nasobit/{a}/{b}")
    def nasob(a: int, b: int):
        return {"vysledek": a * b}

    req = make_request("GET", "/nasobit/6/7")
    resp = run(app.handle_request(req))
    assert json.loads(resp.body)["vysledek"] == 42


def test_app_query_params():
    app = TinyAPI()

    @app.get("/pocitej")
    def pocitej(start: int = 1, konec: int = 10):
        return {"soucet": sum(range(start, konec + 1))}

    req = make_request("GET", "/pocitej", query_string="start=1&konec=4")
    resp = run(app.handle_request(req))
    assert json.loads(resp.body)["soucet"] == 10


def test_app_dependency_injection():
    app = TinyAPI()

    def get_cislo():
        return 42

    @app.get("/cislo")
    def vrat_cislo(cislo=Depends(get_cislo)):
        return {"cislo": cislo}

    req = make_request("GET", "/cislo")
    resp = run(app.handle_request(req))
    assert json.loads(resp.body)["cislo"] == 42


def test_app_async_handler():
    app = TinyAPI()

    @app.get("/async")
    async def async_handler():
        await asyncio.sleep(0)
        return {"typ": "async"}

    req = make_request("GET", "/async")
    resp = run(app.handle_request(req))
    assert json.loads(resp.body)["typ"] == "async"


def test_app_handler_vrati_response_primo():
    """Handler může vrátit Response objekt přímo — použije se beze změny."""
    app = TinyAPI()

    @app.get("/custom")
    def handler():
        return Response("vlastni obsah", status_code=201)

    req = make_request("GET", "/custom")
    resp = run(app.handle_request(req))
    assert resp.status_code == 201
    assert resp.body == b"vlastni obsah"


def test_app_handler_vyhodi_vyjimku():
    """Výjimka v handleru vrátí 500 Internal Server Error."""
    app = TinyAPI()

    @app.get("/boom")
    def handler():
        raise ValueError("něco selhalo")

    req = make_request("GET", "/boom")
    resp = run(app.handle_request(req))
    assert resp.status_code == 500
    assert "něco selhalo" in json.loads(resp.body)["chyba"]


def test_app_422_chybejici_parametr():
    """Chybějící povinný parametr vrátí 422."""
    app = TinyAPI()

    @app.get("/test")
    def handler(povinny: str):
        return povinny

    req = make_request("GET", "/test")
    resp = run(app.handle_request(req))
    assert resp.status_code == 422


def test_app_sync_middleware():
    """Sync middleware se zavolá před každým požadavkem."""
    app = TinyAPI()
    log = []

    @app.middleware
    def mw(request: Request):
        log.append(f"before:{request.path}")

    @app.get("/")
    def handler():
        return "ok"

    run(app.handle_request(make_request("GET", "/")))
    assert log == ["before:/"]


def test_app_async_middleware():
    """Async middleware se zavolá pomocí await."""
    app = TinyAPI()
    log = []

    @app.middleware
    async def async_mw(request: Request):
        await asyncio.sleep(0)
        log.append("async_middleware")

    @app.get("/")
    def handler():
        return "ok"

    run(app.handle_request(make_request("GET", "/")))
    assert log == ["async_middleware"]


def test_app_vice_middleware():
    """Více middleware se spustí v pořadí registrace."""
    app = TinyAPI()
    log = []

    @app.middleware
    def mw1(r: Request):
        log.append("mw1")

    @app.middleware
    def mw2(r: Request):
        log.append("mw2")

    @app.get("/")
    def handler():
        return "ok"

    run(app.handle_request(make_request("GET", "/")))
    assert log == ["mw1", "mw2"]


def test_app_repr():
    """app.__repr__ obsahuje TinyAPI a seznam routes."""
    app = TinyAPI()

    @app.get("/test")
    def h():
        return "ok"

    r = repr(app)
    assert "TinyAPI" in r
    assert "/test" in r


def test_app_vsechny_metody():
    """App zpřístupňuje POST, PUT, DELETE, PATCH přes zkratky."""
    app = TinyAPI()

    @app.post("/a")
    def post_h():
        return "post"

    @app.put("/b")
    def put_h():
        return "put"

    @app.delete("/c")
    def delete_h():
        return "delete"

    @app.patch("/d")
    def patch_h():
        return "patch"

    assert run(app.handle_request(make_request("POST", "/a"))).status_code == 200
    assert run(app.handle_request(make_request("PUT", "/b"))).status_code == 200
    assert run(app.handle_request(make_request("DELETE", "/c"))).status_code == 200
    assert run(app.handle_request(make_request("PATCH", "/d"))).status_code == 200


# ============================================================
# TESTY: WSGI server (server.py)
# ============================================================


def test_wsgi_get():
    """WSGI app zpracuje GET request a vrátí JSON."""
    app = TinyAPI()

    @app.get("/")
    def home():
        return {"ok": True}

    wsgi = make_wsgi_app(app)
    responses = []

    def start_response(status, headers):
        responses.append((status, dict(headers)))

    result = wsgi(make_wsgi_environ("GET", "/"), start_response)
    assert responses[0][0] == "200 OK"
    assert json.loads(result[0])["ok"] is True
    assert "Content-Length" in responses[0][1]


def test_wsgi_post_s_body():
    """WSGI app přečte tělo POST requestu."""
    app = TinyAPI()

    @app.post("/echo")
    def echo(request: Request):
        return request.json()

    wsgi = make_wsgi_app(app)
    responses = []

    def start_response(status, headers):
        responses.append(status)

    body = b'{"hello": "world"}'
    environ = make_wsgi_environ("POST", "/echo", body=body)
    result = wsgi(environ, start_response)
    assert "200" in responses[0]
    assert json.loads(result[0])["hello"] == "world"


def test_wsgi_query_string():
    """WSGI app předá query string do request.query_params."""
    app = TinyAPI()

    @app.get("/hledat")
    def hledat(q: str):
        return {"q": q}

    wsgi = make_wsgi_app(app)
    responses = []

    def start_response(status, headers):
        responses.append(status)

    environ = make_wsgi_environ("GET", "/hledat", query_string="q=pes")
    result = wsgi(environ, start_response)
    assert json.loads(result[0])["q"] == "pes"


def test_wsgi_http_hlavicky():
    """WSGI app přeloží HTTP_ proměnné na hlavičky requestu."""
    app = TinyAPI()

    @app.get("/hlavicky")
    def hlavicky(request: Request):
        return {"auth": request.headers.get("Authorization", "")}

    wsgi = make_wsgi_app(app)
    responses = []

    def start_response(status, headers):
        responses.append(status)

    environ = make_wsgi_environ(
        "GET", "/hlavicky", headers={"Authorization": "token-test"}
    )
    result = wsgi(environ, start_response)
    assert json.loads(result[0])["auth"] == "token-test"


def test_wsgi_404():
    """WSGI app vrátí 404 pro neznámou cestu."""
    app = TinyAPI()
    wsgi = make_wsgi_app(app)
    responses = []

    def start_response(status, headers):
        responses.append(status)

    wsgi(make_wsgi_environ("GET", "/neexistuje"), start_response)
    assert "404" in responses[0]


def test_wsgi_prazdne_content_length():
    """WSGI app zvládne chybějící nebo prázdné CONTENT_LENGTH."""
    app = TinyAPI()

    @app.get("/")
    def home():
        return "ok"

    wsgi = make_wsgi_app(app)
    responses = []

    def start_response(status, headers):
        responses.append(status)

    # CONTENT_LENGTH chybí úplně
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/",
        "QUERY_STRING": "",
        "wsgi.input": io.BytesIO(b""),
    }
    wsgi(environ, start_response)
    assert "200" in responses[0]


def test_app_run_predava_parametry():
    """app.run() předá host a port do run_server."""
    app = TinyAPI()
    volani = []

    def fake_run_server(a, host, port):
        volani.append((host, port))

    with patch("tinyapi.server.run_server", fake_run_server):
        app.run(host="127.0.0.1", port=7777)

    assert volani == [("127.0.0.1", 7777)]


def test_run_server_keyboard_interrupt(capsys):
    """run_server se čistě ukončí při KeyboardInterrupt (Ctrl+C)."""
    app = TinyAPI()

    mock_httpd = MagicMock()
    mock_httpd.serve_forever.side_effect = KeyboardInterrupt
    mock_httpd.__enter__ = lambda s: mock_httpd
    mock_httpd.__exit__ = MagicMock(return_value=False)

    with patch("tinyapi.server.make_server", return_value=mock_httpd):
        run_server(app, host="127.0.0.1", port=19999)

    mock_httpd.serve_forever.assert_called_once()
    captured = capsys.readouterr()
    assert "zastaven" in captured.out
