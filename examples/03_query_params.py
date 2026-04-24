# ============================================================
# LEARNING CASE 3: Query parametry, POST a Request objekt
# ============================================================
# Co se naučíš:
#   - Co jsou query parametry (část URL za otazníkem ?klic=hodnota)
#   - Jak posílat data na server pomocí POST
#   - Jak přistoupit k celému Request objektu
#   - Jak fungují výchozí hodnoty parametrů
#
# Spusť:
#   uv run python examples/03_query_params.py
#
# Pak vyzkoušej:
#   curl http://localhost:8888/produkty
#   curl "http://localhost:8888/produkty?min_cena=3&max_cena=6"
#   curl "http://localhost:8888/hledat?dotaz=ja"
#   curl -X POST http://localhost:8888/echo -H "Content-Type: application/json" -d '{"text":"Ahoj!"}'
# ============================================================

# Importujeme TinyAPI a Request z našeho balíčku
from tinyapi import TinyAPI, Request

# Vytvoříme aplikaci
app = TinyAPI()

# Falešná databáze produktů — seznam slovníků
# Každý produkt má id (číslo), nazev (text) a cena (desetinné číslo)
PRODUKTY = [
    {"id": 1, "nazev": "Jablko",  "cena": 5.50},
    {"id": 2, "nazev": "Banán",   "cena": 3.00},
    {"id": 3, "nazev": "Jahoda",  "cena": 8.00},
    {"id": 4, "nazev": "Malina",  "cena": 12.00},
    {"id": 5, "nazev": "Hruška",  "cena": 4.50},
]


# ============================================================
# QUERY PARAMETRY — část URL za otazníkem
# ============================================================
# URL: /produkty?min_cena=3&max_cena=6
#         ^path    ^query string
#
# Jak framework pozná že "min_cena" je query parametr a ne path parametr?
# Jednoduše: není v {} ve vzoru cesty -> hledáme za otazníkem v URL.
#
# Výchozí hodnoty (= 0.0 a = 999.0):
# Pokud parametr není v URL, použije se výchozí hodnota.
# ============================================================

# Registrujeme GET /produkty
@app.get("/produkty")
# min_cena: float = 0.0   -> pokud není v URL, použij 0.0
# max_cena: float = 999.0 -> pokud není v URL, použij 999.0
def seznam_produktu(min_cena: float = 0.0, max_cena: float = 999.0):
    # List comprehension = zkrácený způsob vytvoření seznamu s podmínkou
    # [p for p in PRODUKTY if podminka] = vezmi každé p ze seznamu pokud platí podmínka
    filtrovane = [p for p in PRODUKTY if min_cena <= p["cena"] <= max_cena]

    # Vrátíme filtrovaný seznam a počet nalezených produktů
    return {"produkty": filtrovane, "pocet": len(filtrovane)}


# Registrujeme GET /hledat
@app.get("/hledat")
# dotaz: str  -> POVINNÝ parametr (bez výchozí hodnoty) — MUSÍ být v URL
# limit: int = 10 -> VOLITELNÝ (výchozí 10)
def hledat(dotaz: str, limit: int = 10):
    # Filtrujeme produkty kde název obsahuje hledaný dotaz
    # .lower() převede na malá písmena — hledání bez rozlišení velikosti
    # "in" zkontroluje jestli je dotaz obsažen v názvu
    nalezene = [p for p in PRODUKTY if dotaz.lower() in p["nazev"].lower()]

    # Vrátíme max "limit" výsledků pomocí slice [:limit]
    # [:10] = vezmi prvních 10 prvků
    return {"vysledky": nalezene[:limit], "celkem": len(nalezene)}


# ============================================================
# REQUEST OBJEKT — přístup k celé žádosti
# ============================================================
# Pokud handler chce celý Request, přidá parametr s type hintem Request.
# Framework pozná typ Request a předá celý objekt (ne hledá v URL).
# ============================================================

# Registrujeme GET /debug
@app.get("/debug")
# request: Request -> framework předá celý objekt žádosti
def debug_request(request: Request):
    # Vrátíme vše co víme o příchozím požadavku
    return {
        # HTTP metoda: GET, POST...
        "metoda": request.method,
        # Cesta URL
        "cesta": request.path,
        # Parametry za otazníkem (slovník)
        "query_params": request.query_params,
        # HTTP hlavičky (informace o prohlížeči, formátu dat...)
        "hlavicky": request.headers,
    }


# Registrujeme POST /echo
@app.post("/echo")
# request: Request -> potřebujeme celý objekt abychom přečetli tělo (body)
def echo(request: Request):
    # try/except = zkus, a pokud to selže, zachyť chybu
    try:
        # .json() přečte tělo POST požadavku jako Python slovník
        # Tělo je JSON text: '{"text": "Ahoj!"}'
        data = request.json()

        # Vrátíme přijatá data zpět (echo = ozvěna)
        return {"prijato": data, "zprava": "Data přijata v pořádku"}

    # Exception zachytí libovolnou chybu (špatný JSON formát apod.)
    except Exception:
        return {"chyba": "Body není validní JSON"}


# Spusť kód jen při přímém spuštění souboru
if __name__ == "__main__":

    # Ukázka přímého volání bez serveru
    print("=== Test bez serveru ===")

    # Zavoláme bez parametrů -> použijí se výchozí hodnoty
    print("seznam_produktu()           ->", seznam_produktu())

    # Zavoláme s min_cena -> filtruje produkty
    print("seznam_produktu(min_cena=4) ->", seznam_produktu(min_cena=4))

    # Hledáme produkty obsahující "ja" v názvu
    print("hledat('ja')               ->", hledat("ja"))
    print()

    # Spustíme server
    app.run()
