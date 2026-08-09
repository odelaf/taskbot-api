# commands.py
import logging
import database as db

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def _rows_to_dicts(rows, columns=None):
    if not rows:
        return []
    if columns:
        return [dict(zip(columns, row)) for row in rows]
    return [dict(row) for row in rows]

def _format_task_list(rows, columns):
    if not rows:
        return "No hay tareas."
    tasks = _rows_to_dicts(rows, columns)
    lines = []
    for t in tasks:
        estado = t.get("estado")
        estado_txt = {0: "Pendiente", 1: "Completada", None: "Sin definir"}.get(estado, "?")
        categoria = t.get("categoria") or "?"
        lines.append(f"{t['id']} · {categoria} · {t['descripcion']} · ({t.get('prioridad', 3)}) · [{estado_txt}]")
    return "\n".join(lines)

def parsear(texto: str) -> dict | None:
    texto = texto.strip()
    if not texto:
        return None

    lower_text = texto.lower()

    if lower_text.startswith(("help", "ayuda", "h", "?")):
        parts = [p.strip() for p in texto.replace("::", " ").split() if p.strip()]
        if parts and parts[0].lower() in ("help", "ayuda", "h", "?"):
            if len(parts) == 1:
                return {"accion": "HELP"}
            sub = parts[1].lower()
            if sub in ("c", "crear"):     return {"accion": "HELP_C"}
            if sub in ("k", "consultar", "ver"): return {"accion": "HELP_K"}
            if sub in ("a", "asignar"):   return {"accion": "HELP_A"}
            if sub in ("e", "eliminar", "borrar"): return {"accion": "HELP_E"}
            if sub in ("r", "renombrar", "renom"): return {"accion": "HELP_R"}
            if sub in ("s", "super", "mercado"): return {"accion": "HELP_S"}
            if sub in ("p", "prioridad", "prio"): return {"accion": "HELP_P"}
            if sub in ("estado", "status"): return {"accion": "HELP_ESTADO"}
            return {"accion": "HELP"}

    p = [x.strip() for x in texto.split("::") if x.strip()]
    if not p:
        return None

    primera = p[0].lower()

    # Estado: 5::0, 5::1, 5::null
    if len(p) == 2 and p[0].isdigit() and p[1].lower() in ("0", "1", "null"):
        return {"accion": "ESTADO", "id": int(p[0]), "estado": p[1]}

    # Supermercado
    if primera == "s" and len(p) == 1:
        return {"accion": "S_LIST"}
    if primera == "s" and len(p) == 3 and p[1].isdigit() and p[2] in ("0", "1"):
        return {"accion": "S_STATE", "id": int(p[1]), "existencia": int(p[2])}

    # Prioridad: p::id::1-5
    if primera == "p" and len(p) == 3 and p[1].isdigit() and p[2].isdigit():
        prio = int(p[2])
        if 1 <= prio <= 5:
            return {"accion": "PRIORIDAD", "id": int(p[1]), "prioridad": prio}

    acc = p[0].upper()

    # Crear (C)
    if acc == "C" and len(p) >= 3:
        if p[1].upper() == "U":
            return {"accion": "C_USUARIO", "nombre": p[2]}
        if p[1].upper() == "C":
            return {"accion": "C_CATEGORIA", "nombre": p[2]}
        est = int(p[3]) if len(p) > 3 and p[3] in ("0", "1") else None
        prio = int(p[4]) if len(p) > 4 and p[4].isdigit() and 1 <= int(p[4]) <= 5 else None
        return {"accion": "C_TAREA", "cat": p[1], "desc": p[2], "estado": est, "prioridad": prio}

    # Consultar (K)
    if acc == "K" and len(p) >= 2:
        sub = p[1].upper()

        # k::u / k::u::nombre
        if sub == "U":
            if len(p) == 2:
                return {"accion": "K_USUARIOS"}
            return {"accion": "K_USUARIO_TAREAS", "usuario": p[2]}

        # k::c (lista categorias)
        if sub == "C" and len(p) == 2:
            return {"accion": "K_CATEGORIAS"}

        # k::t / k::t::0/1 / k::t::p::1-5
        if sub == "T":
            if len(p) == 2:
                return {"accion": "K_TODAS"}
            if len(p) == 4 and p[2].lower() == "p" and p[3].isdigit():
                return {"accion": "K_PRIORIDAD_GLOBAL", "prioridad": int(p[3])}
            return {"accion": "K_ESTADO_GLOBAL", "estado": int(p[2])}

        # k::categoria / k::categoria::0/1 / k::categoria::p::1-5
        if len(p) == 2:
            return {"accion": "K_CAT_TAREAS", "cat": p[1]}
        if len(p) == 3 and p[2] in ("0", "1"):
            return {"accion": "K_CAT_ESTADO", "cat": p[1], "estado": int(p[2])}
        if len(p) == 4 and p[2].lower() == "p" and p[3].isdigit():
            return {"accion": "K_CAT_PRIORIDAD", "cat": p[1], "prioridad": int(p[3])}

    # Asignar (A)
    if acc == "A" and len(p) == 3 and p[1].isdigit():
        return {"accion": "ASIGNAR", "id": int(p[1]), "usuario": p[2]}

    # Eliminar (E)
    if acc == "E" and len(p) == 3:
        if p[1].upper() == "U": return {"accion": "E_USUARIO", "nombre": p[2]}
        if p[1].upper() == "C": return {"accion": "E_CATEGORIA", "nombre": p[2]}
        if p[1].upper() == "T": return {"accion": "E_TAREA", "id": int(p[2])}

    # Renombrar tarea: r::id::nuevo nombre
    if primera == "r" and len(p) >= 3 and p[1].isdigit():
        return {"accion": "RENOMBRAR", "id": int(p[1]), "nombre": p[2]}

    return None


async def ejecutar(cmd: dict):
    c = db.get_db()
    acc = cmd["accion"]

    try:
        # ------- AYUDA -------
        if acc == "HELP":
            return {"msg": (
                "Significado de Prefijos:\n"
                "  c = Crear (Usuarios, Categorias, Tareas)\n"
                "  k = Consultar (Ver listas, tareas pendientes)\n"
                "  a = Asignar (Tarea a Usuario)\n"
                "  p = Prioridad (Cambiar prioridad 1-5)\n"
                "  r = Renombrar (Cambiar nombre de tarea)\n"
                "  e = Eliminar (Borrar registros)\n"
                "  s = Supermercado (Lista de compras)\n"
                "  id::0|1|null = Cambiar estado de tarea\n\n"
                "Escala de prioridad: 1=Urgente, 2=Alta, 3=Media, 4=Baja, 5=Minima\n\n"
                "Escribe help [letra] para ver la sintaxis de cada comando.\n"
                "Ejemplo: help c  o  help k"
            ), "items": []}

        elif acc == "HELP_C":
            return {"msg": (
                "--- Sintaxis de Creacion (c::) ---\n\n"
                "c::u::nombre\n"
                "  Crea un usuario.\n"
                "  Ej: c::u::juan\n\n"
                "c::c::nombre\n"
                "  Crea una categoria.\n"
                "  Ej: c::c::casa\n\n"
                "c::categoria::tarea::[estado]\n"
                "  Crea una tarea. 0=Pendiente, 1=Completada, omitir=Sin definir.\n"
                "  Ej: c::casa::limpiar::0\n\n"
                "c::categoria::tarea::[estado]::[prioridad]\n"
                "  Crea una tarea con prioridad (1-5).\n"
                "  Ej: c::casa::limpiar::0::2  (pendiente, prioridad alta)"
            ), "items": []}

        elif acc == "HELP_K":
            return {"msg": (
                "--- Sintaxis de Consulta (k::) ---\n\n"
                "k::u              -> Lista usuarios\n"
                "k::u::nombre      -> Tareas pendientes de un usuario\n"
                "k::c              -> Lista categorias\n"
                "k::categoria      -> Tareas de esa categoria\n"
                "k::categoria::0   -> Pendientes de esa categoria\n"
                "k::categoria::p::1 -> Tareas de esa categoria con prioridad 1\n"
                "k::t              -> Todas las tareas\n"
                "k::t::0           -> Todas las pendientes\n"
                "k::t::p::1        -> Todas las tareas con prioridad 1"
            ), "items": []}

        elif acc == "HELP_A":
            return {"msg": (
                "--- Sintaxis de Asignacion (a::) ---\n\n"
                "a::id_tarea::usuario\n\n"
                "Asigna una tarea existente a un usuario.\n"
                "Ej: a::5::juan"
            ), "items": []}

        elif acc == "HELP_E":
            return {"msg": (
                "--- Sintaxis de Eliminacion (e::) ---\n\n"
                "e::u::nombre  -> Borra usuario\n"
                "e::c::nombre  -> Borra categoria (y sus tareas)\n"
                "e::t::id      -> Borra tarea por ID"
            ), "items": []}

        elif acc == "HELP_R":
            return {"msg": (
                "--- Renombrar Tarea (r::) ---\n\n"
                "r::id::nuevo nombre\n\n"
                "Cambia la descripcion de una tarea.\n"
                "  Ej: r::5::limpiar cocina y baño"
            ), "items": []}

        elif acc == "HELP_S":
            return {"msg": (
                "--- Comandos de Supermercado (s) ---\n\n"
                "s             -> Muestra items pendientes\n"
                "s::id::1      -> Marca item como comprado\n"
                "s::id::0      -> Marca item como pendiente"
            ), "items": []}

        elif acc == "HELP_ESTADO":
            return {"msg": (
                "--- Cambio de Estado ---\n\n"
                "id::0         -> Pendiente\n"
                "id::1         -> Completada\n"
                "id::null      -> Limpia estado"
            ), "items": []}

        elif acc == "HELP_P":
            return {"msg": (
                "--- Escala de Prioridad (p::) ---\n\n"
                "1 = Urgente\n"
                "2 = Alta\n"
                "3 = Media (default)\n"
                "4 = Baja\n"
                "5 = Minima\n\n"
                "Cambiar prioridad: p::id::1-5\n"
                "  Ej: p::5::1  (tarea 5 a urgente)\n\n"
                "Crear con prioridad:\n"
                "  Ej: c::trabajo::informe::0::2\n\n"
                "Filtrar por prioridad:\n"
                "  k::t::p::1        (todas las urgentes)\n"
                "  k::trabajo::p::2  (trabajo con prioridad alta)"
            ), "items": []}

        # ------- ASIGNAR -------
        elif acc == "ASIGNAR":
            uid_res = await c.execute("SELECT id FROM usuario WHERE nombre=?", (cmd["usuario"],))
            if not uid_res.rows:
                return {"msg": f"Usuario '{cmd['usuario']}' no existe. Crealo con c::u::{cmd['usuario']}", "items": []}
            await c.execute("UPDATE tarea SET usuario_id=? WHERE id=?", (uid_res.rows[0]["id"], cmd["id"]))
            return {"msg": f"Tarea {cmd['id']} asignada a {cmd['usuario']}", "items": []}

        # ------- ESTADO -------
        elif acc == "ESTADO":
            if cmd["estado"] == "null":
                await c.execute("UPDATE tarea SET estado=NULL, actualizado_en=datetime('now') WHERE id=?", (cmd["id"],))
                return {"msg": f"Tarea {cmd['id']} -> estado limpiado", "items": []}
            comp = "datetime('now')" if cmd["estado"] == "1" else None
            await c.execute("UPDATE tarea SET estado=?, actualizado_en=datetime('now'), completada_en=? WHERE id=?",
                            (int(cmd["estado"]), comp, cmd["id"]))
            return {"msg": f"Tarea {cmd['id']} -> {'completada' if cmd['estado']=='1' else 'pendiente'}", "items": []}

        # ------- PRIORIDAD -------
        elif acc == "PRIORIDAD":
            await c.execute("UPDATE tarea SET prioridad=?, actualizado_en=datetime('now') WHERE id=?", (cmd["prioridad"], cmd["id"]))
            return {"msg": f"Tarea {cmd['id']} -> prioridad {cmd['prioridad']}", "items": []}

        # ------- SUPERMERCADO -------
        elif acc == "S_LIST":
            res = await c.execute("SELECT id, chino, pinyin, español FROM supermercado WHERE existencia = 0 ORDER BY id")
            items = _rows_to_dicts(res.rows, res.columns)

            if not items:
                return {"msg": "Lista vacia. Todo comprado o sin estado definido.", "items": []}

            lines = []
            for item in items:
                chino = item.get("chino", "")
                pinyin = item.get("pinyin", "")
                espanol = item.get("español", "")
                item_id = item.get("id")

                if pinyin:
                    lines.append(f"#{item_id} {chino} ({pinyin}) - {espanol}")
                else:
                    lines.append(f"#{item_id} {chino} - {espanol}")

            return {"msg": "Pendientes:\n" + "\n".join(lines), "items": items}

        elif acc == "S_STATE":
            await c.execute("UPDATE supermercado SET existencia=?, actualizado_en=datetime('now') WHERE id=?", (cmd["existencia"], cmd["id"]))
            return {"msg": f"Item {cmd['id']} -> {'comprado' if cmd['existencia']==1 else 'pendiente'}", "items": []}

        # ------- CREAR -------
        elif acc == "C_USUARIO":
            await c.execute("INSERT OR IGNORE INTO usuario (nombre) VALUES (?)", (cmd["nombre"],))
            return {"msg": f"Usuario '{cmd['nombre']}' creado", "items": []}

        elif acc == "C_CATEGORIA":
            await c.execute("INSERT OR IGNORE INTO categoria (nombre) VALUES (?)", (cmd["nombre"],))
            return {"msg": f"Categoria '{cmd['nombre']}' creada", "items": []}

        elif acc == "C_TAREA":
            cat_res = await c.execute("SELECT id FROM categoria WHERE nombre=?", (cmd["cat"],))
            if not cat_res.rows:
                return {"msg": f"Categoria '{cmd['cat']}' no existe", "items": []}
            prioridad = cmd.get("prioridad") or 3
            await c.execute("INSERT INTO tarea (categoria_id, usuario_id, descripcion, prioridad, estado) VALUES (?, NULL, ?, ?, ?)",
                            (cat_res.rows[0]["id"], cmd["desc"], prioridad, cmd["estado"]))
            return {"msg": f"Tarea '{cmd['desc']}' en '{cmd['cat']}'", "items": []}

        # ------- CONSULTAR -------
        elif acc == "K_USUARIOS":
            res = await c.execute("SELECT id, nombre FROM usuario ORDER BY nombre")
            items = _rows_to_dicts(res.rows, res.columns)
            nombres = ", ".join([i["nombre"] for i in items]) if items else "Ninguno"
            return {"msg": f"Usuarios: {nombres}", "items": items}

        elif acc == "K_USUARIO_TAREAS":
            uid = await c.execute("SELECT id FROM usuario WHERE nombre=?", (cmd["usuario"],))
            if not uid.rows:
                return {"msg": f"Usuario '{cmd['usuario']}' no encontrado", "items": []}
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, t.estado, c.nombre as categoria
                FROM tarea t JOIN categoria c ON t.categoria_id=c.id WHERE t.usuario_id=? AND t.estado=0 ORDER BY t.prioridad, c.nombre, t.id""", (uid.rows[0]["id"],))
            return {"msg": _format_task_list(res.rows, res.columns), "items": _rows_to_dicts(res.rows, res.columns)}

        elif acc == "K_CATEGORIAS":
            res = await c.execute("SELECT id, nombre FROM categoria ORDER BY nombre")
            items = _rows_to_dicts(res.rows, res.columns)
            nombres = ", ".join([i["nombre"] for i in items]) if items else "Ninguna"
            return {"msg": f"Categorias: {nombres}", "items": items}

        elif acc == "K_CAT_TAREAS":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, t.estado, c.nombre as categoria FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id WHERE c.nombre=? ORDER BY CASE WHEN t.estado = 0 THEN 0 WHEN t.estado IS NULL THEN 1 ELSE 2 END, t.prioridad, t.id""", (cmd["cat"],))
            return {"msg": _format_task_list(res.rows, res.columns), "items": _rows_to_dicts(res.rows, res.columns)}

        elif acc == "K_CAT_ESTADO":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, t.estado, c.nombre as categoria FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id WHERE c.nombre=? AND t.estado=? ORDER BY t.prioridad, t.id""", (cmd["cat"], cmd["estado"]))
            return {"msg": _format_task_list(res.rows, res.columns), "items": _rows_to_dicts(res.rows, res.columns)}

        elif acc == "K_CAT_PRIORIDAD":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, t.estado, c.nombre as categoria FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id WHERE c.nombre=? AND t.prioridad=? ORDER BY CASE WHEN t.estado = 0 THEN 0 WHEN t.estado IS NULL THEN 1 ELSE 2 END, t.id""", (cmd["cat"], cmd["prioridad"]))
            return {"msg": _format_task_list(res.rows, res.columns), "items": _rows_to_dicts(res.rows, res.columns)}

        elif acc == "K_TODAS":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, t.estado, t.usuario_id, c.nombre as categoria FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id ORDER BY c.nombre, CASE WHEN t.estado = 0 THEN 0 WHEN t.estado IS NULL THEN 1 ELSE 2 END, t.prioridad, t.id""")
            return {"msg": _format_task_list(res.rows, res.columns), "items": _rows_to_dicts(res.rows, res.columns)}

        elif acc == "K_ESTADO_GLOBAL":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, t.estado, c.nombre as categoria FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id WHERE t.estado=? ORDER BY c.nombre, t.prioridad, t.id""", (cmd["estado"],))
            return {"msg": _format_task_list(res.rows, res.columns), "items": _rows_to_dicts(res.rows, res.columns)}

        elif acc == "K_PRIORIDAD_GLOBAL":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, t.estado, c.nombre as categoria FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id WHERE t.prioridad=? ORDER BY c.nombre, CASE WHEN t.estado = 0 THEN 0 WHEN t.estado IS NULL THEN 1 ELSE 2 END, t.id""", (cmd["prioridad"],))
            return {"msg": _format_task_list(res.rows, res.columns), "items": _rows_to_dicts(res.rows, res.columns)}

        # ------- ELIMINAR -------
        elif acc == "E_USUARIO":
            r = await c.execute("DELETE FROM usuario WHERE nombre=?", (cmd["nombre"],))
            return {"msg": f"Usuario '{cmd['nombre']}' eliminado" if r.rows_affected else "Usuario no encontrado", "items": []}

        elif acc == "E_CATEGORIA":
            r = await c.execute("DELETE FROM categoria WHERE nombre=?", (cmd["nombre"],))
            return {"msg": f"Categoria '{cmd['nombre']}' eliminada" if r.rows_affected else "No encontrada", "items": []}

        elif acc == "E_TAREA":
            r = await c.execute("DELETE FROM tarea WHERE id=?", (cmd["id"],))
            return {"msg": f"Tarea {cmd['id']} eliminada" if r.rows_affected else "No encontrada", "items": []}

        # ------- RENOMBRAR -------
        elif acc == "RENOMBRAR":
            await c.execute("UPDATE tarea SET descripcion=?, actualizado_en=datetime('now') WHERE id=?", (cmd["nombre"], cmd["id"]))
            return {"msg": f"Tarea {cmd['id']} renombrada a '{cmd['nombre']}'", "items": []}

        else:
            return {"msg": "Comando no reconocido. Usa 'help'.", "items": []}

    except Exception as e:
        logger.error(f"DB Error en {acc}: {e}")
        return {"msg": f"Error interno: {e}", "items": []}
