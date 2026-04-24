# Tento soubor popisuje co je RESPONSE (odpověď).
# Číšník se vrátí k zákazníkovi s jídlem — to je RESPONSE.
# Odpověď obsahuje:
#   - číslo (status_code): říká "jak to dopadlo"
#     200 = OK, všechno v pořádku
#     404 = Not Found, stránka neexistuje
#     500 = Chyba v serveru (chyba v kódu)
#   - tělo (body): samotná data (jídlo)
#   - hlavičky (headers): popis dat ("toto je JSON", "toto je obrázek")

# Importujeme modul json — umí převádět Python slovníky na JSON text a zpět
import json


# Slovník s popisky stavových kódů HTTP
# Každý číselný kód má svůj anglický název
# Je to jako slovník cizojazyčných výrazů
STATUS_TEXTS = {
    200: "OK",  # Vše v pořádku
    201: "Created",  # Nový záznam byl vytvořen
    204: "No Content",  # Odpověď nemá obsah
    400: "Bad Request",  # Špatně sestavená žádost
    401: "Unauthorized",  # Nejsi přihlášen
    403: "Forbidden",  # Nemáš oprávnění
    404: "Not Found",  # Stránka nenalezena
    422: "Unprocessable Entity",  # Data nejdou zpracovat (chybné parametry)
    500: "Internal Server Error",  # Chyba v kódu serveru
}


# Třída Response představuje jednu odpověď serveru
class Response:
    # __init__ se zavolá při vytvoření nové odpovědi
    # content = co chceme poslat (slovník, text, číslo...)
    # status_code = číslo stavu, výchozí 200 (OK)
    # headers = extra informace o odpovědi, výchozí None
    def __init__(self, content=None, status_code: int = 200, headers: dict = None):

        # Uložíme stavový kód
        self.status_code = status_code

        # Vytvoříme kopii slovníku headers (pokud existuje) nebo prázdný slovník
        # dict() s argumentem vytvoří KOPII — abychom nezměnili původní slovník
        # Bez kopie by změna self.headers změnila i původní headers — to nechceme!
        self.headers = dict(headers) if headers else {}

        # Teď musíme zjistit, co je content, a správně ho zakódovat do bytů
        # isinstance() zkontroluje typ proměnné — jako zeptat se "je toto číslo?"

        # Případ 1: content je slovník {} nebo seznam [] — převedeme na JSON
        if isinstance(content, (dict, list)):
            # json.dumps() převede Python slovník/seznam na JSON text (string)
            # ensure_ascii=False = zachovej česká písmena (á, é, í...) jako jsou
            # .encode("utf-8") převede text na bytes (bajty) — počítače pracují s bajty
            self.body = json.dumps(content, ensure_ascii=False).encode("utf-8")

            # Přidáme hlavičku Content-Type aby prohlížeč věděl "toto je JSON"
            # setdefault() přidá klíč jen pokud tam ještě není
            self.headers.setdefault("Content-Type", "application/json")

        # Případ 2: content je text (string) — zakódujeme ho
        elif isinstance(content, str):
            # .encode("utf-8") převede text na bytes
            self.body = content.encode("utf-8")

            # Říkáme prohlížeči "toto je prostý text, česky"
            self.headers.setdefault("Content-Type", "text/plain; charset=utf-8")

        # Případ 3: content jsou již hotové bytes — použijeme přímo
        elif isinstance(content, bytes):
            # Bytes jsou jako hotové zabalené jídlo — nemusíme nic dělat
            self.body = content

        # Případ 4: content je None (nic) — prázdná odpověď
        elif content is None:
            # b"" jsou prázdné bytes — jako prázdná krabička
            self.body = b""

        # Případ 5: cokoliv jiného — převedeme na text pomocí str()
        else:
            # str() převede cokoliv na textový řetězec
            # Například číslo 42 -> "42"
            self.body = str(content).encode("utf-8")

            # Nastavíme Content-Type na prostý text
            self.headers.setdefault("Content-Type", "text/plain; charset=utf-8")

    # @property — tato funkce se chová jako vlastnost (bez závorek při volání)
    @property
    def status_text(self) -> str:

        # .get() hledá klíč ve slovníku
        # Pokud klíč neexistuje, vrátí "Unknown" (druhý parametr)
        # Například STATUS_TEXTS.get(200, "Unknown") -> "OK"
        return STATUS_TEXTS.get(self.status_code, "Unknown")

    # __repr__ — popis objektu pro výpis
    def __repr__(self):

        # len(self.body) = počet bajtů v těle odpovědi
        # f-string = řetězec s proměnnými uvnitř {}
        return f"Response(status={self.status_code}, body_size={len(self.body)}B)"
