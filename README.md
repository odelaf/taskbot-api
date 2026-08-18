# TaskBot

FastAPI + Turso (libSQL) para gestionar tareas. Un solo motor de comandos (`commands.py`) compartido por dos interfaces:

- **`cli.py`** — terminal del MacBook.
- **`api.py`** — endpoint HTTP que usan los iOS Shortcuts (iPhone/iPad).

Ambas interfaces parsean y ejecutan **exactamente los mismos comandos**, así que la sintaxis de la tabla de abajo sirve para el MacBook y para iOS Shortcuts sin diferencias.

## Deploy en Render

1. Crear Web Service desde este repo
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn api:app --host 0.0.0.0 --port $PORT`
4. Variables de entorno requeridas:
   - `TURSO_DATABASE_URL`
   - `TURSO_AUTH_TOKEN`

> Tras hacer `git push`, redeployá en Render para que los iOS Shortcuts vean los últimos comandos (prioridad, renombrar, varias categorías, etc.).

## Uso en el MacBook (CLI)

Ver [CLI.md](CLI.md). Resumen:

```bash
python cli.py                 # modo interactivo
python cli.py "c::trabajo::enviar informe::0"
```

## Comandos

La sintaxis usa `::` como delimitador (general a particular):

| Comando | Accion |
|---------|--------|
| `help` / `help c` / `help k` | Ayuda general o por letra |
| `c::u::nombre` | Crear usuario |
| `c::c::nombre` | Crear categoria |
| `c::categoria::tarea::[0\|1]::[1-5]` | Crear tarea (estado y prioridad opcionales) |
| `k::u` / `k::u::nombre` | Listar usuarios / tareas pendientes de un usuario |
| `k::c` | Listar categorias |
| `k::t` / `k::t::0` / `k::t::p::1` | Todas / pendientes / por prioridad |
| `k::categoria` / `k::cat1,cat2` | Tareas de una o varias categorias |
| `k::categoria::0` / `k::categoria::p::1` | Filtro por estado o prioridad |
| `p::id::1-5` | Cambiar prioridad de una tarea |
| `r::id::nombre` | Renombrar tarea |
| `a::id::usuario` | Asignar tarea a usuario |
| `e::u\|c\|t::nombre\|id` | Eliminar usuario, categoria o tarea |
| `id::0\|1\|null` | Cambiar estado de tarea |
| `s` / `s::id::0\|1` | Supermercado: listar / marcar item |
| `l` | Pendientes urgentes (estado 0, prioridad 1) |
