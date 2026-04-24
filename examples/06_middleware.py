# ============================================================
# LEARNING CASE 6: Middleware — Kód kolem každého požadavku
# ============================================================
# Co se naučíš:
#   - Co je middleware a k čemu se používá
#   - Jak funguje dekorátor @app.middleware
#   - Jak přidat logování, měření, nebo autentizaci pro všechny cesty
#
# Spusť:
#   uv run python examples/06_middleware.py
#
# Pak vyzkoušej (a koukni na výstup v terminálu serveru!):
#   curl http://localhost:8888/
#   curl http://localhost:8888/info
#   curl http://localhost:8888/hlavicky
# ============================================================

# Importujeme time pro práci s časem
import time

# Importujeme TinyAPI a Request
from tinyapi import TinyAPI, Request

# Vytvoříme aplikaci
app = TinyAPI()


# ============================================================
# CO JE MIDDLEWARE?
# ============================================================
# Middleware = kód který obaluje KAŽDÝ příchozí požadavek.
# Je to jako bezpečnostní brána na letišti:
#   Každý cestující (požadavek) musí projít kontrolou (middleware)
#   PŘED tím než nastoupí na palubu (handler).
#
# Příklady použití:
#   Logování    = zapiš každý požadavek do souboru
#   Autentizace = zkontroluj přihlášení před každým endpointem
#   Měření času = zjisti jak dlouho zpracování trvalo
#   CORS        = přidej hlavičky pro cross-origin požadavky
#   Rate limit  = omez počet požadavků za minutu
# ============================================================


# @app.middleware zaregistruje funkci jako middleware
@app.middleware
# Funkce dostane Request a zavolá se před KAŽDÝM požadavkem
def loguj_requesty(request: Request):
    # time.strftime() formátuje čas jako text
    # "%H:%M:%S" = hodiny:minuty:sekundy (například "14:35:22")
    cas = time.strftime("%H:%M:%S")

    # Zalogujeme příchozí požadavek (metoda + cesta)
    print(f"  [{cas}] PŘÍCHOZÍ: {request.method} {request.path}")

    # Pokud jsou query parametry, zalogujeme i je
    if request.query_params:
        print(f"  [{cas}] PARAMS:   {request.query_params}")

    # Middleware nevrací nic — jen "projde" a předá štafetu dál


# Druhý middleware — přidá vlastní hlavičky do requestu
@app.middleware
# Tato funkce se zavolá po první (loguj_requesty)
def pridej_hlavicky(request: Request):
    # Do slovníku headers přidáme vlastní klíče
    # X- prefix = nestandardní hlavičky (konvence)
    request.headers["X-Framework"] = "TinyAPI"

    # id(request) vrátí unikátní číslo objektu — jako rodné číslo pro každý request
    # str() převede číslo na text (hlavičky musí být text)
    request.headers["X-Request-Id"] = str(id(request))


# ============================================================
# ENDPOINTY
# ============================================================


# GET / — jednoduchá uvítací stránka
@app.get("/")
# Tento handler se zavolá po obou middleware funkcích
def domov():
    return {"zprava": "Ahoj! Koukni na terminál — middleware loguje každý požadavek."}


# GET /hlavicky — ukáže hlavičky přidané middlewarem
@app.get("/hlavicky")
# Potřebujeme Request abychom viděli hlavičky
def ukaz_hlavicky(request: Request):
    # Vrátíme slovník hlaviček — uvidíš i ty přidané middlewarem
    return {"hlavicky": request.headers}


# GET /info — ukáže data která přidal middleware
@app.get("/info")
# Opět potřebujeme Request pro přístup k hlavičkám
def info(request: Request):
    return {
        # Hlavička přidaná middlewarem pridej_hlavicky
        "framework": request.headers.get("X-Framework"),
        # Unikátní ID přidané middlewarem
        "request_id": request.headers.get("X-Request-Id"),
        # Vysvětlení
        "zprava": "Tato data přidal middleware automaticky!",
    }


# Spusť kód jen při přímém spuštění souboru
if __name__ == "__main__":
    print("=== Spouštím server s middleware ===")
    print("Každý požadavek bude logován v tomto terminálu.")
    print()

    # Spustíme server
    app.run()
