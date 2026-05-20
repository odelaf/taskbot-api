# database.py - DEBUG VERSION
import os
import sys

print("🔥 DB DEBUG: database.py cargado", file=sys.stderr)
sys.stderr.flush()

try:
    import libsql_client
    print("✅ DB DEBUG: libsql_client importado", file=sys.stderr)
    sys.stderr.flush()
except ImportError as e:
    print(f"❌ DB CRASH: libsql-client no instalado: {e}", file=sys.stderr)
    sys.stderr.flush()
    sys.exit(1)

_client = None

def get_db():
    """Retorna el cliente Turso, inicializándolo si es necesario."""
    global _client
    if _client is None:
        url = os.getenv("TURSO_DATABASE_URL")
        token = os.getenv("TURSO_AUTH_TOKEN")
        
        # 🔥 Forzar HTTPS para evitar WebSocket 505 en Render y local
        if url and url.startswith("libsql://"):
            url = url.replace("libsql://", "https://", 1)
        
        _client = libsql_client.create_client(url=url, auth_token=token)
    return _client

async def init_db():
    print("🔥 DB DEBUG: init_db() iniciado", file=sys.stderr)
    sys.stderr.flush()
    client = get_db()
    
    try:
        await client.execute("CREATE TABLE IF NOT EXISTS usuarios (alias TEXT PRIMARY KEY, matrix_id TEXT DEFAULT '', creado_en DATETIME DEFAULT CURRENT_TIMESTAMP)")
        print("✅ DB DEBUG: tabla usuarios creada", file=sys.stderr)
        sys.stderr.flush()
        
        await client.execute("CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL, creado_en DATETIME DEFAULT CURRENT_TIMESTAMP)")
        print("✅ DB DEBUG: tabla categorias creada", file=sys.stderr)
        sys.stderr.flush()
        
        await client.execute("CREATE TABLE IF NOT EXISTS tareas (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria_id INTEGER NOT NULL, contenido TEXT NOT NULL, estado TEXT DEFAULT 'pendiente', prioridad TEXT DEFAULT 'media', asignado_a TEXT DEFAULT 'sin_asignar', creado_en DATETIME DEFAULT CURRENT_TIMESTAMP, completada_en DATETIME, FOREIGN KEY(categoria_id) REFERENCES categorias(id))")
        print("✅ DB DEBUG: tabla tareas creada", file=sys.stderr)
        sys.stderr.flush()
        
        print("✅ DB DEBUG: Todas las tablas creadas", file=sys.stderr)
        sys.stderr.flush()
        
    except Exception as e:
        print(f"❌ DB ERROR creando tablas: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback; traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise