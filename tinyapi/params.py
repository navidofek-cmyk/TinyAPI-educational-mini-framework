# Tento soubor zjišťuje co handler (funkce) potřebuje a dává mu to.
# Je to jako osobní asistent který před schůzkou připraví vše co potřebuješ:
# dokumenty, kávu, vizitky — vše co jsi požadoval.
#
# Jak to funguje?
# Python umí "rentgenovat" funkce — podívat se co potřebují.
# Tomu se říká INTROSPEKCE (self-reflection, sebepozorování).
#
# Příklad:
# def get_uzivatel(id: int, jmeno: str = "neznamy"):
#     ...
# Z této funkce zjistíme:
# - Parametr "id" typu int, bez výchozí hodnoty (povinný)
# - Parametr "jmeno" typu str, výchozí hodnota "neznamy" (volitelný)

# asyncio = modul pro asynchronní programování (více věcí najednou)
import asyncio

# inspect = modul pro "rentgenování" (introspekci) funkcí a tříd
import inspect

# get_type_hints = funkce která vrátí typové anotace funkce jako slovník
# Any = speciální typ který znamená "cokoliv"
from typing import get_type_hints, Any

# Importujeme naši třídu Depends ze souboru dependencies.py
# .dependencies = relativní import (stejná složka)
from .dependencies import Depends


# Funkce coerce() převede textový řetězec na správný typ
# Proč? URL parametry jsou VŽDY text. Ale funkce může chtít číslo.
# value = textová hodnota (vždy string z URL)
# target_type = cílový typ (int, float, bool, str)
# -> Any = vrátí cokoliv
def coerce(value: str, target_type) -> Any:

    # Pokud chceme boolean (True/False)
    if target_type is bool:

        # .lower() převede na malá písmena: "True" -> "true"
        # in (...) zkontroluje jestli je hodnota v seznamu
        # Vrátí True pro "1", "true", "yes", "ano" — jinak False
        return value.lower() in ("1", "true", "yes", "ano")

    # Pokud chceme číslo (celé nebo desetinné)
    if target_type in (int, float):

        # Zkusíme převést — "42" -> 42, "3.14" -> 3.14
        try:

            # target_type(value) zavolá int() nebo float() s hodnotou
            return target_type(value)

        # ValueError nastane když převod selže — "abc" nejde převést na int
        except ValueError:

            # Vyhodíme vlastní chybu s popisem co se stalo
            raise TypeError(f"Nelze převést '{value}' na {target_type.__name__}")

    # Pro str nebo Any vrátíme hodnotu beze změny
    return value


# Hlavní async funkce — zjistí co handler potřebuje a naplní to hodnotami
# handler = funkce která zpracuje požadavek
# request = příchozí HTTP žádost
# path_params = parametry z URL (například {"id": "42"})
# -> dict = vrátí slovník argumentů pro handler
async def resolve_handler_params(handler, request, path_params: dict) -> dict:

    # get_type_hints() je mocnější verze handler.__annotations__
    # Vrátí slovník: {"id": int, "jmeno": str, ...}
    # try/except pro případ že funkce má zvláštní anotace které nejdou přečíst
    try:
        hints = get_type_hints(handler)
    except Exception:
        # Pokud selže, použijeme prázdný slovník (bez typů)
        hints = {}

    # inspect.signature() vrátí "podpis" funkce — popis všech parametrů
    # Je to jako přečíst etiketu na krabičce: "obsah: id (číslo), jmeno (text)"
    sig = inspect.signature(handler)

    # kwargs bude slovník hotových argumentů které předáme handleru
    # Začínáme s prázdným slovníkem a postupně ho plníme
    kwargs = {}

    # Procházíme všechny parametry funkce
    # sig.parameters je slovník: {"id": <Parameter id: int>, ...}
    # .items() vrátí dvojice (název, objekt parametru)
    for name, param in sig.parameters.items():

        # Zjistíme typ parametru z hints slovníku
        # .get() vrátí None pokud typ není definován
        annotated_type = hints.get(name)

        # PŘÍPAD 1: Parametr je Request — chce celý objekt požadavku
        # getattr() bezpečně získá atribut objektu (nebo None pokud neexistuje)
        # __name__ je název třídy: Request.__name__ == "Request"
        # Tím se vyhneme importu Request zde (zamezení circular importu)
        if annotated_type is not None and getattr(annotated_type, "__name__", "") == "Request":

            # Dáme handleru celý request objekt
            kwargs[name] = request

            # continue = přeskočíme zbytek cyklu, jdeme na další parametr
            continue

        # PŘÍPAD 2: Parametr má Depends() — dependency injection
        # isinstance() zkontroluje jestli výchozí hodnota parametru je Depends objekt
        if isinstance(param.default, Depends):

            # Vytáhneme funkci ze závislosti
            dep_func = param.default.dependency

            # REKURZIVNĚ vyřešíme i parametry závislosti
            # (závislost může sama potřebovat Request nebo jiné závislosti)
            # await = počkej na výsledek async funkce
            dep_kwargs = await resolve_handler_params(dep_func, request, path_params)

            # Zkontrolujeme jestli je závislostní funkce async nebo normální
            if asyncio.iscoroutinefunction(dep_func):

                # async funkce — musíme použít await
                kwargs[name] = await dep_func(**dep_kwargs)

            else:

                # normální funkce — zavoláme přímo
                # **dep_kwargs = "rozbal slovník jako argumenty funkce"
                kwargs[name] = dep_func(**dep_kwargs)

            # Jdeme na další parametr
            continue

        # PŘÍPAD 3: Parametr je v path_params (z URL vzoru {id})
        # Například URL "/uzivatele/42" a vzor "/uzivatele/{id}" -> path_params = {"id": "42"}
        if name in path_params:

            # Vezmeme textovou hodnotu z URL
            raw_value = path_params[name]

            # Určíme cílový typ — pokud není annotace, použijeme str
            target = annotated_type if annotated_type is not None else str

            # Převedeme string na správný typ (např. "42" -> 42)
            kwargs[name] = coerce(raw_value, target)

            # Jdeme na další parametr
            continue

        # PŘÍPAD 4: Parametr je v query_params (za ? v URL)
        # Například URL "/hledat?slovo=pes" -> query_params = {"slovo": "pes"}
        if name in request.query_params:

            # Vezmeme textovou hodnotu z query stringu
            raw_value = request.query_params[name]

            # Určíme cílový typ
            target = annotated_type if annotated_type is not None else str

            # Převedeme a uložíme
            kwargs[name] = coerce(raw_value, target)

            # Jdeme na další parametr
            continue

        # PŘÍPAD 5: Parametr má výchozí hodnotu (default value)
        # inspect.Parameter.empty je speciální sentinel — znamená "žádná výchozí hodnota"
        if param.default is not inspect.Parameter.empty:

            # Použijeme výchozí hodnotu
            kwargs[name] = param.default

            # Jdeme na další parametr
            continue

        # PŘÍPAD 6: Parametr je povinný a nikde jsme ho nenašli — chyba!
        # Vyhodíme TypeError s popisem chybějícího parametru
        raise TypeError(f"Chybí povinný parametr: '{name}' ve funkci {handler.__name__}()")

    # Vrátíme hotový slovník argumentů
    return kwargs
