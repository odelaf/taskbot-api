# database.py
# Persistente con Turso (libSQL) + FastAPI async
import os
import libsql_client

# Cliente global único (reutilizable)
_client = None

def get_db():
    """Retorna el cliente Turso, inicializándolo si es necesario."""
    global _client
    if _client is None:
        _client = libsql_client.create_client(
            url=os.getenv("TURSO_DATABASE_URL"),
            auth_token=os.getenv("TURSO_AUTH_TOKEN")
        )
    return _client

async def init_db():
    """Inicializa el esquema (idempotente). Se llama al startup de FastAPI."""
    client = get_db()
    
    await client.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            alias TEXT PRIMARY KEY,
            matrix_id TEXT DEFAULT '',
            creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await client.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await client.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL,
            contenido TEXT NOT NULL,
            estado TEXT DEFAULT 'pendiente' CHECK(estado IN ('pendiente', 'completada')),
            prioridad TEXT DEFAULT 'media' CHECK(prioridad IN ('baja', 'media', 'alta')),
            asignado_a TEXT DEFAULT 'sin_asignar',
            creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
            completada_en DATETIME,
            FOREIGN KEY(categoria_id) REFERENCES categorias(id)
        )
    """)
    
    # Índices para consultas rápidas
    await client.execute("CREATE INDEX IF NOT EXISTS idx_tareas_estado ON tareas(estado)")
    await client.execute("CREATE INDEX IF NOT EXISTS idx_tareas_categoria ON tareas(categoria_id)")
    
    print("✅ BD persistente inicializada en Turso")