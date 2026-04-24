# Tento soubor řeší DEPENDENCY INJECTION (vkládání závislostí).
# Závislost = věc, kterou funkce potřebuje k práci.
#
# Příklad ze života:
# Kuchař potřebuje nůž, prkénko a suroviny.
# Místo aby si je sám hledal po celé kuchyni,
# dostane je "podány" — položené na stole před ním.
# Tomu se říká Dependency Injection.
#
# V kódu:
# Funkce potřebuje databázové připojení.
# Místo aby si ho sama pokaždé vytvářela,
# dostane ho jako parametr — TinyAPI ho připraví za ni.


# Třída Depends je jednoduchý "štítek"
# Když uvidíš Depends(get_db), říká to:
# "Zavolej funkci get_db() a výsledek mi dej jako argument"
class Depends:

    # __init__ přijme jednu věc: dependency = funkci která vrátí potřebnou hodnotu
    def __init__(self, dependency):

        # Uložíme funkci do atributu dependency
        # Například: Depends(get_db) uloží funkci get_db
        # Pozor: nevoláme get_db() — jen ji ULOŽÍME, zavolá se až později
        self.dependency = dependency

    # __repr__ — popis objektu pro výpis
    def __repr__(self):

        # .dependency.__name__ = název uložené funkce
        # Například Depends(get_db) -> "Depends(get_db)"
        return f"Depends({self.dependency.__name__})"
