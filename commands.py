# commands.py
import sys
import database as db

def _rows_to_dicts(rows):
    """Convierte filas de libsql-client a lista de dicts puros para JSON."""
    if not rows:
        return []
    return [dict(row) for row in rows]

def parsear(texto: str) -> dict | None:
    p = [x.strip() for x in texto.split("::") if x.strip()]
    if not p:
        return None

    # 🔹 HELP / AYUDA
    if p[0].lower() in ("help", "ayuda", "?", "!help", "!ayuda", "h"):
        return {"accion": "HELP"}

    # id::estado (ej: 5::0, 12::1, 3::null)
    if len(p) == 2 and p[0].isdigit() and p[1].lower() in ("0", "1", "null"):
        return {"accion": "ESTADO", "id": int(p[0]), "estado": p[1]}

    # Supermercado
    if p == ["s"]:
        return {"accion": "S_LIST"}
    if len(p) == 3 and p[0].lower() == "s" and p[1].isdigit() and p[2] in ("0", "1"):
        return {"accion": "S_STATE", "id": int(p[1]), "existencia": int(p[2])}

    acc = p[0].upper()
    if acc == "C":
        if len(p) >= 3 and p[1].upper() == "U":
            return {"accion": "C_USUARIO", "nombre": p[2]}
        if len(p) >= 3 and p[1].upper() == "C":
            return {"accion": "C_CATEGORIA", "nombre": p[2]}
        if len(p) >= 3:  # c::categoria::desc::[estado]
            est = int(p[3]) if len(p) > 3 and p[3] in ("0", "1") else None
            return {"accion": "C_TAREA", "cat": p[1], "desc": p[2], "estado": est}
    elif acc == "K":
        if len(p) == 2 and p[1].upper() == "U":
            return {"accion": "K_USUARIOS"}
        if len(p) == 3 and p[1].upper() == "U":
            return {"accion": "K_USUARIO_TAREAS", "usuario": p[2]}
        if len(p) == 2 and p[1].upper() == "C":
            return {"accion": "K_CATEGORIAS"}
        if len(p) == 2 and p[1].upper() != "T":
            return {"accion": "K_CAT_TAREAS", "cat": p[1]}
        if len(p) == 3 and p[2] in ("0", "1"):
            return {"accion": "K_CAT_ESTADO", "cat": p[1], "estado": int(p[2])}
        if p[1].upper() == "T" and len(p) == 2:
            return {"accion": "K_TODAS"}
        if p[1].upper() == "T" and len(p) == 3 and p[2] in ("0", "1"):
            return {"accion": "K_ESTADO_GLOBAL", "estado": int(p[2])}
    elif acc == "E":
        if len(p) == 3 and p[1].upper() == "U":
            return {"accion": "E_USUARIO", "nombre": p[2]}
        if len(p) == 3 and p[1].upper() == "C":
            return {"accion": "E_CATEGORIA", "nombre": p[2]}
        if len(p) == 3 and p[1].upper() == "T":
            return {"accion": "E_TAREA", "id": int(p[2])}

    return None

async def ejecutar(cmd: dict):
    c = db.get_db()
    acc = cmd["accion"]
    
    try:
        # 🔹 HELP
        if acc == "HELP":
            help_text = (
                "📋 Comandos disponibles:\n"
                "• c::u::nombre → Crear usuario\n"
                "• c::c::nombre → Crear categoría\n"
                "• c::categoria::desc::[0|1] → Crear tarea (0=pendiente, 1=completada)\n"
                "• k::u → Listar usuarios\n"
                "• k::u::nombre → Tareas pendientes de usuario\n"
                "• k::c → Listar categorías\n"
                "• k::categoria → Todas las tareas de categoría\n"
                "• k::categoria::0 → Pendientes de categoría\n"
                "• k::categoria::1 → Completadas de categoría\n"
                "• k::t → Todas las tareas\n"
                "• k::t::0 → Todas las pendientes\n"
                "• k::t::1 → Todas las completadas\n"
                "• id::0 → Marcar tarea como pendiente\n"
                "• id::1 → Marcar tarea como completada\n"
                "• id::null → Limpiar estado de tarea\n"
                "• e::u::nombre → Eliminar usuario\n"
                "• e::c::nombre → Eliminar categoría\n"
                "• e::t::id → Eliminar tarea\n"
                "• s → Mostrar items de supermercado pendientes\n"
                "• s::id::1 → Marcar item como comprado\n"
                "• s::id::0 → Desmarcar item"
            )
            return {"msg": help_text, "items": []}

        if acc == "ESTADO":
            if cmd["estado"] == "null":
                await c.execute("UPDATE tarea SET estado=NULL, actualizado_en=datetime('now') WHERE id=?", (cmd["id"],))
                return {"msg": f"Tarea {cmd['id']} → estado limpiado", "items": []}
            comp = "datetime('now')" if cmd["estado"] == "1" else None
            await c.execute("UPDATE tarea SET estado=?, actualizado_en=datetime('now'), completada_en=? WHERE id=?",
                            (int(cmd["estado"]), comp, cmd["id"]))
            return {"msg": f"Tarea {cmd['id']} → {'completada' if cmd['estado']=='1' else 'pendiente'}", "items": []}

        if acc == "S_LIST":
            res = await c.execute("SELECT id, chino, pinyin, español FROM supermercado WHERE existencia=0 OR existencia IS NULL ORDER BY id")
            return {"msg": f"{len(res.rows)} pendientes", "items": _rows_to_dicts(res.rows)}
        if acc == "S_STATE":
            await c.execute("UPDATE supermercado SET existencia=?, actualizado_en=datetime('now') WHERE id=?", (cmd["existencia"], cmd["id"]))
            return {"msg": f"Item {cmd['id']} → {'comprado' if cmd['existencia']==1 else 'pendiente'}", "items": []}

        if acc == "C_USUARIO":
            await c.execute("INSERT OR IGNORE INTO usuario (nombre) VALUES (?)", (cmd["nombre"],))
            return {"msg": f"Usuario '{cmd['nombre']}' creado", "items": []}
        if acc == "C_CATEGORIA":
            await c.execute("INSERT OR IGNORE INTO categoria (nombre) VALUES (?)", (cmd["nombre"],))
            return {"msg": f"Categoría '{cmd['nombre']}' creada", "items": []}
        if acc == "C_TAREA":
            cat_res = await c.execute("SELECT id FROM categoria WHERE nombre=?", (cmd["cat"],))
            if not cat_res.rows:
                return {"msg": f"Categoría '{cmd['cat']}' no existe", "items": []}
            await c.execute("INSERT INTO tarea (categoria_id, usuario_id, descripcion, prioridad, estado) VALUES (?, NULL, ?, 3, ?)",
                            (cat_res.rows[0]["id"], cmd["desc"], cmd["estado"]))
            return {"msg": f"Tarea '{cmd['desc']}' en '{cmd['cat']}'", "items": []}

        if acc == "K_USUARIOS":
            res = await c.execute("SELECT id, nombre FROM usuario ORDER BY nombre")
            return {"msg": f"{len(res.rows)} usuarios", "items": _rows_to_dicts(res.rows)}
        if acc == "K_USUARIO_TAREAS":
            uid = await c.execute("SELECT id FROM usuario WHERE nombre=?", (cmd["usuario"],))
            if not uid.rows:
                return {"msg": f"Usuario '{cmd['usuario']}' no encontrado", "items": []}
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, c.nombre as categoria
                FROM tarea t JOIN categoria c ON t.categoria_id=c.id WHERE t.usuario_id=? AND t.estado=0""", (uid.rows[0]["id"],))
            return {"msg": f"{len(res.rows)} pendientes para {cmd['usuario']}", "items": _rows_to_dicts(res.rows)}
        if acc == "K_CATEGORIAS":
            res = await c.execute("SELECT id, nombre FROM categoria ORDER BY nombre")
            return {"msg": f"{len(res.rows)} categorías", "items": _rows_to_dicts(res.rows)}
        if acc == "K_CAT_TAREAS":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, t.estado, t.usuario_id FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id WHERE c.nombre=? ORDER BY t.id""", (cmd["cat"],))
            return {"msg": f"{len(res.rows)} tareas en '{cmd['cat']}'", "items": _rows_to_dicts(res.rows)}
        if acc == "K_CAT_ESTADO":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, t.usuario_id FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id WHERE c.nombre=? AND t.estado=? ORDER BY t.id""", (cmd["cat"], cmd["estado"]))
            tipo = "pendientes" if cmd["estado"]==0 else "completadas"
            return {"msg": f"{len(res.rows)} {tipo} en '{cmd['cat']}'", "items": _rows_to_dicts(res.rows)}
        if acc == "K_TODAS":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, t.estado, c.nombre as categoria FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id ORDER BY c.nombre, t.id""")
            return {"msg": f"{len(res.rows)} tareas totales", "items": _rows_to_dicts(res.rows)}
        if acc == "K_ESTADO_GLOBAL":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, c.nombre as categoria FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id WHERE t.estado=? ORDER BY c.nombre, t.id""", (cmd["estado"],))
            tipo = "pendientes" if cmd["estado"]==0 else "completadas"
            return {"msg": f"{len(res.rows)} tareas {tipo}", "items": _rows_to_dicts(res.rows)}

        if acc == "E_USUARIO":
            r = await c.execute("DELETE FROM usuario WHERE nombre=?", (cmd["nombre"],))
            return {"msg": f"Usuario '{cmd['nombre']}' eliminado" if r.affected_row_count else "Usuario no encontrado", "items": []}
        if acc == "E_CATEGORIA":
            r = await c.execute("DELETE FROM categoria WHERE nombre=?", (cmd["nombre"],))
            return {"msg": f"Categoría '{cmd['nombre']}' eliminada" if r.affected_row_count else "No encontrada", "items": []}
        if acc == "E_TAREA":
            r = await c.execute("DELETE FROM tarea WHERE id=?", (cmd["id"],))
            return {"msg": f"Tarea {cmd['id']} eliminada" if r.affected_row_count else "No encontrada", "items": []}

        return {"msg": "Comando no reconocido. Usa 'help' para ver la lista.", "items": []}
    except Exception as e:
        print(f"❌ DB Error: {e}", file=sys.stderr)
        return {"msg": f"Error interno: {e}", "items": []}