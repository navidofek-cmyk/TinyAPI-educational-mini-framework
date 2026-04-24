# ============================================================
# LEARNING CASE 2: Path parametry a typová konverze
# ============================================================
# Co se naučíš:
#   - Jak fungují {parametry} v URL adrese
#   - Jak type hints (: int, : str) říkají frameworku jak převést data
#   - Jak funguje modul inspect (rentgen pro funkce)
#   - Proč URL parametry jsou vždy text a jak je převést na číslo
#
# Spusť:
#   uv run python examples/02_path_params.py
#
# Pak vyzkoušej:
#   curl http://localhost:8888/uzivatele/1
#   curl http://localhost:8888/uzivatele/2
#   curl http://localhost:8888/nasobit/6/7
#   curl http://localhost:8888/produkty/jablko/cena
# ============================================================

# Importujeme inspect — modul pro "rentgenování" funkcí
# Umí zjistit parametry funkce, jejich typy, výchozí hodnoty
import inspect

# Importujeme TinyAPI z našeho balíčku
from tinyapi import TinyAPI

# Vytvoříme aplikaci
app = TinyAPI()


# ============================================================
# JAK FUNGUJÍ PATH PARAMETRY?
# ============================================================
# URL vzor:  /uzivatele/{id}
# Skutečná URL: /uzivatele/42
#
# Framework přeloží vzor na regulární výraz:
#   /uzivatele/(?P<id>[^/]+)
#   (?P<id>...) = pojmenovaná skupina — zachytí cokoliv a pojmenuje to "id"
#   [^/]+ = jeden nebo více znaků které nejsou lomítko
#
# Výsledek: {"id": "42"}   <- VŽDY STRING (text)!
#
# Type hint `id: int` říká frameworku: "převeď "42" na číslo 42"
# ============================================================

# Falešná databáze uživatelů — slovník místo skutečné databáze
# Klíče jsou čísla (int), hodnoty jsou slovníky s daty
UZIVATELE = {
    1: {"id": 1, "jmeno": "Honza", "vek": 10},
    2: {"id": 2, "jmeno": "Anička", "vek": 12},
    3: {"id": 3, "jmeno": "Petr", "vek": 9},
}

# Falešná databáze produktů — klíče jsou textové názvy
PRODUKTY = {
    "jablko": {"nazev": "Jablko", "cena": 5.50},
    "banan": {"nazev": "Banán", "cena": 3.00},
}


# Registrujeme cestu s parametrem {id}
@app.get("/uzivatele/{id}")
# Parametr id: int říká "chci celé číslo" — framework převede "42" -> 42
def get_uzivatel(id: int):
    # .get() hledá klíč ve slovníku, vrátí None pokud nenajde
    uzivatel = UZIVATELE.get(id)

    # Pokud uživatel neexistuje, vrátíme chybovou zprávu
    if uzivatel is None:
        # Vrátíme slovník s chybou — bude jako JSON
        return {"chyba": f"Uživatel s id={id} neexistuje"}

    # Vrátíme nalezený slovník uživatele
    return uzivatel


# URL může mít segment uprostřed — parametr {nazev} je mezi /produkty/ a /cena
@app.get("/produkty/{nazev}/cena")
# Parametr nazev: str — chceme text (string), bez konverze
def cena_produktu(nazev: str):
    # Hledáme produkt podle názvu
    produkt = PRODUKTY.get(nazev)

    # Pokud produkt nenajdeme
    if produkt is None:
        return {"chyba": f"Produkt '{nazev}' nenalezen"}

    # Vrátíme název a cenu
    return {"produkt": nazev, "cena": produkt["cena"]}


# Více parametrů v jedné URL — {a} a {b} jsou obě celá čísla
@app.get("/nasobit/{a}/{b}")
# Oba parametry jsou int — framework převede oba z textu na čísla
def nasob(a: int, b: int):
    # Vrátíme výsledek násobení s pěkným popisem
    return {"vysledek": a * b, "vypocet": f"{a} × {b} = {a * b}"}


# ============================================================
# UKÁZKA INTROSPEKCE — jak framework "vidí" funkci
# ============================================================
if __name__ == "__main__":
    # Ukážeme jak inspect "vidí" naši funkci
    print("=== Introspekce funkce get_uzivatel ===")

    # inspect.signature() vrátí podpis funkce — popis parametrů
    sig = inspect.signature(get_uzivatel)

    # .parameters je slovník všech parametrů funkce
    for name, param in sig.parameters.items():
        # Vypíšeme každý parametr a jeho vlastnosti
        print(f"  Parametr: '{name}'")

        # param.annotation je typová anotace (int, str...)
        # inspect.Parameter.empty = žádná anotace
        print(f"    typ:     {param.annotation}")

        # param.default je výchozí hodnota parametru
        print(f"    default: {param.default}")
        print()

    # Ukážeme přímé volání bez serveru
    print("=== Přímé volání (bez serveru) ===")
    # Zavoláme jako normální funkce — parametry předáme ručně
    print("get_uzivatel(1) ->", get_uzivatel(1))
    print("get_uzivatel(99)->", get_uzivatel(99))
    print("nasob(6, 7)     ->", nasob(6, 7))
    print()

    # Spustíme server
    app.run()
