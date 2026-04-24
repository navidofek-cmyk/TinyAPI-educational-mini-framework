# ============================================================
# LEARNING CASE 7: JSON body — Posílání dat na server
# ============================================================
# Co se naučíš:
#   - Jak přijmout JSON data z těla (body) POST požadavku
#   - Jak vytvořit jednoduché CRUD operace (Create, Read, Update, Delete)
#   - Jak kombinovat path parametry + JSON body
#   - Co je REST API konvence
#
# Spusť:
#   uv run python examples/07_json_body.py
#
# Pak vyzkoušej:
#   curl http://localhost:8888/uzivatele
#   curl -X POST http://localhost:8888/uzivatele \
#        -H "Content-Type: application/json" \
#        -d '{"jmeno": "Karel", "vek": 11}'
#   curl http://localhost:8888/uzivatele/4
#   curl -X PUT http://localhost:8888/uzivatele/1 \
#        -H "Content-Type: application/json" \
#        -d '{"jmeno": "Honza Updated", "vek": 11}'
#   curl -X DELETE http://localhost:8888/uzivatele/1
# ============================================================

# Importujeme TinyAPI a Request z balíčku
from tinyapi import TinyAPI, Request

# Vytvoříme aplikaci
app = TinyAPI()


# ============================================================
# CRUD = Create, Read, Update, Delete
# Čtyři základní operace s daty — základ každé webové aplikace.
#
#   Create = POST   /uzivatele          (vytvoř nového)
#   Read   = GET    /uzivatele          (seznam všech)
#   Read   = GET    /uzivatele/{id}     (detail jednoho)
#   Update = PUT    /uzivatele/{id}     (aktualizuj celého)
#   Delete = DELETE /uzivatele/{id}     (smaž)
# ============================================================

# Naše "databáze" — seznam slovníků v paměti
# V reálné aplikaci by toto byl PostgreSQL, SQLite, MongoDB...
# int() vrátí číslo — id začínáme od 1
UZIVATELE: list[dict] = [
    {"id": 1, "jmeno": "Honza", "vek": 10},
    {"id": 2, "jmeno": "Anička", "vek": 12},
    {"id": 3, "jmeno": "Petr", "vek": 9},
]

# Počítadlo pro nová ID — každý nový uživatel dostane vyšší číslo
# Začínáme od 4 (1, 2, 3 jsou již použita výše)
next_id = 4


# ============================================================
# READ — Získání dat (GET)
# ============================================================


# GET /uzivatele — vrátí všechny uživatele
@app.get("/uzivatele")
# Jednoduchý handler bez parametrů
def seznam_uzivatelu():
    # Vrátíme celý seznam jako JSON pole
    return UZIVATELE


# GET /uzivatele/{id} — vrátí jednoho uživatele podle ID
@app.get("/uzivatele/{id}")
# id: int — framework převede string "1" na číslo 1
def get_uzivatel(id: int):
    # Projdeme seznam a hledáme uživatele s daným ID
    # next() vrátí první shodu, nebo None pokud nikdo nenajde
    uzivatel = next((u for u in UZIVATELE if u["id"] == id), None)

    # Pokud uživatel neexistuje, vrátíme chybu
    if uzivatel is None:
        return {"chyba": f"Uživatel {id} nenalezen"}

    # Vrátíme nalezeného uživatele
    return uzivatel


# ============================================================
# CREATE — Vytvoření nového záznamu (POST)
# ============================================================


# POST /uzivatele — vytvoří nového uživatele
@app.post("/uzivatele")
# Potřebujeme Request abychom mohli přečíst JSON tělo
def vytvor_uzivatele(request: Request):
    # global říká Pythonu: "next_id je globální proměnná, ne lokální"
    # Bez global bychom nemohli globální proměnnou měnit
    global next_id

    # Přečteme JSON data z těla požadavku
    # Tělo požadavku: '{"jmeno": "Karel", "vek": 11}'
    try:
        data = request.json()
    except Exception:
        # Pokud JSON není validní, vrátíme chybu
        return {"chyba": "Tělo požadavku musí být validní JSON"}

    # Zkontrolujeme povinná pole
    if "jmeno" not in data:
        return {"chyba": "Pole 'jmeno' je povinné"}
    if "vek" not in data:
        return {"chyba": "Pole 'vek' je povinné"}

    # Vytvoříme nového uživatele se všemi daty
    novy = {
        # Přiřadíme nové unikátní ID
        "id": next_id,
        # Vezmeme jméno z přijatých dat
        "jmeno": data["jmeno"],
        # int() zajistí že vek je číslo (ne text)
        "vek": int(data["vek"]),
    }

    # Přidáme uživatele do "databáze"
    UZIVATELE.append(novy)

    # Zvýšíme počítadlo pro příští ID
    next_id += 1

    # Vrátíme nového uživatele se status kódem 201 (Created)
    # Číslo 201 říká "byl vytvořen nový zdroj" — konvence REST API
    from tinyapi import Response

    return Response(novy, status_code=201)


# ============================================================
# UPDATE — Aktualizace záznamu (PUT)
# ============================================================


# PUT /uzivatele/{id} — aktualizuje celého uživatele
@app.put("/uzivatele/{id}")
# id: int z URL + celý request pro JSON tělo
def aktualizuj_uzivatele(id: int, request: Request):
    # Najdeme index uživatele v seznamu
    # enumerate() vrátí dvojice (index, hodnota)
    index = None
    for i, u in enumerate(UZIVATELE):
        if u["id"] == id:
            # Uložíme index a přestaneme hledat
            index = i
            break

    # Pokud jsme nic nenašli
    if index is None:
        return {"chyba": f"Uživatel {id} nenalezen"}

    # Přečteme nová data z JSON těla
    try:
        data = request.json()
    except Exception:
        return {"chyba": "Tělo požadavku musí být validní JSON"}

    # Aktualizujeme uživatele — zachováme původní ID
    UZIVATELE[index] = {
        # ID se nemění — vezmeme původní
        "id": id,
        # Nové jméno z dat, nebo původní pokud není v datech
        "jmeno": data.get("jmeno", UZIVATELE[index]["jmeno"]),
        # Nový věk z dat, nebo původní pokud není
        "vek": int(data.get("vek", UZIVATELE[index]["vek"])),
    }

    # Vrátíme aktualizovaného uživatele
    return UZIVATELE[index]


# ============================================================
# DELETE — Smazání záznamu (DELETE)
# ============================================================


# DELETE /uzivatele/{id} — smaže uživatele
@app.delete("/uzivatele/{id}")
# id: int — ID uživatele ke smazání
def smaz_uzivatele(id: int):
    # Zjistíme délku PŘED smazáním
    puvodni_pocet = len(UZIVATELE)

    # List comprehension = vytvoříme nový seznam BEZ uživatele s daným ID
    # Je to jako "dej mi všechny uživatele kromě toho s id=X"
    # Přiřazení do UZIVATELE[:] = nahradíme obsah seznamu (ne referenci)
    UZIVATELE[:] = [u for u in UZIVATELE if u["id"] != id]

    # Pokud se délka nezměnila, uživatel neexistoval
    if len(UZIVATELE) == puvodni_pocet:
        return {"chyba": f"Uživatel {id} nenalezen"}

    # Vrátíme potvrzení smazání se status 200
    return {"zprava": f"Uživatel {id} byl smazán"}


# Spusť kód jen při přímém spuštění souboru
if __name__ == "__main__":
    print("=== TinyAPI — CRUD příklad ===")
    print()
    print("Dostupné endpointy:")
    print("  GET    /uzivatele          -> seznam všech")
    print("  GET    /uzivatele/{id}     -> jeden uživatel")
    print("  POST   /uzivatele          -> vytvoř nového (JSON body)")
    print("  PUT    /uzivatele/{id}     -> aktualizuj (JSON body)")
    print("  DELETE /uzivatele/{id}     -> smaž")
    print()

    # Spustíme server
    app.run()
