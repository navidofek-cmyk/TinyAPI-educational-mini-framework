# ============================================================
# LEARNING CASE 4: Dependency Injection (Vkládání závislostí)
# ============================================================
# Co se naučíš:
#   - Co je Dependency Injection a proč je to super věc
#   - Jak funguje Depends() — automatické volání funkcí
#   - DRY princip: Don't Repeat Yourself (Neopakuj se)
#   - Jak závislosti mohou mít vlastní závislosti (matrioshka)
#
# Spusť:
#   uv run python examples/04_dependencies.py
#
# Pak vyzkoušej:
#   curl http://localhost:8888/profil
#   curl -H "Authorization: token-honza" http://localhost:8888/profil
#   curl -H "Authorization: token-honza" http://localhost:8888/tajne
#   curl -H "Authorization: token-anička" http://localhost:8888/tajne
#   curl http://localhost:8888/statistiky
# ============================================================

# Importujeme TinyAPI, Request a Depends z balíčku
from tinyapi import TinyAPI, Request, Depends

# Vytvoříme aplikaci
app = TinyAPI()


# ============================================================
# PROČ DEPENDENCY INJECTION?
# ============================================================
# BEZ DI — opakujeme stejný kód všude (špatně!):
#
#   @app.get("/profil")
#   def profil(request: Request):
#       token = request.headers.get("Authorization", "")  # opakování!
#       uzivatel = UZIVATELE_DB.get(token)                # opakování!
#       return uzivatel
#
#   @app.get("/nastaveni")
#   def nastaveni(request: Request):
#       token = request.headers.get("Authorization", "")  # opakování!
#       uzivatel = UZIVATELE_DB.get(token)                # opakování!
#       ...
#
# S DI — napíšeme kód jednou, framework ho spustí za nás:
#
#   @app.get("/profil")
#   def profil(uzivatel = Depends(get_current_user)):
#       return uzivatel  # čisté a jednoduché!
# ============================================================

# Falešná databáze uživatelů
# Token je jako heslo — prohlížeč ho posílá v hlavičce Authorization
UZIVATELE_DB = {
    "token-honza": {"id": 1, "jmeno": "Honza", "role": "admin"},
    "token-anička": {"id": 2, "jmeno": "Anička", "role": "user"},
}

# Falešná databáze s daty aplikace
DATABAZE = {
    "produkty": [{"id": 1, "nazev": "Jablko"}, {"id": 2, "nazev": "Banán"}],
    "nastaveni": {"barva": "modra", "jazyk": "cs"},
}


# ============================================================
# ZÁVISLOST 1: Připojení k databázi
# ============================================================
# Toto je normální Python funkce — žádná magie
# Framework ji zavolá automaticky když ji vidí v Depends()
def get_db() -> dict:
    # Simulujeme připojení k databázi (v reálu by byl engine, session...)
    print("  [DB] Vytvářím připojení k databázi...")

    # Vrátíme naši falešnou databázi
    return DATABAZE


# ============================================================
# ZÁVISLOST 2: Aktuální přihlášený uživatel
# ============================================================
# Tato závislost sama potřebuje Request!
# Framework to vyřeší automaticky — Depends může mít vlastní Depends.
# Je to jako matrioshka: Handler -> get_current_user -> Request
def get_current_user(request: Request) -> dict | None:
    # Přečteme token z hlavičky Authorization
    # .get() vrátí "" (prázdný string) pokud hlavička neexistuje
    token = request.headers.get("Authorization", "")

    # Zobrazíme co jsme dostali (jen pro vzdělávací účely)
    uzivatel = UZIVATELE_DB.get(token)
    print(f"  [Auth] Token: '{token}' -> Uživatel: {uzivatel}")

    # Vrátíme uživatele nebo None pokud token neznáme
    return uzivatel


# ============================================================
# ZÁVISLOST 3: Kontrola admin oprávnění
# ============================================================
# Tato závislost závisí na get_current_user!
# Framework vyřeší celý strom závislostí automaticky.
# Depends(get_current_user) -> get_current_user potřebuje Request -> framework dá Request
def require_admin(uzivatel=Depends(get_current_user)) -> dict:
    # Pokud uzivatel je None -> nejsi přihlášen
    if uzivatel is None:
        # PermissionError = chyba oprávnění
        raise PermissionError("Nejsi přihlášen!")

    # Pokud role není "admin" -> nemáš dost práv
    if uzivatel.get("role") != "admin":
        raise PermissionError(f"Nemáš admin práva! Tvoje role: {uzivatel['role']}")

    # Jsme admin -> vrátíme uživatele
    return uzivatel


# ============================================================
# ENDPOINTY POUŽÍVAJÍCÍ ZÁVISLOSTI
# ============================================================

# GET /profil — vidí každý (i nepřihlášený)
@app.get("/profil")
# Depends(get_current_user) = "zavolej get_current_user() a výsledek mi dej jako uzivatel"
def profil(uzivatel=Depends(get_current_user)):
    # Pokud uzivatel je None -> nejsi přihlášen
    if uzivatel is None:
        return {"chyba": "Nejsi přihlášen. Pošli hlavičku: Authorization: token-honza"}

    # Vrátíme data přihlášeného uživatele
    return {"profil": uzivatel}


# GET /tajne — pouze pro adminy
@app.get("/tajne")
# Dvě závislosti najednou! Framework vyřeší obě.
# admin = výsledek require_admin() — pokud selže, handler se ani nespustí
# db = výsledek get_db()
def tajne_stranky(admin=Depends(require_admin), db=Depends(get_db)):
    # Sem se dostaneme jen pokud require_admin() uspělo (jsme admin)
    return {
        # Uvítání s jménem admina
        "zprava": f"Vítej, {admin['jmeno']}! Toto je tajná stránka.",
        # Data z databáze
        "data": db["nastaveni"],
    }


# GET /statistiky — veřejné, jen potřebuje databázi
@app.get("/statistiky")
# Jen jedna závislost: get_db()
def statistiky(db=Depends(get_db)):
    # Vrátíme počet produktů
    return {
        "pocet_produktu": len(db["produkty"]),
        "zprava": "Statistiky jsou veřejné pro všechny.",
    }


# Spusť kód jen při přímém spuštění souboru
if __name__ == "__main__":

    print("=== Ukázka Dependency Injection ===")
    print()

    # Ukážeme přímé volání závislosti
    print("Přímé volání get_db():")
    print(" ", get_db())
    print()

    print("Framework za tebe zavolá závislosti automaticky.")
    print("Spouštím server...")
    print()

    # Spustíme server
    app.run()
