# commands.py
# Adaptado para Turso (libsql-client async) + FastAPI
import logging
import database as db

logger = logging.getLogger(__name__)

def parsear(mensaje: str) -> dict | None:
    """Parser robusto: ignora vacíos, soporta comandos de una palabra y filtra respuestas del bot."""
    msg = mensaje.strip()
    msg_lower = msg.lower()
    
    # 🛡️ Ignorar respuestas del bot o mensajes de error
    if msg.startswith(("⚠️", "✅", "❌", "📁", "📋", "🚨", "🟢", "🗑️", "🔄")):
        return None
    if any(frase in msg_lower for frase in ["comando no reconocido", "formato:", "acción::parte"]):
        return None
    
    # 🆘 Soporte para help/ayuda
    if msg_lower in ("help", "ayuda", "?", "!help", "!ayuda"):
        return {"accion": "HELP", "partes": []}
    
    # Parser normal
    partes = [p.strip() for p in msg.split("::") if p.strip()]
    if len(partes) < 2:
        return None
    
    return {
        "accion": partes[0].upper(),
        "partes": partes[1:]
    }

async def ejecutar(cmd: dict) -> str:
    acc = cmd["accion"]
    p = cmd["partes"]
    client = db.get_db()  # Retorna el cliente async de Turso
    
    try:
        # ── HELP ──
        if acc == "HELP":
            return (
                "📋 *Comandos disponibles:*\n"
                "• `CREAR::USUARIO::alias`\n"
                "• `CREAR::CAT::nombre`\n"
                "• `CREAR::TAREA::categoria::desc1;desc2`\n"
                "• `ASIGNAR::ID1;ID2::alias`\n"
                "• `ELIMINAR::USUARIO::alias` | `ELIMINAR::CAT::nombre` | `ELIMINAR::TAREA::ID1;ID2`\n"
                "• `ESTADO::ID1;ID2::0|1` (0=pendiente, 1=completada)\n"
                "• `CONSULTA::CAT` | `CONSULTA::PENDIENTES` | `CONSULTA::PENDIENTES::categoria`\n"
                "• `CONSULTA::alias_usuario`"
            )

        # ── USUARIOS ──
        if acc == "CREAR" and len(p) >= 2 and p[0].upper() == "USUARIO":
            alias = p[1]
            if not alias: return "⚠️ Formato: `CREAR::USUARIO::alias`"
            await client.execute("INSERT OR IGNORE INTO usuarios (alias, matrix_id) VALUES (?, ?)", (alias, f"@{alias}:matrix.org"))
            return f"✅ Usuario `{alias}` registrado."

        if acc == "ELIMINAR" and len(p) >= 2 and p[0].upper() == "USUARIO":
            alias = p[1]
            res = await client.execute("DELETE FROM usuarios WHERE alias=?", (alias,))
            return f"🗑️ Usuario `{alias}` eliminado." if res.affected_row_count else f"⚠️ Usuario `{alias}` no encontrado."

        # ── CATEGORÍAS ──
        if acc == "CREAR" and len(p) >= 2 and p[0].upper() == "CAT":
            nombre = p[1]
            if not nombre: return "⚠️ Formato: `CREAR::CAT::nombre`"
            await client.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (nombre,))
            return f"📁 Categoría `{nombre}` creada."

        if acc == "ELIMINAR" and len(p) >= 2 and p[0].upper() == "CAT":
            nombre = p[1]
            tareas_res = await client.execute("SELECT COUNT(*) as total FROM tareas WHERE categoria_id=(SELECT id FROM categorias WHERE nombre=?)", (nombre,))
            if tareas_res.rows[0]["total"] > 0:
                return f"⚠️ No se puede eliminar `{nombre}`: tiene {tareas_res.rows[0]['total']} tarea(s)."
            res = await client.execute("DELETE FROM categorias WHERE nombre=?", (nombre,))
            return f"🗑️ Categoría `{nombre}` eliminada." if res.affected_row_count else f"⚠️ Categoría `{nombre}` no encontrada."

        # ── TAREAS: CREAR ──
        if acc == "CREAR" and len(p) >= 2 and p[0].upper() == "TAREA":
            if len(p) < 3:
                return "⚠️ Falta asignar categoría. Usa: `CREAR::TAREA::categoria::descripcion`"
            categoria = p[1]
            descripciones = [d.strip() for d in p[2].split(";") if d.strip()]
            
            cat_res = await client.execute("SELECT id FROM categorias WHERE nombre=?", (categoria,))
            if not cat_res.rows:
                return f"⚠️ Categoría `{categoria}` no existe. Créala con `CREAR::CAT::{categoria}`"
            
            cat_id = cat_res.rows[0]["id"]
            ids = []
            for desc in descripciones:
                ins_res = await client.execute(
                    "INSERT INTO tareas (categoria_id, contenido, estado, asignado_a) VALUES (?, ?, 'pendiente', 'sin_asignar')",
                    (cat_id, desc)
                )
                ids.append(ins_res.last_insert_rowid)
            
            lista = "\n".join(f"• `{tid}` → {desc}" for tid, desc in zip(ids, descripciones))
            return f"✅ {len(descripciones)} tarea(s) en `{categoria}`:\n{lista}"

        # ── TAREAS: ASIGNAR ──
        if acc == "ASIGNAR" and len(p) >= 2:
            ids_str = p[0]
            alias = p[1]
            user_res = await client.execute("SELECT alias FROM usuarios WHERE alias=?", (alias,))
            if not user_res.rows:
                return f"⚠️ Usuario `{alias}` no registrado."
            
            ids = [i.strip() for i in ids_str.split(";") if i.strip()]
            resultados = []
            for tid in ids:
                try:
                    tid_int = int(tid)
                    res = await client.execute("UPDATE tareas SET asignado_a=? WHERE id=?", (alias, tid_int))
                    resultados.append(f"`{tid}`→@{alias}" if res.affected_row_count else f"`{tid}`❌")
                except ValueError:
                    resultados.append(f"`{tid}`❌(ID inválido)")
            return f"✅ Asignadas: {', '.join(resultados)}"

        # ── TAREAS: ELIMINAR ──
        if acc == "ELIMINAR" and len(p) >= 2 and p[0].upper() == "TAREA":
            ids_str = p[1]
            ids = [i.strip() for i in ids_str.split(";") if i.strip()]
            resultados = []
            for tid in ids:
                try:
                    tid_int = int(tid)
                    res = await client.execute("DELETE FROM tareas WHERE id=?", (tid_int,))
                    resultados.append(f"`{tid}`🗑️" if res.affected_row_count else f"`{tid}`❌")
                except ValueError:
                    resultados.append(f"`{tid}`❌(ID inválido)")
            return f"✅ Eliminadas: {', '.join(resultados)}"

        # ── TAREAS: ESTADO ──
        if acc == "ESTADO" and len(p) >= 2:
            ids_str = p[0]
            estado_valor = p[1]
            if estado_valor not in ("0", "1"):
                return "⚠️ Estado válido: `0` (pendiente) o `1` (completada)"
            
            estado_texto = "completada" if estado_valor == "1" else "pendiente"
            ids = [i.strip() for i in ids_str.split(";") if i.strip()]
            resultados = []
            
            for tid in ids:
                try:
                    tid_int = int(tid)
                    if estado_valor == "1":
                        res = await client.execute(
                            "UPDATE tareas SET estado='completada', completada_en=datetime('now') WHERE id=?", 
                            (tid_int,)
                        )
                    else:
                        res = await client.execute(
                            "UPDATE tareas SET estado='pendiente', completada_en=NULL WHERE id=?", 
                            (tid_int,)
                        )
                    resultados.append(f"`{tid}`→{estado_texto}" if res.affected_row_count else f"`{tid}`❌")
                except ValueError:
                    resultados.append(f"`{tid}`❌(ID inválido)")
            return f"✅ Actualizadas: {', '.join(resultados)}"

        # ── CONSULTAS ──
        if acc == "CONSULTA":
            if not p:
                return "⚠️ Usa: `CONSULTA::CAT` | `CONSULTA::PENDIENTES` | `CONSULTA::PENDIENTES::categoria` | `CONSULTA::alias`"
            
            tipo = p[0].upper()
            if tipo == "CAT":
                cats = await client.execute("SELECT id, nombre FROM categorias ORDER BY nombre")
                return "📂 Categorías:\n" + "\n".join(f"• ID `{c['id']}` → `{c['nombre']}`" for c in cats.rows) or "📂 Sin categorías."

            elif tipo == "PENDIENTES":
                if len(p) > 1:
                    cat_name = p[1]
                    cat_res = await client.execute("SELECT id FROM categorias WHERE nombre=?", (cat_name,))
                    if not cat_res.rows: return f"⚠️ Categoría `{cat_name}` no encontrada."
                    
                    tasks = await client.execute(
                        "SELECT id, contenido, prioridad, asignado_a FROM tareas WHERE categoria_id=? AND estado='pendiente' ORDER BY prioridad DESC, creado_en ASC",
                        (cat_res.rows[0]["id"],)
                    )
                    return f"📋 Pendientes en `{cat_name}`:\n" + "\n".join(
                        f"• `{t['id']}` [{t['prioridad'].upper()}] @{t['asignado_a']} → {t['contenido']}" for t in tasks.rows
                    ) if tasks.rows else f"🟢 Nada pendiente en `{cat_name}`."
                else:
                    tasks = await client.execute("""
                        SELECT t.id, t.contenido, t.prioridad, t.asignado_a, c.nombre as categoria
                        FROM tareas t JOIN categorias c ON t.categoria_id = c.id
                        WHERE t.estado = 'pendiente' ORDER BY c.nombre, t.prioridad DESC
                    """)
                    if not tasks.rows: return "🟢 No hay tareas pendientes."
                    
                    grouped = {}
                    for t in tasks.rows: grouped.setdefault(t['categoria'], []).append(t)
                    
                    lines = ["📋 *Todas las tareas pendientes:*"]
                    for cat_name, items in grouped.items():
                        lines.append(f"\n📁 `{cat_name}`:")
                        for t in items: lines.append(f"• `{t['id']}` [{t['prioridad'].upper()}] @{t['asignado_a']} → {t['contenido']}")
                    return "\n".join(lines)
            else:
                alias = p[0]
                user_res = await client.execute("SELECT alias FROM usuarios WHERE alias=?", (alias,))
                if user_res.rows:
                    tasks = await client.execute("""
                        SELECT t.id, t.contenido, t.prioridad, c.nombre as categoria
                        FROM tareas t JOIN categorias c ON t.categoria_id = c.id
                        WHERE t.asignado_a = ? AND t.estado = 'pendiente' ORDER BY c.nombre
                    """, (alias,))
                    if not tasks.rows: return f"🟢 @{alias} no tiene tareas pendientes."
                    lines = [f"📋 *Pendientes de @{alias}:*"]
                    for t in tasks.rows: lines.append(f"• `{t['id']}` [{t['prioridad'].upper()}] `{t['categoria']}` → {t['contenido']}")
                    return "\n".join(lines)
                else:
                    return "⚠️ Alias no registrado o formato inválido."

        return "⚠️ Comando no reconocido. Usa `help`."

    except Exception as e:
        logger.error(f"❌ Error ejecutando {acc}: {e}")
        return f"❌ Error interno: {e}"