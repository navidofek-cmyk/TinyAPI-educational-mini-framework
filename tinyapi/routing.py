# Tento soubor řeší ROUTING — jak server najde správnou funkci pro danou URL.
# Představ si velkou poštu.
# Přijde dopis (request) a poštovní úředník (router) rozhodne kdo ho vyřídí.
# URL /uzivatele/42 -> funkce get_uzivatel(id=42)
# URL /produkty     -> funkce seznam_produktu()

# Importujeme modul re — "regular expressions" (regulární výrazy)
# Regulární výraz je šablona pro porovnávání textu
# Například: r"\d+" odpovídá libovolnému číslu (1, 42, 999...)
import re

# dataclass je dekorátor, který automaticky vytvoří __init__, __repr__ a další
# Ušetříme psaní — Python sám vygeneruje kód pro ukládání atributů
from dataclasses import dataclass, field

# Callable = "něco co se dá zavolat" — funkce, metoda, lambda
# Importujeme ho pro typové anotace (říkáme Pythonu co očekáváme)
from typing import Callable


# @dataclass řekne Pythonu: "automaticky vytvoř __init__ z atributů níže"
# Je to jako říct: "vytvoř formulář s políčky path, method, handler"
@dataclass
class Route:
    # path = vzor URL adresy, například "/uzivatele/{id}"
    # str = datový typ string (textový řetězec)
    path: str

    # method = HTTP metoda: "GET", "POST", "PUT", "DELETE"
    method: str

    # handler = funkce která zpracuje požadavek — Callable říká "toto je funkce"
    handler: Callable

    # field(init=False) = tento atribut nevyplňuje uživatel
    # repr=False = nezobrazuj ho v __repr__ (byl by moc dlouhý)
    # _pattern bude zkompilovaný regulární výraz pro porovnávání URL
    _pattern: re.Pattern = field(init=False, repr=False)

    # _param_names bude seznam názvů parametrů z URL
    # Například z "/uzivatele/{id}" -> ["id"]
    _param_names: list = field(init=False, repr=False)

    # __post_init__ se zavolá AUTOMATICKY po __init__ (po vytvoření objektu)
    # dataclass zavolá __init__ sám, my pak dokončíme inicializaci zde
    def __post_init__(self):

        # Zavoláme naši pomocnou funkci _compile_path
        # Ona přeloží "/uzivatele/{id}" na regulární výraz a seznam parametrů
        # Výsledek uložíme do dvou proměnných najednou (tuple unpacking)
        pattern, self._param_names = self._compile_path(self.path)

        # re.compile() zkompiluje (připraví) regulární výraz pro opakované použití
        # ^ = začátek textu, $ = konec textu — URL musí přesně odpovídat
        # Tím se vyhneme tomu, že "/uzivatele/42extra" by pasovalo na "/uzivatele/{id}"
        self._pattern = re.compile(f"^{pattern}$")

    # Pomocná funkce která přeloží cestu s parametry na regulární výraz
    # -> tuple[str, list] říká: vrátí dvojici (text, seznam)
    def _compile_path(self, path: str) -> tuple[str, list]:

        # Sem budeme ukládat názvy parametrů které najdeme
        param_names = []

        # Definujeme vnitřní funkci (closure) — funkci uvnitř funkce
        # re.sub() ji zavolá pro každý nalezený výskyt vzoru
        def replace_param(match):

            # match.group(1) = obsah první závorky v regexu \{(\w+)\}
            # Například pro {id} vrátí "id"
            name = match.group(1)

            # Přidáme název do seznamu parametrů
            param_names.append(name)

            # Vrátíme regex skupinu: (?P<id>[^/]+)
            # (?P<name>...) = pojmenovaná zachytávací skupina
            # [^/]+ = jeden nebo více znaků které NEJSOU lomítko
            return f"(?P<{name}>[^/]+)"

        # re.sub() najde všechna {slova} a nahradí je pomocí naší funkce
        # r"\{(\w+)\}" = najdi {neco} kde neco jsou písmena/čísla/podtržítko
        # \{ a \} = složené závorky (musíme escapovat zpětným lomítkem)
        # \w+ = jedno nebo více "word" znaků (písmena, číslice, podtržítko)
        pattern = re.sub(r"\{(\w+)\}", replace_param, path)

        # Vrátíme dvojici: (hotový regex pattern, seznam názvů parametrů)
        return pattern, param_names

    # Funkce match() zkusí jestli tato Route odpovídá dané URL a metodě
    # Vrátí slovník s parametry (nebo None pokud nesedí)
    # dict | None = vrátí buď slovník nebo None (Python 3.10+)
    def match(self, path: str, method: str) -> dict | None:

        # Nejprve zkontrolujeme HTTP metodu (GET, POST...)
        # .upper() = převede na velká písmena pro jistotu
        if self.method != method.upper():

            # Špatná metoda — vrátíme None (žádná shoda)
            return None

        # Zkusíme porovnat URL s naším regulárním výrazem
        # .match() vrátí objekt Match pokud sedí, nebo None pokud nesedí
        m = self._pattern.match(path)

        # Pokud m není None (tj. regulární výraz sedí)
        if m:

            # .groupdict() vrátí pojmenované skupiny jako slovník
            # Například pro URL "/uzivatele/42" vrátí {"id": "42"}
            # Pozor: hodnoty jsou vždy STRING (text), i když jde o číslo!
            return m.groupdict()

        # URL nesedí — vrátíme None
        return None


# Třída Router uchovává seznam všech Routes a umí v nich hledat
class Router:

    # __init__ se zavolá při vytvoření nového Routeru
    def __init__(self):

        # routes je seznam všech zaregistrovaných cest
        # list[Route] = seznam objektů typu Route
        # Začínáme s prázdným seznamem []
        self.routes: list[Route] = []

    # Přidá novou Route do seznamu
    # path = vzor URL, method = HTTP metoda, handler = funkce
    def add_route(self, path: str, method: str, handler: Callable):

        # Route(...) vytvoří nový objekt Route
        # .append() přidá ho na konec seznamu self.routes
        self.routes.append(Route(path=path, method=method, handler=handler))

    # Dekorátor pro GET požadavky
    # Volá se jako: @app.get("/uzivatele")
    # path = URL vzor pro tuto cestu
    def get(self, path: str):

        # Vracíme FUNKCI (dekorátor) — ne výsledek
        # Tato funkce dostane handler jako argument
        def decorator(func: Callable) -> Callable:

            # Zaregistrujeme handler pro GET metodu na dané cestě
            self.add_route(path, "GET", func)

            # Vrátíme funkci BEZ ZMĚNY — dekorátor ji jen zaregistruje
            # Díky tomu ji jde volat i normálně: domov()
            return func

        # Vrátíme dekorátor (funkci decorator)
        return decorator

    # Dekorátor pro POST požadavky (posílání dat na server)
    def post(self, path: str):

        # Stejný vzor jako get() — jen jiná metoda
        def decorator(func: Callable) -> Callable:
            self.add_route(path, "POST", func)
            return func
        return decorator

    # Dekorátor pro PUT požadavky (aktualizace celého záznamu)
    def put(self, path: str):

        def decorator(func: Callable) -> Callable:
            self.add_route(path, "PUT", func)
            return func
        return decorator

    # Dekorátor pro DELETE požadavky (mazání záznamů)
    def delete(self, path: str):

        def decorator(func: Callable) -> Callable:
            self.add_route(path, "DELETE", func)
            return func
        return decorator

    # Dekorátor pro PATCH požadavky (aktualizace části záznamu)
    def patch(self, path: str):

        def decorator(func: Callable) -> Callable:
            self.add_route(path, "PATCH", func)
            return func
        return decorator

    # Funkce resolve() hledá Route která odpovídá dané URL a metodě
    # Vrátí dvojici: (nalezená Route, slovník parametrů)
    # Nebo: (None, {}) pokud nic nenajde
    def resolve(self, path: str, method: str) -> tuple:

        # Procházíme všechny zaregistrované routes jednu po druhé
        for route in self.routes:

            # Zkusíme shodu — match() vrátí slovník nebo None
            params = route.match(path, method)

            # Pokud params není None — našli jsme shodu!
            if params is not None:

                # Vrátíme nalezenou route a parametry z URL
                return route, params

        # Prošli jsme vše a nic nenašli — vrátíme None a prázdný slovník
        return None, {}

    # __repr__ — pěkný výpis obsahu routeru
    def __repr__(self):

        # Začneme s nadpisem
        lines = [f"Router ({len(self.routes)} routes):"]

        # Pro každou route přidáme řádek s metodou, cestou a názvem funkce
        for r in self.routes:

            # :6 = zarovnání na 6 znaků (aby GET a DELETE byly pod sebou)
            # r.handler.__name__ = název funkce (například "get_uzivatel")
            lines.append(f"  {r.method:6} {r.path} -> {r.handler.__name__}()")

        # "\n".join() spojí seznam řádků do jednoho textu odděleného novými řádky
        return "\n".join(lines)
