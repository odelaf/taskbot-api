# commands.py
import sys
import logging
import database as db

# Configurar logging para Railway
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def _rows_to_dicts(rows):
    """ CRÍTICO: Convierte filas de libsql-client a lista de dicts para JSON."""
    if not rows:
        return []
    return [dict(row) for row in rows]

def parsear(texto: str) -> dict | None:
    texto = texto.strip()
    if not texto: return None

    # 🔹 HELP FLEXIBLE (acepta "help k", "help::k", "h c", etc.)
    lower_text = texto.lower()
    if lower_text.startswith(("help", "ayuda", "h", "?")):
        # Normaliza separadores a espacio solo para el comando help
        parts = [p.strip() for p in texto.replace("::", " ").split() if p.strip()]
        if parts and parts[0].lower() in ("help", "ayuda", "h", "?"):
            if len(parts) == 1:
                return {"accion": "HELP"}
            sub = parts[1].lower()
            if sub in ("c", "crear"): return {"accion": "HELP_C"}
            if sub in ("k", "consultar", "ver"): return {"accion": "HELP_K"}
            if sub in ("a", "asignar"): return {"accion": "HELP_A"}
            if sub in ("e", "eliminar", "borrar"): return {"accion": "HELP_E"}
            if sub in ("s", "super", "mercado"): return {"accion": "HELP_S"}
            if sub in ("estado", "status"): return {"accion": "HELP_ESTADO"}
            return {"accion": "HELP"}

    # 🔹 PARSER PRINCIPAL (Usa :: estrictamente para el resto de comandos)
    p = [x.strip() for x in texto.split("::") if x.strip()]
    if not p: return None

    primera = p[0].lower()

    # Estado: 5::0, 5::1, 5::null
    if len(p) == 2 and p[0].isdigit() and p[1].lower() in ("0", "1", "null"):
        return {"accion": "ESTADO", "id": int(p[0]), "estado": p[1]}

    # Supermercado
    if primera == "s" and len(p) == 1: return {"accion": "S_LIST"}
    if primera == "s" and len(p) == 3 and p[1].isdigit() and p[2] in ("0", "1"):
        return {"accion": "S_STATE", "id": int(p[1]), "existencia": int(p[2])}

    acc = p[0].upper()

    # Crear (C)
    if acc == "C" and len(p) >= 3:
        if p[1].upper() == "U": return {"accion": "C_USUARIO", "nombre": p[2]}
        if p[1].upper() == "C": return {"accion": "C_CATEGORIA", "nombre": p[2]}
        est = int(p[3]) if len(p) > 3 and p[3] in ("0", "1") else None
        return {"accion": "C_TAREA", "cat": p[1], "desc": p[2], "estado": est}

    # Consultar (K)
    elif acc == "K" and len(p) >= 2:
        if p[1].upper() == "U":
            return {"accion": "K_USUARIOS"} if len(p)==2 else {"accion": "K_USUARIO_TAREAS", "usuario": p[2]}
        if p[1].upper() == "C":
            return {"accion": "K_CATEGORIAS"} if len(p)==2 else {"accion": "K_CAT_ESTADO", "cat": p[1], "estado": int(p[2])}
        if p[1].upper() == "T":
            return {"accion": "K_TODAS"} if len(p)==2 else {"accion": "K_ESTADO_GLOBAL", "estado": int(p[2])}
        # Fallback para k::categoria
        return {"accion": "K_CAT_TAREAS", "cat": p[1]}

    # Asignar (A)
    elif acc == "A" and len(p) == 3 and p[1].isdigit():
        return {"accion": "ASIGNAR", "id": int(p[1]), "usuario": p[2]}

    # Eliminar (E)
    elif acc == "E" and len(p) == 3:
        if p[1].upper() == "U": return {"accion": "E_USUARIO", "nombre": p[2]}
        if p[1].upper() == "C": return {"accion": "E_CATEGORIA", "nombre": p[2]}
        if p[1].upper() == "T": return {"accion": "E_TAREA", "id": int(p[2])}

    return None

async def ejecutar(cmd: dict):
    c = db.get_db()
    acc = cmd["accion"]
    
    try:
                # 🔹 AYUDA GENERAL
        if acc == "HELP":
            return {"msg": (
                " **Significado de Prefijos:**\n"
                "🔹 **c** = Crear (Usuarios, Categorías, Tareas)\n"
                "🔹 **k** = Consultar (Ver listas, tareas pendientes)\n"
                "🔹 **a** = Asignar (Tarea a Usuario)\n"
                "🔹 **e** = Eliminar (Borrar registros)\n"
                "🔹 **s** = Supermercado (Lista de compras)\n"
                "🔹 **id::0|1|null** = Cambiar estado de tarea\n\n"
                "💡 Escribe **help [letra]** para ver la sintaxis.\n"
                "Ejemplo: `help c` o `help k`"
            ), "items": []}

        # 🔹 HELP CREAR (c)
        elif acc == "HELP_C":
            return {"msg": (
                "🛠️ **Sintaxis de Creación (c::)**\n\n"
                "👤 `c::u::nombre`\n   Crea un usuario.\n"
                "   Ej: `c::u::juan`\n\n"
                "📁 `c::c::nombre`\n   Crea una categoría.\n"
                "   Ej: `c::c::casa`\n\n"
                " `c::categoria::tarea::[0|1]`\n   Crea una tarea.\n"
                "   0=Pendiente, 1=Completada. Si omites el número, queda indefinido.\n"
                "   Ej: `c::casa::limpiar::0`"
            ), "items": []}

        # 🔹 HELP CONSULTAR (k)
        elif acc == "HELP_K":
            return {"msg": (
                "👁️ **Sintaxis de Consulta (k::)**\n\n"
                " `k::u` → Lista usuarios\n"
                "📋 `k::u::nombre` → Tareas pendientes de un usuario\n"
                "📋 `k::c` → Lista categorías\n"
                " `k::categoria` → Tareas de esa categoría\n"
                "📋 `k::categoria::0` → Pendientes de esa categoría\n"
                "📋 `k::t` → Todas las tareas\n"
                " `k::t::0` → Todas las pendientes"
            ), "items": []}

        # 🔹 HELP ASIGNAR (a)
        elif acc == "HELP_A":
            return {"msg": (
                "🔗 **Sintaxis de Asignación (a::)**\n\n"
                "👉 `a::id_tarea::usuario`\n\n"
                "Asigna una tarea existente a un usuario.\n"
                "Ej: `a::5::juan`"
            ), "items": []}

        # 🔹 HELP ELIMINAR (e)
        elif acc == "HELP_E":
            return {"msg": (
                "🗑️ **Sintaxis de Eliminación (e::)**\n\n"
                "👤 `e::u::nombre` → Borra usuario\n"
                "📁 `e::c::nombre` → Borra categoría (y sus tareas)\n"
                "📝 `e::t::id` → Borra tarea por ID"
            ), "items": []}

        # 🔹 HELP SUPERMERCADO (s)
        elif acc == "HELP_S":
            return {"msg": (
                "🛒 **Comandos de Supermercado (s)**\n\n"
                "📋 `s` → Muestra items pendientes (existencia 0)\n"
                "✅ `s::id::1` → Marca item como comprado\n"
                "❌ `s::id::0` → Marca item como pendiente"
            ), "items": []}

        # 🔹 HELP ESTADOS
        elif acc == "HELP_ESTADO":
            return {"msg": (
                "🔄 **Cambio de Estado**\n\n"
                " `id::0` → Pendiente\n"
                "👉 `id::1` → Completada\n"
                "👉 `id::null` → Limpia estado"
            ), "items": []}

        # 🔹 ASIGNAR
        if acc == "ASIGNAR":
            uid_res = await c.execute("SELECT id FROM usuario WHERE nombre=?", (cmd["usuario"],))
            if not uid_res.rows:
                return {"msg": f"Usuario '{cmd['usuario']}' no existe. Créalo con c::u::{cmd['usuario']}", "items": []}
            await c.execute("UPDATE tarea SET usuario_id=? WHERE id=?", (uid_res.rows[0]["id"], cmd["id"]))
            return {"msg": f"Tarea {cmd['id']} asignada a {cmd['usuario']}", "items": []}

        # 🔹 ESTADO
        if acc == "ESTADO":
            if cmd["estado"] == "null":
                await c.execute("UPDATE tarea SET estado=NULL, actualizado_en=datetime('now') WHERE id=?", (cmd["id"],))
                return {"msg": f"Tarea {cmd['id']} → estado limpiado", "items": []}
            comp = "datetime('now')" if cmd["estado"] == "1" else None
            await c.execute("UPDATE tarea SET estado=?, actualizado_en=datetime('now'), completada_en=? WHERE id=?",
                            (int(cmd["estado"]), comp, cmd["id"]))
            return {"msg": f"Tarea {cmd['id']} → {'completada' if cmd['estado']=='1' else 'pendiente'}", "items": []}

        # 🔹 SUPERMERCADO
        if acc == "S_LIST":
            res = await c.execute("SELECT id, chino, pinyin, español FROM supermercado WHERE existencia=0 OR existencia IS NULL ORDER BY id")
            return {"msg": f"{len(res.rows)} pendientes", "items": _rows_to_dicts(res.rows)}
        if acc == "S_STATE":
            await c.execute("UPDATE supermercado SET existencia=?, actualizado_en=datetime('now') WHERE id=?", (cmd["existencia"], cmd["id"]))
            return {"msg": f"Item {cmd['id']} → {'comprado' if cmd['existencia']==1 else 'pendiente'}", "items": []}

        # 🔹 CREAR
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

        # 🔹 CONSULTAR
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
            return {"msg": f"{len(res.rows)} categorías", "items": _rows_to_dicts(res.rows)}  # <-- Usa _rows_to_dicts
        
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

        # 🔹 ELIMINAR
        if acc == "E_USUARIO":
            r = await c.execute("DELETE FROM usuario WHERE nombre=?", (cmd["nombre"],))
            return {"msg": f"Usuario '{cmd['nombre']}' eliminado" if r.affected_row_count else "Usuario no encontrado", "items": []}
        if acc == "E_CATEGORIA":
            r = await c.execute("DELETE FROM categoria WHERE nombre=?", (cmd["nombre"],))
            return {"msg": f"Categoría '{cmd['nombre']}' eliminada" if r.affected_row_count else "No encontrada", "items": []}
        if acc == "E_TAREA":
            r = await c.execute("DELETE FROM tarea WHERE id=?", (cmd["id"],))
            return {"msg": f"Tarea {cmd['id']} eliminada" if r.affected_row_count else "No encontrada", "items": []}

        return {"msg": "Comando no reconocido. Usa 'help'.", "items": []}
    except Exception as e:
        logger.error(f"❌ DB Error en {acc}: {e}")
        return {"msg": f"Error interno: {e}", "items": []}