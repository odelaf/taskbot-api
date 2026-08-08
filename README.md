# TaskBot API

FastAPI + Turso (libSQL) para gestionar tareas desde iOS Shortcuts.

## Deploy en Render

1. Crear Web Service desde este repo
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn api:app --host 0.0.0.0 --port $PORT`
4. Variables de entorno requeridas:
   - `TURSO_DATABASE_URL`
   - `TURSO_AUTH_TOKEN`

## Comandos

La sintaxis usa `::` como delimitador (general a particular):

| Comando | Accion |
|---------|--------|
| `c::u::nombre` | Crear usuario |
| `c::c::nombre` | Crear categoria |
| `c::categoria::tarea::0` | Crear tarea pendiente |
| `k::u` | Listar usuarios |
| `k::c` | Listar categorias |
| `k::t` | Listar todas las tareas |
| `k::categoria` | Tareas de una categoria |
| `k::categoria::0` | Pendientes de una categoria |
| `k::t::0` | Todas las pendientes |
| `k::u::nombre` | Tareas pendientes de un usuario |
| `a::id::usuario` | Asignar tarea a usuario |
| `e::u::nombre` | Eliminar usuario |
| `e::c::nombre` | Eliminar categoria |
| `e::t::id` | Eliminar tarea |
| `id::0\|1\|null` | Cambiar estado de tarea |
| `s` | Lista de supermercado pendiente |
| `s::id::0\|1` | Marcar item supermercado |
| `help` | Ayuda general |
| `help c` | Ayuda de creacion |
