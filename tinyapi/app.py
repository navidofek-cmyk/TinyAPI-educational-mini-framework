# Tento soubor obsahuje hlavní třídu TinyAPI — "mozek" celého frameworku.
# Spojuje dohromady všechny ostatní části:
# Router (nalezení správné funkce) + Params (naplnění argumentů) +
# Request (příchozí žádost) + Response (odchozí odpověď)
#
# Životní cyklus jednoho HTTP požadavku:
#
#   Prohlížeč pošle: "GET /uzivatele/42"
#        |
#        v
#   server.py vytvoří objekt Request
#        |
#        v
#   app.py najde správnou Route v routeru
#        |
#        v
#   params.py zjistí co handler potřebuje a naplní argumenty
#        |
#        v
#   Tvůj handler se zavolá: get_uzivatel(id=42)
#        |
#        v
#   app.py zabalí výsledek do Response
#        |
#        v
#   Prohlížeč dostane odpověď: {"id": 42, "jmeno": "Honza"}

# asyncio = modul pro asynchronní programování
# async/await umožňuje serveru zpracovávat více požadavků "najednou"
import asyncio

# Importujeme naše vlastní třídy z ostatních souborů
# Tečka . před názvem = relativní import (soubory ve stejné složce)
from .routing import Router
from .request import Request
from .response import Response
from .params import resolve_handler_params


# Hlavní třída celého frameworku
class TinyAPI:

    # __init__ se zavolá při vytvoření: app = TinyAPI()
    def __init__(self):

        # Vytvoříme Router — bude uchovávat všechny zaregistrované URL cesty
        self.router = Router()

        # _middleware je seznam funkcí které se spustí před KAŽDÝM požadavkem
        # Podtržítko _ = "interní proměnná, nepoužívej přímo zvenku"
        # list = seznam, začínáme prázdným []
        self._middleware: list = []

        # Vytvoříme zkratky — aby šlo psát app.get() místo app.router.get()
        # Toto jsou přímé reference na metody routeru (ne kopie!)
        # Změna v routeru se projeví i přes tyto zkratky
        self.get = self.router.get
        self.post = self.router.post
        self.put = self.router.put
        self.delete = self.router.delete
        self.patch = self.router.patch

    # middleware je dekorátor pro registraci middleware funkcí
    # Použití: @app.middleware
    # func = funkce která se má spustit před každým požadavkem
    def middleware(self, func):

        # Přidáme funkci do seznamu middleware
        self._middleware.append(func)

        # Vrátíme funkci beze změny (jako každý správný dekorátor)
        return func

    # handle_request zpracuje jeden HTTP požadavek a vrátí odpověď
    # Je to async funkce — může "čekat" aniž by blokovala ostatní požadavky
    # request = příchozí požadavek od prohlížeče
    # -> Response = vrátí objekt Response
    async def handle_request(self, request: Request) -> Response:

        # KROK 1: Spusť všechny middleware funkce
        # Například: zaloguj požadavek, zkontroluj přihlášení...
        for mw_func in self._middleware:

            # Zkontrolujeme jestli je middleware funkce async nebo normální
            if asyncio.iscoroutinefunction(mw_func):

                # async middleware — musíme await
                await mw_func(request)

            else:

                # normální middleware — zavoláme přímo
                mw_func(request)

        # KROK 2: Najdi Route která odpovídá URL a metodě požadavku
        # resolve() vrátí dvojici (route, parametry) nebo (None, {})
        route, path_params = self.router.resolve(request.path, request.method)

        # Pokud route je None — žádná cesta neodpovídá
        if route is None:

            # Vrátíme odpověď 404 Not Found
            # Slovník se automaticky převede na JSON
            return Response(
                {"chyba": f"Stránka '{request.path}' neexistuje"},
                status_code=404
            )

        # KROK 3: Zjisti co handler potřebuje a naplň parametry
        # try/except zachytí chybu pokud chybí povinný parametr
        try:

            # resolve_handler_params je async — musíme await
            # Vrátí slovník jako: {"id": 42, "jmeno": "Honza"}
            kwargs = await resolve_handler_params(route.handler, request, path_params)

        # TypeError nastane když chybí povinný parametr
        except TypeError as e:

            # 422 = Unprocessable Entity (nelze zpracovat — chybné parametry)
            return Response({"chyba": str(e)}, status_code=422)

        # KROK 4: Zavolej handler (funkci) s připravenými argumenty
        # try/except zachytí libovolnou chybu v kódu handleru
        try:

            # Zkontrolujeme jestli je handler async nebo normální funkce
            if asyncio.iscoroutinefunction(route.handler):

                # async handler — musíme await
                # **kwargs = "rozbal slovník jako pojmenované argumenty"
                result = await route.handler(**kwargs)

            else:

                # normální handler — zavoláme přímo
                result = route.handler(**kwargs)

        # Exception zachytí JAKOUKOLI chybu (nejobecnější typ chyby)
        except Exception as e:

            # 500 = Internal Server Error (chyba v kódu)
            return Response({"chyba": f"Interní chyba: {str(e)}"}, status_code=500)

        # KROK 5: Zabal výsledek do Response (pokud ještě není)
        # Pokud handler vrátil přímo Response objekt — použijeme ho
        if isinstance(result, Response):

            # Handler vrátil Response přímo -> použijeme beze změny
            return result

        # Handler vrátil dict, str, číslo... -> zabalíme do Response
        return Response(result)

    # run() spustí HTTP server na daném hostu a portu
    # host = IP adresa na které server poslouchá
    # "0.0.0.0" = všechna síťová rozhraní (dostupný z celé sítě)
    # port = číslo portu (jako číslo bytu v domě)
    def run(self, host: str = "0.0.0.0", port: int = 8888):

        # Importujeme run_server funkci ze souboru server.py
        # Import tady (ne nahoře) = načteme server.py až když ho potřebujeme
        from .server import run_server

        # Zavoláme run_server a předáme mu sebe (app) + host + port
        run_server(self, host, port)

    # __repr__ — popis objektu pro výpis
    def __repr__(self):

        # Vrátíme popis včetně obsahu routeru
        return f"TinyAPI(\n{self.router}\n)"
