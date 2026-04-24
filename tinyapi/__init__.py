"""
TinyAPI — Vzdělávací mini-framework inspirovaný FastAPI
=======================================================
Naučíš se zde:
  - Jak fungují Python dekorátory
  - Jak funguje HTTP routing
  - Jak funguje typová introspekce (inspect modul)
  - Jak funguje Dependency Injection
  - Jak funguje WSGI server

Minimální příklad:
    from tinyapi import TinyAPI

    app = TinyAPI()

    @app.get("/")
    def domov():
        return {"zprava": "Ahoj světe!"}

    app.run()  # http://localhost:8888
"""

# __init__.py je vstupní bod balíčku (package).
# Díky němu může Python importovat: from tinyapi import TinyAPI
# Místo:                            from tinyapi.app import TinyAPI

from .app import TinyAPI
from .request import Request
from .response import Response
from .dependencies import Depends

# __all__ říká, co se exportuje při "from tinyapi import *"
__all__ = ["TinyAPI", "Request", "Response", "Depends"]

__version__ = "0.1.0"
__author__ = "Vzdělávací projekt"
