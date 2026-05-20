# database.py
# Persistente con Turso (libSQL) + FastAPI async
import os
import sys

try:
    import libsql_client
except ImportError as e:
    print(f"❌ ERROR CRÍTICO: libsql-client no instalado. Detalle: {e}", file=sys.stderr)
    sys.exit(1)

_client = None

def get_db():
    """Retorna el cliente Turso, inicializándolo si es necesario."""
    global _client
    if _client is None:
        url = os.getenv("TURSO_DATABASE_URL")
        token = os.getenv("TURSO_AUTH_TOKEN")
        
        if not url or not token:
            print(f"❌ ERROR: Faltan variables de entorno.", file=sys.stderr)
            print(f"   TURSO_DATABASE_URL: {'✅' if url else '❌'}", file=sys.stderr)
            print(f"   TURSO_AUTH_TOKEN: {'✅' if token else '❌'}", file=sys.stderr)
            sys.exit(1)
        
        try:
            _client = libsql_client.create_client(url=url, auth_token=token)
            print("✅ Cliente Turso conectado", file=sys.stderr)
        except Exception as e:
            print(f"❌ ERROR conectando a Turso: {e}", file=sys.stderr)
            sys.exit(1)
    return _client

async def init_db():
    """Inicializa el esquema (idempotente)."""
    client = get_db()
    
    try:
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
        
        await client.execute("CREATE INDEX IF NOT EXISTS idx_tareas_estado ON tareas(estado)")
        await client.execute("CREATE INDEX IF NOT EXISTS idx_tareas_categoria ON tareas(categoria_id)")
        
        print("✅ Tablas creadas en Turso", file=sys.stderr)
        
    except Exception as e:
        print(f"❌ ERROR creando tablas: {e}", file=sys.stderr)
        import traceback; traceback.print_exc(file=sys.stderr)
        raise