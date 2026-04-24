# TinyAPI — Educational Mini-Framework / Vzdělávací mini-framework

> **EN:** A FastAPI clone written from scratch to understand how web frameworks work inside.
>
> **CZ:** FastAPI klon napsaný od nuly — aby bylo vidět jak webové frameworky fungují uvnitř.

---

## EN — English

### What you will learn

| File | Topic | Python concepts |
|------|-------|-----------------|
| `examples/01_hello_world.py` | Basic routing | Decorators, closures |
| `examples/02_path_params.py` | URL parameters | Regex, `inspect`, type hints |
| `examples/03_query_params.py` | Query string, POST | URL parsing, `isinstance` |
| `examples/04_dependencies.py` | Dependency Injection | `Depends`, recursion |
| `examples/05_async.py` | Async/Await | `asyncio`, coroutines |
| `examples/06_middleware.py` | Middleware | Decorator pattern |

### Quick start

```python
from tinyapi import TinyAPI

app = TinyAPI()

@app.get("/")
def home():
    return {"message": "Hello world!"}

app.run()  # http://localhost:8888
```

### Installation and running

```bash
# Clone the repo
git clone https://github.com/navidofek-cmyk/TinyAPI-educational-mini-framework.git
cd TinyAPI-educational-mini-framework

# Install dependencies via uv
uv sync

# Run an example
uv run python examples/01_hello_world.py
```

In another terminal:
```bash
curl http://localhost:8888/
```

### Run tests

```bash
uv run pytest tests/ -v
```

### Project structure

```
tinyapi/
├── tinyapi/
│   ├── __init__.py       # Package entry point
│   ├── app.py            # Main TinyAPI class
│   ├── routing.py        # Router + decorators
│   ├── request.py        # Request object
│   ├── response.py       # Response object
│   ├── params.py         # Introspection + type coercion
│   ├── dependencies.py   # Depends class
│   └── server.py         # WSGI HTTP server
├── examples/             # Learning cases (01–06)
├── tests/                # 16 unit tests
└── pyproject.toml        # uv / Python project config
```

### Comparison with FastAPI

```python
# FastAPI                          # TinyAPI
from fastapi import FastAPI        from tinyapi import TinyAPI
from fastapi import Depends        from tinyapi import Depends

app = FastAPI()                    app = TinyAPI()

@app.get("/users/{id}")            @app.get("/users/{id}")
def get_user(id: int):             def get_user(id: int):
    return {"id": id}                  return {"id": id}
```

The API is almost identical! FastAPI additionally provides: Pydantic validation,
OpenAPI docs, WebSockets, background tasks, OAuth2, and much more.

---

## CZ — Čeština

### Co se naučíš

| Soubor | Téma | Python koncepty |
|--------|------|-----------------|
| `examples/01_hello_world.py` | Základní routing | Dekorátory, closures |
| `examples/02_path_params.py` | URL parametry | Regex, `inspect`, type hints |
| `examples/03_query_params.py` | Query string, POST | Parsování URL, `isinstance` |
| `examples/04_dependencies.py` | Dependency Injection | `Depends`, rekurze |
| `examples/05_async.py` | Async/Await | `asyncio`, coroutiny |
| `examples/06_middleware.py` | Middleware | Decorator pattern |

### Rychlý start

```python
from tinyapi import TinyAPI

app = TinyAPI()

@app.get("/")
def domov():
    return {"zprava": "Ahoj světe!"}

app.run()  # http://localhost:8888
```

### Instalace a spuštění

```bash
# Naklonuj repozitář
git clone https://github.com/navidofek-cmyk/TinyAPI-educational-mini-framework.git
cd TinyAPI-educational-mini-framework

# Nainstaluj závislosti přes uv
uv sync

# Spusť příklad
uv run python examples/01_hello_world.py
```

V jiném terminálu:
```bash
curl http://localhost:8888/
```

### Spuštění testů

```bash
uv run pytest tests/ -v
```

### Struktura projektu

```
tinyapi/
├── tinyapi/
│   ├── __init__.py       # Vstupní bod balíčku
│   ├── app.py            # Hlavní třída TinyAPI
│   ├── routing.py        # Router + dekorátory
│   ├── request.py        # Request objekt
│   ├── response.py       # Response objekt
│   ├── params.py         # Introspekce + typová konverze
│   ├── dependencies.py   # Třída Depends
│   └── server.py         # WSGI HTTP server
├── examples/             # Learning cases (01–06)
├── tests/                # 16 unit testů
└── pyproject.toml        # uv / Python konfigurace projektu
```

### Srovnání s FastAPI

```python
# FastAPI                          # TinyAPI
from fastapi import FastAPI        from tinyapi import TinyAPI
from fastapi import Depends        from tinyapi import Depends

app = FastAPI()                    app = TinyAPI()

@app.get("/uzivatele/{id}")        @app.get("/uzivatele/{id}")
def get_uzivatel(id: int):         def get_uzivatel(id: int):
    return {"id": id}                  return {"id": id}
```

API je skoro stejné! FastAPI navíc přidává: Pydantic validaci, OpenAPI dokumentaci,
WebSockets, background tasks, OAuth2 a mnoho dalšího.

Každý soubor v projektu má komentář na každém řádku — psaný tak, aby ho pochopilo i 10leté dítě.
