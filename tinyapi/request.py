# Tento soubor popisuje co je REQUEST (žádost).
# Představ si, že jsi číšník v restauraci.
# Zákazník přijde a řekne: "Chci pizzu číslo 3, extra sýr."
# To je REQUEST — zákazník tě o něco žádá.
# Na internetu: Prohlížeč řekne serveru: "Chci stránku /uzivatele/42"

# Importujeme funkci parse_qs z modulu urllib.parse.
# urllib.parse je jako slovníček, který umí rozluštit části URL adresy.
# parse_qs umí rozebrat část URL za otazníkem: "?jmeno=Honza&vek=10"
from urllib.parse import parse_qs


# Vytváříme třídu (class) Request.
# Třída je jako šablona (forma na sušenky) — z jedné formy uděláš mnoho sušenek.
# Z třídy Request uděláme jeden objekt pro každou příchozí žádost od prohlížeče.
class Request:
    # __init__ je speciální funkce, která se zavolá vždy když vytvoříme nový Request.
    # Je to jako "nastavení nové sušenky" — určíme barvu, tvar, posyp.
    # self = odkaz na tuto konkrétní sušenku (objekt), ne na formu (třídu)
    # method = typ žádosti: "GET" (chci dostat), "POST" (chci poslat), "DELETE" (chci smazat)
    # path = adresa stránky: "/uzivatele", "/produkty/42"
    # query_string = část URL za otazníkem: "jmeno=Honza&vek=10" (výchozí prázdný řetězec)
    # body = obsah zprávy (data poslaná u POST žádostí), výchozí prázdné bytes b""
    # headers = extra informace o žádosti (jako popisek na obálce), výchozí None
    def __init__(
        self,
        method: str,
        path: str,
        query_string: str = "",
        body: bytes = b"",
        headers: dict = None,
    ):

        # Uložíme metodu VELKÝMI PÍSMENY (GET, POST...) — .upper() převede na velká
        # Například "get" se stane "GET", aby bylo vše jednotné
        self.method = method.upper()

        # Uložíme cestu (path) — například "/uzivatele/42"
        # self.path znamená: "tato sušenka má vlastnost path"
        self.path = path

        # Uložíme hlavičky (headers). Jsou to extra informace jako "jsem Firefox" nebo "posílám JSON"
        # Pokud headers je None (nic), použijeme prázdný slovník {}
        # "or" funguje jako: "vezmi headers, ale pokud je None, vezmi místo toho {}"
        self.headers = headers or {}

        # Uložíme tělo zprávy (body) — data poslaná prohlížečem
        # Podtržítko _body říká: "tato proměnná je interní, nepoužívej ji přímo zvenku"
        self._body = body

        # Uložíme query_string — část URL za otazníkem
        # Například z "localhost:8888/hledat?slovo=pes" je query_string = "slovo=pes"
        self._query_string = query_string

        # Nastavíme _query_params na None (prázdno)
        # Parsovat (rozebrat) query string budeme až když to někdo opravdu potřebuje
        # Proč? Aby jsme nedělali práci zbytečně — jako nevařit oběd pro případ, že možná přijde host
        self._query_params = None

    # @property je dekorátor — mění funkci na vlastnost
    # Díky tomu píšeme request.query_params (jako vlastnost) místo request.query_params() (jako funkci)
    # Je to jako říct "výška stromu" místo "změř výšku stromu"
    @property
    def query_params(self) -> dict:

        # Zkontrolujeme jestli jsme query_params už někdy počítali
        # None znamená "ještě jsme to nepočítali"
        if self._query_params is None:
            # parse_qs rozebere query_string na slovník
            # "slovo=pes&barva=cerna" -> {"slovo": ["pes"], "barva": ["cerna"]}
            # Vrací seznam hodnot pro každý klíč (proto jsou v hranatých závorkách [])
            parsed = parse_qs(self._query_string)

            # Chceme {"slovo": "pes"} místo {"slovo": ["pes"]}
            # Proto procházíme slovník a pro každý klíč (k) a hodnotu (v):
            # Pokud je v seznamu jen jedna hodnota (len(v) == 1), vezmeme jen tu první v[0]
            # Jinak (více hodnot) necháme celý seznam v
            # Toto je "dict comprehension" — zkrácený způsob vytvoření slovníku
            self._query_params = {
                k: v[0] if len(v) == 1 else v for k, v in parsed.items()
            }

        # Vrátíme výsledek — buď právě vypočítaný nebo starý (z minulého volání)
        return self._query_params

    # Funkce json() přečte tělo zprávy jako JSON slovník
    # JSON je formát dat: {"jmeno": "Honza", "vek": 10}
    # -> dict vrací slovník Pythonu
    def json(self) -> dict:

        # Importujeme modul json uvnitř funkce — načte se jen když ho potřebujeme
        import json

        # json.loads() vezme text (nebo bytes) a přeloží ho na Python slovník
        # loads = "load string" (načti řetězec)
        return json.loads(self._body)

    # Funkce text() přečte tělo jako obyčejný text
    def text(self) -> str:

        # .decode("utf-8") přeloží bytes (bajty) na text
        # UTF-8 je způsob kódování textu — zahrnuje i česká písmena (á, é, í...)
        return self._body.decode("utf-8")

    # __repr__ je speciální funkce — Python ji zavolá když chceme zobrazit objekt
    # Například print(request) zavolá tuto funkci
    def __repr__(self):

        # Vrátíme pěkný popis objektu, například: Request(GET /uzivatele/42)
        return f"Request({self.method} {self.path})"
