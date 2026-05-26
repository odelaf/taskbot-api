# commands.py
import sys
import database as db

def parsear(texto: str) -> dict | None:
    p = [x.strip() for x in texto.split("::") if x.strip()]
    if not p: return None

    # id::estado (ej: 5::0, 12::1, 3::null)
    if len(p) == 2 and p[0].isdigit() and p[1].lower() in ("0", "1", "null"):
        return {"accion": "ESTADO", "id": int(p[0]), "estado": p[1]}

    # Supermercado
    if p == ["s"]: return {"accion": "S_LIST"}
    if len(p) == 3 and p[0].lower() == "s" and p[1].isdigit() and p[2] in ("0", "1"):
        return {"accion": "S_STATE", "id": int(p[1]), "existencia": int(p[2])}

    acc = p[0].upper()
    if acc == "C":
        if len(p) >= 3 and p[1].upper() == "U": return {"accion": "C_USUARIO", "nombre": p[2]}
        if len(p) >= 3 and p[1].upper() == "C": return {"accion": "C_CATEGORIA", "nombre": p[2]}
        if len(p) >= 3: # c::categoria::desc::[estado]
            est = int(p[3]) if len(p) > 3 and p[3] in ("0","1") else None
            return {"accion": "C_TAREA", "cat": p[1], "desc": p[2], "estado": est}
    elif acc == "K":
        if len(p) == 2 and p[1].upper() == "U": return {"accion": "K_USUARIOS"}
        if len(p) == 3 and p[1].upper() == "U": return {"accion": "K_USUARIO_TAREAS", "usuario": p[2]}
        if len(p) == 2 and p[1].upper() == "C": return {"accion": "K_CATEGORIAS"}
        if len(p) == 2 and p[1].upper() != "T": return {"accion": "K_CAT_TAREAS", "cat": p[1]}
        if len(p) == 3 and p[2] in ("0","1"): return {"accion": "K_CAT_ESTADO", "cat": p[1], "estado": int(p[2])}
        if p[1].upper() == "T" and len(p) == 2: return {"accion": "K_TODAS"}
        if p[1].upper() == "T" and len(p) == 3 and p[2] in ("0","1"): return {"accion": "K_ESTADO_GLOBAL", "estado": int(p[2])}
    elif acc == "E":
        if len(p) == 3 and p[1].upper() == "U": return {"accion": "E_USUARIO", "nombre": p[2]}
        if len(p) == 3 and p[1].upper() == "C": return {"accion": "E_CATEGORIA", "nombre": p[2]}
        if len(p) == 3 and p[1].upper() == "T": return {"accion": "E_TAREA", "id": int(p[2])}

    return None

async def ejecutar(cmd: dict):
    c = db.get_db()
    acc, p = cmd["accion"], cmd
    try:
        if acc == "ESTADO":
            if p["estado"] == "null":
                await c.execute("UPDATE tarea SET estado=NULL, actualizado_en=datetime('now') WHERE id=?", (p["id"],))
                return {"msg": f"Tarea {p['id']} → estado limpiado", "items": []}
            comp = "datetime('now')" if p["estado"]=="1" else None
            await c.execute("UPDATE tarea SET estado=?, actualizado_en=datetime('now'), completada_en=? WHERE id=?",
                            (int(p["estado"]), comp, p["id"]))
            return {"msg": f"Tarea {p['id']} → {'completada' if p['estado']=='1' else 'pendiente'}", "items": []}

        if acc == "S_LIST":
            res = await c.execute("SELECT id, chino, pinyin, español FROM supermercado WHERE existencia=0 OR existencia IS NULL ORDER BY id")
            return {"msg": f"{len(res.rows)} pendientes", "items": res.rows}
        if acc == "S_STATE":
            await c.execute("UPDATE supermercado SET existencia=?, actualizado_en=datetime('now') WHERE id=?", (p["existencia"], p["id"]))
            return {"msg": f"Item {p['id']} → {'comprado' if p['existencia']==1 else 'pendiente'}", "items": []}

        if acc == "C_USUARIO":
            await c.execute("INSERT OR IGNORE INTO usuario (nombre) VALUES (?)", (p["nombre"],))
            return {"msg": f"Usuario '{p['nombre']}' creado", "items": []}
        if acc == "C_CATEGORIA":
            await c.execute("INSERT OR IGNORE INTO categoria (nombre) VALUES (?)", (p["nombre"],))
            return {"msg": f"Categoría '{p['nombre']}' creada", "items": []}
        if acc == "C_TAREA":
            cat_res = await c.execute("SELECT id FROM categoria WHERE nombre=?", (p["cat"],))
            if not cat_res.rows: return {"msg": f"Categoría '{p['cat']}' no existe", "items": []}
            await c.execute("INSERT INTO tarea (categoria_id, usuario_id, descripcion, prioridad, estado) VALUES (?, NULL, ?, 3, ?)",
                            (cat_res.rows[0]["id"], p["desc"], p["estado"]))
            return {"msg": f"Tarea '{p['desc']}' en '{p['cat']}'", "items": []}

        if acc == "K_USUARIOS":
            res = await c.execute("SELECT id, nombre FROM usuario ORDER BY nombre")
            return {"msg": f"{len(res.rows)} usuarios", "items": res.rows}
        if acc == "K_USUARIO_TAREAS":
            uid = await c.execute("SELECT id FROM usuario WHERE nombre=?", (p["usuario"],))
            if not uid.rows: return {"msg": f"Usuario '{p['usuario']}' no encontrado", "items": []}
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, c.nombre as categoria
                FROM tarea t JOIN categoria c ON t.categoria_id=c.id WHERE t.usuario_id=? AND t.estado=0""", (uid.rows[0]["id"],))
            return {"msg": f"{len(res.rows)} pendientes para {p['usuario']}", "items": res.rows}
        if acc == "K_CATEGORIAS":
            res = await c.execute("SELECT id, nombre FROM categoria ORDER BY nombre")
            return {"msg": f"{len(res.rows)} categorías", "items": res.rows}
        if acc == "K_CAT_TAREAS":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, t.estado, t.usuario_id FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id WHERE c.nombre=? ORDER BY t.id""", (p["cat"],))
            return {"msg": f"{len(res.rows)} tareas en '{p['cat']}'", "items": res.rows}
        if acc == "K_CAT_ESTADO":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, t.usuario_id FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id WHERE c.nombre=? AND t.estado=? ORDER BY t.id""", (p["cat"], p["estado"]))
            tipo = "pendientes" if p["estado"]==0 else "completadas"
            return {"msg": f"{len(res.rows)} {tipo} en '{p['cat']}'", "items": res.rows}
        if acc == "K_TODAS":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, t.estado, c.nombre as categoria FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id ORDER BY c.nombre, t.id""")
            return {"msg": f"{len(res.rows)} tareas totales", "items": res.rows}
        if acc == "K_ESTADO_GLOBAL":
            res = await c.execute("""SELECT t.id, t.descripcion, t.prioridad, c.nombre as categoria FROM tarea t
                JOIN categoria c ON t.categoria_id=c.id WHERE t.estado=? ORDER BY c.nombre, t.id""", (p["estado"],))
            tipo = "pendientes" if p["estado"]==0 else "completadas"
            return {"msg": f"{len(res.rows)} tareas {tipo}", "items": res.rows}

        if acc == "E_USUARIO":
            r = await c.execute("DELETE FROM usuario WHERE nombre=?", (p["nombre"],))
            return {"msg": f"Usuario '{p['nombre']}' eliminado" if r.affected_row_count else "Usuario no encontrado", "items": []}
        if acc == "E_CATEGORIA":
            r = await c.execute("DELETE FROM categoria WHERE nombre=?", (p["nombre"],))
            return {"msg": f"Categoría '{p['nombre']}' eliminada" if r.affected_row_count else "No encontrada", "items": []}
        if acc == "E_TAREA":
            r = await c.execute("DELETE FROM tarea WHERE id=?", (p["id"],))
            return {"msg": f"Tarea {p['id']} eliminada" if r.affected_row_count else "No encontrada", "items": []}

        return {"msg": "Comando no reconocido", "items": []}
    except Exception as e:
        print(f"❌ DB Error: {e}", file=sys.stderr)
        return {"msg": f"Error interno: {e}", "items": []}