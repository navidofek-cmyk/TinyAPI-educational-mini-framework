# ============================================================
# LEARNING CASE 5: Async/Await — Asynchronní programování
# ============================================================
# Co se naučíš:
#   - Co je asynchronní programování a proč existuje
#   - Rozdíl mezi sync (synchronní) a async (asynchronní) funkcemi
#   - Jak async umožňuje obsloužit více požadavků najednou
#   - Co jsou coroutines (korutiny)
#   - Jak asyncio.gather() spustí více věcí paralelně
#
# Spusť:
#   uv run python examples/05_async.py
#
# Pak vyzkoušej:
#   curl http://localhost:8888/rychly
#   curl http://localhost:8888/pomaly
#   curl http://localhost:8888/paralelni
# ============================================================

# asyncio = modul pro asynchronní programování
# Obsahuje: sleep, gather, run, iscoroutinefunction a mnoho dalšího
import asyncio

# time = modul pro práci s časem
# time.time() = aktuální čas v sekundách (jako stopky)
# time.sleep() = BLOKUJÍCÍ čekání (zastaví vše!)
import time

# Importujeme TinyAPI
from tinyapi import TinyAPI

# Vytvoříme aplikaci
app = TinyAPI()


# ============================================================
# SYNC vs ASYNC — Analogie z restaurace
# ============================================================
# SYNCHRONNÍ (sync) = jeden pokladní v obchodě:
#   Zákazník 1: přijde, zaplatí, odejde (2 minuty)
#   Zákazník 2: ČEKÁ celou dobu (i když pokladní jen stojí)
#   Zákazník 3: ČEKÁ celou dobu
#   -> Pomalé, zákazníci naštvaní
#
# ASYNCHRONNÍ (async) = číšník v restauraci:
#   Zákazník 1: přijde, objedná -> číšník jde jinam
#   Zákazník 2: přijde, objedná -> číšník jde jinam
#   Zákazník 3: přijde, objedná -> číšník jde jinam
#   (kuchyně vaří paralelně, číšník nosí jídla jak jsou hotová)
#   -> Rychlé, zákazníci spokojení
# ============================================================


# Async pomocná funkce — simuluje pomalou databázi
# async def = tato funkce je asynchronní (coroutine)
async def simuluj_databazi(dotaz: str, cas: float) -> dict:
    # asyncio.sleep() = neblokující čekání
    # Řekne Pythonu: "Počkej X sekund, ale mezitím dělej jiné věci"
    # NAROZDÍL od time.sleep() které zastaví celý program!
    await asyncio.sleep(cas)

    # Po uplynutí času vrátíme výsledek
    return {"dotaz": dotaz, "vysledek": "data z databaze", "cas_s": cas}


# GET /rychly — okamžitá odpověď
@app.get("/rychly")
# async def = handler je asynchronní
# Použijeme async i pro jednoduché handlery — je to dobrý zvyk
async def rychly_endpoint():
    # Okamžitě vrátíme odpověď — žádné čekání
    return {"zprava": "Odpovím okamžitě!", "cas_s": 0}


# GET /pomaly — čeká 2 sekundy (ale neblokuje server!)
@app.get("/pomaly")
# async def — handler je asynchronní, může čekat
async def pomaly_endpoint():
    # Vypíšeme informaci (viditelné v terminálu kde běží server)
    print("  Čekám na databázi... (2 sekundy)")

    # await = "počkej na výsledek, ale nechej ostatní pracovat"
    # simuluj_databazi() je async -> musíme použít await
    data = await simuluj_databazi("SELECT * FROM produkty", 2.0)

    # Vrátíme odpověď po 2 sekundách čekání
    return {"zprava": "Hotovo po 2 sekundách", "data": data}


# GET /sync-pomaly — ŠPATNÝ příklad (blokuje server)
@app.get("/sync-pomaly")
# POZOR: toto je normální (sync) funkce s time.sleep
# Blokuje celý server — žádný jiný požadavek nemůže být zpracován!
def sync_pomaly_endpoint():
    # Vypíšeme varování
    print("  BLOKUJI celý server na 2 sekundy!")

    # time.sleep() = BLOKUJÍCÍ čekání — celý program stojí
    time.sleep(2)

    # Vrátíme odpověď
    return {"zprava": "Hotovo, ale server byl 2s zablokován!"}


# GET /paralelni — kouzlo asyncio.gather()
@app.get("/paralelni")
# async = tento handler je asynchronní
async def paralelni_endpoint():
    # Zaznamenáme čas začátku
    print("  Spouštím dva dotazy paralelně...")

    # time.time() vrátí aktuální čas v sekundách od roku 1970
    start = time.time()

    # asyncio.gather() spustí VÍCE coroutines NAJEDNOU (paralelně)
    # Bez gather: 1.5s + 2.0s = 3.5 sekundy celkem
    # S gather:   max(1.5s, 2.0s) = 2.0 sekundy  <- rychlejší!
    vysledek1, vysledek2 = await asyncio.gather(
        # První dotaz — trvá 1.5 sekundy
        simuluj_databazi("SELECT uzivatele", 1.5),
        # Druhý dotaz — trvá 2.0 sekundy (běží ZÁROVEŇ s prvním)
        simuluj_databazi("SELECT produkty", 2.0),
    )

    # Vypočítáme kolik času uběhlo
    elapsed = time.time() - start

    # Vrátíme výsledky a informaci o čase
    return {
        # Zaokrouhlíme na 1 desetinné místo pomocí :.1f
        "cas_celkem": f"{elapsed:.1f}s (místo {1.5 + 2.0}s)",
        "vysledky": [vysledek1, vysledek2],
    }


# Demo bez serveru — ukáže async/await v akci
# Musí být async def protože používá await uvnitř
async def demo():
    print("=== Demo: async/await bez serveru ===")
    print()

    # Příklad 1: Jednoduchý await
    print("1. Await jedné coroutine (čeká 0.3s):")

    # await = "počkej na výsledek" — podobné jako volání normální funkce
    result = await simuluj_databazi("SELECT 1", 0.3)
    print(f"   Výsledek: {result}")
    print()

    # Příklad 2: Paralelní gather
    print("2. Paralelní gather (mělo by trvat ~0.5s, ne ~1.0s):")

    # Zaznamenáme čas
    start = time.time()

    # Spustíme dva dotazy najednou — každý trvá 0.5s
    r1, r2 = await asyncio.gather(
        simuluj_databazi("dotaz A", 0.5),
        simuluj_databazi("dotaz B", 0.5),
    )

    # Zobrazíme kolik to trvalo
    print(f"   Trvalo: {time.time() - start:.1f}s (ne {0.5 + 0.5}s)")
    print()


# Spusť kód jen při přímém spuštění souboru
if __name__ == "__main__":
    # asyncio.run() spustí async funkci z normálního (sync) kódu
    # Je to "vstupní brána" do async světa
    asyncio.run(demo())

    # Spustíme HTTP server
    app.run()
