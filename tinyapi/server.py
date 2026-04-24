# Tento soubor spouští skutečný HTTP server.
# WSGI = Web Server Gateway Interface
# Je to "smlouva" (dohoda) mezi Python aplikací a HTTP serverem.
# Říká: "Tvoje Python aplikace musí mít funkci s přesně těmito parametry."
# Jako zástrčka a zásuvka — obě strany musí mít stejný tvar.
#
# Jak HTTP komunikace funguje?
# 1. Prohlížeč otevře TCP spojení na IP:port (například 192.168.0.163:8888)
# 2. Pošle textovou zprávu:
#       GET /uzivatele HTTP/1.1
#       Host: 192.168.0.163:8888
# 3. Server zpracuje požadavek (tady nastupuje náš kód)
# 4. Server vrátí textovou odpověď:
#       HTTP/1.1 200 OK
#       Content-Type: application/json
#
#       {"uzivatele": [...]}
# 5. Spojení se zavře
#
# wsgiref je součástí standardní Python knihovny — nic instalovat!
# Dělá kroky 1, 2 a 5 za nás. My řešíme jen krok 3 a 4.

# asyncio = asynchronní programování
import asyncio

# wsgiref.simple_server = jednoduchý WSGI HTTP server (součást Pythonu)
# make_server = funkce která vytvoří server
# WSGIServer = základní třída serveru
from wsgiref.simple_server import make_server, WSGIServer

# ThreadingMixIn = "příměs" která přidá vícevláknové zpracování
# socketserver = modul pro síťové servery
from socketserver import ThreadingMixIn

# Importujeme Request ze souboru request.py
from .request import Request


# Vytváříme novou třídu kombinací ThreadingMixIn a WSGIServer
# Toto se nazývá "multiple inheritance" (vícenásobné dědičnosti)
# Python převezme schopnosti OD OBOU rodičovských tříd
#
# ThreadingMixIn přidá: každý požadavek dostane vlastní vlákno (thread)
# Vlákno = "pracovník" — více vláken = více pracovníků najednou
#
# Python hledá metody v pořadí: ThreadedWSGIServer -> ThreadingMixIn -> WSGIServer
# Tomu se říká MRO = Method Resolution Order
class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    # daemon_threads = True znamená:
    # "Vlákna jsou démoni — ukončí se automaticky když skončí hlavní program"
    # Bez toho by server čekal na dokončení všech vláken i po Ctrl+C
    daemon_threads = True


# Funkce make_wsgi_app() obalí naši TinyAPI aplikaci do WSGI formátu
# tinyapi_app = naše TinyAPI instance (app)
def make_wsgi_app(tinyapi_app):

    # Definujeme WSGI funkci — toto je "smlouva" o které mluvíme výše
    # environ = slovník se vším o příchozím požadavku (dává ho WSGI server)
    # start_response = callback funkce pro nastavení status a hlaviček
    def wsgi_app(environ: dict, start_response):

        # --- PŘELOŽÍME WSGI environ NA NÁŠ REQUEST OBJEKT ---

        # environ["REQUEST_METHOD"] obsahuje HTTP metodu: "GET", "POST"...
        method = environ["REQUEST_METHOD"]

        # PATH_INFO obsahuje cestu URL: "/uzivatele/42"
        # .get() s výchozí hodnotou "/" pro případ že PATH_INFO chybí
        path = environ.get("PATH_INFO", "/")

        # QUERY_STRING je část URL za otazníkem: "jmeno=Honza&vek=10"
        # Výchozí prázdný řetězec pokud otazník v URL není
        query_string = environ.get("QUERY_STRING", "")

        # CONTENT_LENGTH říká kolik bajtů má tělo požadavku
        # int() převede text na číslo, or 0 = pokud je None/prázdné, použij 0
        content_length = int(environ.get("CONTENT_LENGTH", 0) or 0)

        # Přečteme tělo požadavku ze vstupu
        # Čteme jen pokud content_length > 0 (jsou tam nějaká data)
        # wsgi.input je jako soubor — .read(n) přečte n bajtů
        body = environ["wsgi.input"].read(content_length) if content_length > 0 else b""

        # HTTP hlavičky jsou v environ jako HTTP_NAZEV_HLAVICKY
        # Například Host: localhost -> HTTP_HOST: localhost
        headers = {}

        # Projdeme všechny klíče v environ
        for key, value in environ.items():
            # Zajímají nás jen klíče začínající "HTTP_"
            if key.startswith("HTTP_"):
                # Odstraníme prefix "HTTP_" (prvních 5 znaků: key[5:])
                # Nahradíme podtržítka pomlčkami: "CONTENT_TYPE" -> "CONTENT-TYPE"
                # .title() udělá první písmeno velké: "content-type" -> "Content-Type"
                header_name = key[5:].replace("_", "-").title()

                # Uložíme do slovníku
                headers[header_name] = value

        # Vytvoříme náš Request objekt ze všech shromážděných dat
        request = Request(method, path, query_string, body, headers)

        # --- ZAVOLÁME TINYAPI A ZÍSKÁME ODPOVĚĎ ---

        # asyncio.run() spustí async funkci z normálního (sync) kontextu
        # Je to "most" mezi sync WSGI světem a async TinyAPI světem
        # Čeká na výsledek a vrátí ho
        response = asyncio.run(tinyapi_app.handle_request(request))

        # --- PŘELOŽÍME RESPONSE ZPĚT DO WSGI FORMÁTU ---

        # status musí být string ve formátu "200 OK" nebo "404 Not Found"
        # f-string spojí číslo a text: 200 + " " + "OK" = "200 OK"
        status = f"{response.status_code} {response.status_text}"

        # WSGI vyžaduje hlavičky jako seznam dvojic (ne slovník)
        # list() převede dict.items() na seznam: [("Content-Type", "application/json"), ...]
        response_headers = list(response.headers.items())

        # Přidáme hlavičku Content-Length — říká prohlížeči jak velká je odpověď
        # str(len(...)) = počet bajtů převedený na text (WSGI chce string, ne int)
        response_headers.append(("Content-Length", str(len(response.body))))

        # Zavoláme start_response — tím WSGI serveru říkáme:
        # "Pošli tento status a tyto hlavičky prohlížeči"
        start_response(status, response_headers)

        # Vrátíme tělo odpovědi jako seznam bajtů (WSGI konvence vyžaduje seznam)
        # [response.body] = seznam s jedním prvkem (tělem odpovědi)
        return [response.body]

    # Vrátíme WSGI funkci (ne její výsledek — jen funkci samotnou)
    return wsgi_app


# run_server() spustí HTTP server a čeká na příchozí požadavky
# app = naše TinyAPI instance
# host = IP adresa ("0.0.0.0" = všechna rozhraní, dostupný z celé sítě)
# port = číslo portu (jako číslo bytu v bytovém domě)
def run_server(app, host: str = "0.0.0.0", port: int = 8888):

    # Přeložíme TinyAPI na WSGI aplikaci
    wsgi_app = make_wsgi_app(app)

    # "with" = context manager — zajistí správné ukončení i při chybě
    # make_server() vytvoří socket (síťový bod), naváže ho na host:port
    # server_class = použijeme náš vícevláknový server
    with make_server(host, port, wsgi_app, server_class=ThreadedWSGIServer) as httpd:
        # Vypíšeme informaci kam server naslouchá
        print(f"\n  TinyAPI server běží na http://{host}:{port}")

        # Připomeneme jak server zastavit
        print("  Pro zastavení stiskni Ctrl+C\n")

        # try/except zachytí KeyboardInterrupt (Ctrl+C od uživatele)
        try:
            # serve_forever() = nekonečná smyčka — server čeká na požadavky
            # Tato funkce se nevrátí dokud ji nepřerušíme
            httpd.serve_forever()

        # KeyboardInterrupt nastane když uživatel stiskne Ctrl+C
        except KeyboardInterrupt:
            # Vypíšeme zprávu a ukončíme (with blok zavře server automaticky)
            print("\n  Server zastaven.")
