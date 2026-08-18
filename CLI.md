# TaskBot CLI

Gestiona tareas desde la terminal del MacBook usando los mismos comandos `::` que en iOS Shortcuts.

`cli.py` y `api.py` comparten el mismo motor `commands.py`: la sintaxis es idéntica en ambos. Si iOS Shortcuts muestra resultados distintos, suele ser porque el API desplegado en Render está con código viejo: hacé `git push` y redeployá.

## Requisitos

Python 3.11+ y un archivo `.env` con:

```
TURSO_DATABASE_URL=https://tu-db.turso.io
TURSO_AUTH_TOKEN=tu-token
```

## Instalación

```bash
pip install -r requirements.txt
```

## Alias (recomendado)

```bash
echo "alias t='python ~/Python/tareas/taskbot/cli.py'" >> ~/.zshrc
source ~/.zshrc
```

Luego puedes usar `t` desde cualquier carpeta.

## Uso

**Modo interactivo:**

```bash
python cli.py
```

Abre un REPL donde escribís comandos. `salir` o Ctrl+D para terminar.

**Comando directo:**

```bash
python cli.py "c::trabajo::enviar informe::0"
python cli.py k::t::0
python cli.py "5::1"
```

Con el alias: `t k::t`, `t help`, etc.

## Comandos

| Acción | Sintaxis | Ejemplo |
|---|---|---|
| Ayuda | `help` | `help c` |
| Crear usuario | `c::u::nombre` | `c::u::juan` |
| Crear categoría | `c::c::nombre` | `c::c::casa` |
| Crear tarea | `c::cat::desc::[0\|1]::[1-5]` | `c::casa::limpiar::0::2` |
| Listar usuarios | `k::u` | |
| Listar categorías | `k::c` | |
| Listar tareas | `k::t` | `k::t::0` (pendientes) |
| Listar por categoría | `k::categoria` | `k::casa::0` |
| Listar varias categorías | `k::cat1,cat2` | `k::casa,qq::0` |
| Filtrar por prioridad | `k::t::p::1-5` | `k::t::p::1` (urgentes) |
| Cambiar prioridad | `p::id::1-5` | `p::5::1` |
| Asignar tarea | `a::id::usuario` | `a::5::juan` |
| Cambiar estado | `id::0\|1\|null` | `5::1` |
| Renombrar tarea | `r::id::nombre` | `r::5::comprar pan` |
| Eliminar | `e::u\|c\|t::nombre\|id` | `e::t::4` |
| Supermercado | `s` | `s::3::1` |
| Urgentes pendientes | `l` | |

### Prioridad

Escala de 1 a 5:

| Valor | Significado |
|---|---|
| `1` | Urgente |
| `2` | Alta |
| `3` | Media (default) |
| `4` | Baja |
| `5` | Mínima |

Se puede definir al crear (`c::cat::tarea::0::2`) o cambiar después (`p::id::2`).

### Estados

- `0` = Pendiente (amarillo)
- `1` = Completada (verde)
- `null` = Sin definir

### Salida

Las tareas se muestran con el formato `id · categoría · nombre · (prioridad) · [estado]` y coloreadas: verdes completadas, amarillas pendientes, grises sin definir.
