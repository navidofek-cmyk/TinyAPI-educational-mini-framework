# ============================================================
# LEARNING CASE 1: Dekorátory a základní routing
# ============================================================
# Co se naučíš:
#   - Co jsou dekorátory (@) a jak fungují v Pythonu
#   - Jak zaregistrovat funkci jako HTTP handler (obsluhu stránky)
#   - Jak vrátit různé typy odpovědí (slovník, text)
#
# Spusť:
#   uv run python examples/01_hello_world.py
#
# Pak v jiném terminálu vyzkoušej:
#   curl http://localhost:8888/
#   curl http://localhost:8888/ahoj
#   curl http://localhost:8888/info
# ============================================================

# Importujeme třídu TinyAPI z našeho balíčku tinyapi
from tinyapi import TinyAPI

# Vytvoříme instanci (konkrétní objekt) třídy TinyAPI
# app je naše webová aplikace
app = TinyAPI()


# ============================================================
# JAK FUNGUJÍ DEKORÁTORY?
# ============================================================
# Tento zápis:
#
#   @app.get("/")
#   def domov():
#       return "Ahoj!"
#
# Je PŘESNĚ STEJNÝ jako:
#
#   def domov():
#       return "Ahoj!"
#   domov = app.get("/")(domov)   <- zaregistruje a vrátí funkci zpět
#
# Kroky:
# 1. app.get("/") se zavolá -> vrátí funkci (dekorátor)
# 2. Dekorátor dostane funkci domov jako argument
# 3. Zaregistruje domov pro GET /
# 4. Vrátí domov beze změny
# ============================================================

# @app.get("/") říká: "tato funkce obsluhuje GET požadavky na /"
@app.get("/")
# Funkce domov se zavolá když někdo navštíví http://server:8888/
def domov():
    # Vrátíme slovník -> TinyAPI ho automaticky převede na JSON
    # JSON je formát dat pro internet: {"klic": "hodnota"}
    return {"zprava": "Vítej v TinyAPI!", "verze": "0.1"}


# Registrujeme cestu /ahoj
@app.get("/ahoj")
# Funkce pozdrav obsluhuje GET /ahoj
def pozdrav():
    # Vrátíme prostý text (string) — ne jen slovník
    return "Ahoj z TinyAPI serveru!"


# Registrujeme cestu /info
@app.get("/info")
# Funkce info obsluhuje GET /info
def info():
    # Importujeme modul sys — obsahuje informace o Python prostředí
    import sys
    # Vrátíme více informací najednou
    return {
        # Název frameworku
        "framework": "TinyAPI",
        # sys.version = text jako "3.12.3 (main, ...)"
        "python": sys.version,
        # Seznam všech dostupných cest
        "endpoints": ["/", "/ahoj", "/info"],
    }


# ============================================================
# KLÍČOVÁ VĚTA: Dekorátor funkci NEZMĚNÍ — jen ji zaregistruje!
# domov() funguje normálně i bez serveru.
# ============================================================

# Tento blok se spustí jen když soubor spustíš přímo
# Pokud ho někdo importuje (import 01_hello_world), kód se nespustí
if __name__ == "__main__":

    # Ukážeme že funkce fungují i bez serveru
    print("=== Test bez serveru ===")

    # Zavoláme funkci přímo jako normální Python funkci
    print("domov()   ->", domov())
    # Zavoláme pozdrav()
    print("pozdrav() ->", pozdrav())
    print()

    # Zobrazíme všechny zaregistrované cesty (routes)
    print("=== Zaregistrované routes ===")
    # app.router.__repr__() pěkně vypíše všechny routes
    print(app.router)
    print()

    # Spustíme HTTP server — tato funkce se nevrátí (běží stále)
    # Server poslouchá na 0.0.0.0:8888
    app.run()
