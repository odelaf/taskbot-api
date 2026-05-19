# database.py
# Gestor de SQLite para TaskBot - Compatible con Render y commands.py existente
import os
import sqlite3
from pathlib import Path

# 📁 Determinar ruta de la BD
_env_path = os.getenv("DB_PATH")
if _env_path:
    DB_PATH = Path(_env_path)
else:
    DB_PATH = Path.cwd() / "data" / "tareas.db"

# Asegurar directorio padre
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db():
    """
    Devuelve una conexión SQLite directa (compatible con commands.py).
    El caller es responsable de commit() y close().
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Permite row["columna"]
    return conn


def init_db():
    """Inicializa el esquema (idempotente)."""
    conn = get_db()
    try:
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
        
        # ── Índices ──
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tareas_estado ON tareas(estado)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tareas_categoria ON tareas(categoria_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tareas_asignado ON tareas(asignado_a)")
        
        # ── Optimización ──
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        
        conn.commit()
    finally:
        conn.close()


def reset_db():
    """⚠️ BORRA TODOS LOS DATOS. Solo para desarrollo."""
    if DB_PATH.exists():
        DB_PATH.unlink()
        for ext in ["-wal", "-shm"]:
            p = DB_PATH.with_suffix(DB_PATH.suffix + ext)
            if p.exists():
                p.unlink()
        init_db()
        return "✅ BD reiniciada."
    return "⚠️ No existía BD para reiniciar."