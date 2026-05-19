# database.py
# Gestor de SQLite para TaskBot - Compatible con Render Free Tier y local
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# 📁 Determinar ruta de la BD:
# 1. Variable de entorno DB_PATH (Render, Docker, etc.)
# 2. Fallback: directorio local 'data' relativo al script
_env_path = os.getenv("DB_PATH")
if _env_path:
    DB_PATH = Path(_env_path)
else:
    # Fallback relativo al directorio donde se ejecuta el script
    DB_PATH = Path.cwd() / "data" / "tareas.db"

# Asegurar que el directorio padre existe y es escribible
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

@contextmanager
def get_db():
    """Context manager para conexiones SQLite con row_factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Permite acceso por nombre: row["id"]
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Inicializa el esquema de la base de datos (idempotente)."""
    with get_db() as conn:
        # ── Usuarios ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                alias TEXT PRIMARY KEY,
                matrix_id TEXT DEFAULT '',
                creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ── Categorías ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ── Tareas ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria_id INTEGER NOT NULL,
                contenido TEXT NOT NULL,
                estado TEXT DEFAULT 'pendiente' CHECK(estado IN ('pendiente', 'completada')),
                prioridad TEXT DEFAULT 'media' CHECK(prioridad IN ('baja', 'media', 'alta')),
                asignado_a TEXT DEFAULT 'sin_asignar',
                creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                completada_en DATETIME,
                FOREIGN KEY(categoria_id) REFERENCES categorias(id) ON DELETE CASCADE
            )
        """)
        
        # ── Índices para consultas frecuentes ──
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tareas_estado ON tareas(estado)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tareas_categoria ON tareas(categoria_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tareas_asignado ON tareas(asignado_a)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tareas_creado ON tareas(creado_en DESC)")
        
        # ── Optimización SQLite ──
        conn.execute("PRAGMA journal_mode=WAL;")  # Mejor concurrencia
        conn.execute("PRAGMA synchronous=NORMAL;")  # Balance rendimiento/seguridad
        conn.execute("PRAGMA foreign_keys=ON;")  # Activar claves foráneas

def reset_db():
    """⚠️ BORRA TODOS LOS DATOS. Solo para desarrollo/testing."""
    if DB_PATH.exists():
        DB_PATH.unlink()
        # Eliminar archivos WAL/SHM si existen
        for ext in ["-wal", "-shm"]:
            p = DB_PATH.with_suffix(DB_PATH.suffix + ext)
            if p.exists():
                p.unlink()
        init_db()
        return "✅ Base de datos reiniciada."
    return "⚠️ No existía base de datos para reiniciar."

# ── Helpers de consulta (opcionales, para usar directamente si necesitas) ──

def obtener_categorias():
    """Lista todas las categorías."""
    with get_db() as conn:
        return conn.execute("SELECT id, nombre FROM categorias ORDER BY nombre").fetchall()

def obtener_tareas_pendientes(categoria_id=None, asignado_a=None, limit=50):
    """Consulta tareas pendientes con filtros opcionales."""
    query = """
        SELECT t.id, t.contenido, t.prioridad, t.asignado_a, t.creado_en, c.nombre as categoria
        FROM tareas t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.estado = 'pendiente'
    """
    params = []
    if categoria_id:
        query += " AND t.categoria_id = ?"
        params.append(categoria_id)
    if asignado_a:
        query += " AND t.asignado_a = ?"
        params.append(asignado_a)
    query += " ORDER BY t.prioridad DESC, t.creado_en ASC LIMIT ?"
    params.append(limit)
    
    with get_db() as conn:
        return conn.execute(query, params).fetchall()

def contar_pendientes_por_categoria():
    """Retorna dict: {categoria: count_pendientes}."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT c.nombre, COUNT(t.id) as total
            FROM categorias c
            LEFT JOIN tareas t ON c.id = t.categoria_id AND t.estado = 'pendiente'
            GROUP BY c.id
            ORDER BY c.nombre
        """).fetchall()
        return {row["nombre"]: row["total"] for row in rows}