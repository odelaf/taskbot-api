# database.py
import sqlite3
import logging
from config import DB_PATH

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    alias TEXT PRIMARY KEY,
    matrix_id TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL COLLATE NOCASE,
    dueño_alias TEXT,
    creada_en TEXT DEFAULT (datetime('now', 'localtime'))
);
CREATE TABLE IF NOT EXISTS tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id INTEGER NOT NULL,
    contenido TEXT NOT NULL,
    estado TEXT CHECK(estado IN ('pendiente','completada','archivada')) DEFAULT 'pendiente',
    prioridad TEXT CHECK(prioridad IN ('baja','media','alta')) DEFAULT 'media',
    creado_por TEXT NOT NULL,
    asignado_a TEXT DEFAULT 'sin_asignar',
    fecha_limite TEXT,
    recordatorio_enviado INTEGER DEFAULT 0,
    creada_en TEXT DEFAULT (datetime('now', 'localtime')),
    completada_en TEXT,
    FOREIGN KEY(categoria_id) REFERENCES categorias(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_tareas_plazo 
    ON tareas(fecha_limite, estado, recordatorio_enviado) WHERE fecha_limite IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tareas_cat_estado 
    ON tareas(categoria_id, estado);
"""

def init_db():
    """Inicializa la BD y crea tablas si no existen (ejecutar 1 vez al arranque)."""
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(SCHEMA)
        logger.info("🗃️ Base de datos inicializada: %s", DB_PATH)
    finally:
        conn.close()

def get_db() -> sqlite3.Connection:
    """Retorna una conexión lista para usar (thread-safe por defecto en single-process)."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row  # Acceso por nombre: row["id"], row["estado"]
    return conn