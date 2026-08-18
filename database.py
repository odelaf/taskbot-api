# database.py
import os, sys, logging
import libsql_client

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

_client = None

def get_db():
    global _client
    if _client is None:
        url = os.getenv("TURSO_DATABASE_URL")
        token = os.getenv("TURSO_AUTH_TOKEN")
        if url and url.startswith("libsql://"):
            url = url.replace("libsql://", "https://", 1)
        _client = libsql_client.create_client(url=url, auth_token=token)
    return _client


async def close_db():
    global _client
    if _client is not None:
        await _client.close()
        _client = None

async def init_db():
    c = get_db()
    await c.execute("""CREATE TABLE IF NOT EXISTS usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    await c.execute("""CREATE TABLE IF NOT EXISTS categoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    await c.execute("""CREATE TABLE IF NOT EXISTS tarea (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria_id INTEGER NOT NULL,
        usuario_id INTEGER,
        descripcion TEXT NOT NULL,
        prioridad INTEGER DEFAULT 3 CHECK(prioridad BETWEEN 1 AND 5),
        estado INTEGER CHECK(estado IN (0, 1)),
        creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
        actualizado_en DATETIME,
        completada_en DATETIME,
        FOREIGN KEY(categoria_id) REFERENCES categoria(id) ON DELETE CASCADE,
        FOREIGN KEY(usuario_id) REFERENCES usuario(id) ON DELETE SET NULL
    )""")
    await c.execute("""CREATE TABLE IF NOT EXISTS supermercado (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chino TEXT NOT NULL,
        pinyin TEXT,
        español TEXT,
        existencia INTEGER CHECK(existencia IN (0, 1)),
        creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
        actualizado_en DATETIME
    )""")
    # Índices para rendimiento
    await c.execute("CREATE INDEX IF NOT EXISTS idx_tarea_cat ON tarea(categoria_id)")
    await c.execute("CREATE INDEX IF NOT EXISTS idx_tarea_usr ON tarea(usuario_id)")
    await c.execute("CREATE INDEX IF NOT EXISTS idx_tarea_estado ON tarea(estado)")
    await c.execute("CREATE INDEX IF NOT EXISTS idx_super_exist ON supermercado(existencia)")
    logger.info("BD Turso inicializada")