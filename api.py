# api.py - DEBUG VERSION (imprime TODO antes de crashear)
import sys
import os

# 🔥 DEBUG: Esto se ejecuta AL IMPORTAR el módulo, antes de cualquier código
print("🔥 DEBUG: api.py cargado", file=sys.stderr)
sys.stderr.flush()

# Forzar que el directorio actual esté en el path
sys.path.insert(0, os.getcwd())
print(f"🔥 DEBUG: CWD={os.getcwd()}, PATH={sys.path[:3]}", file=sys.stderr)
sys.stderr.flush()

# Intentar importar y capturar CUALQUIER error
try:
    print("🔥 DEBUG: Intentando importar database...", file=sys.stderr)
    sys.stderr.flush()
    import database
    print("✅ DEBUG: database importado", file=sys.stderr)
    sys.stderr.flush()
except Exception as e:
    print(f"❌ CRASH AL IMPORTAR database: {type(e).__name__}: {e}", file=sys.stderr)
    import traceback; traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    # No hacemos sys.exit() para que uvicorn pueda arrancar y mostrar el error en /health

try:
    print("🔥 DEBUG: Intentando importar commands...", file=sys.stderr)
    sys.stderr.flush()
    import commands
    print("✅ DEBUG: commands importado", file=sys.stderr)
    sys.stderr.flush()
except Exception as e:
    print(f"❌ CRASH AL IMPORTAR commands: {type(e).__name__}: {e}", file=sys.stderr)
    import traceback; traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()

# Ahora sí, importar FastAPI (si llegamos aquí, los imports locales funcionaron)
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

print("🔥 DEBUG: FastAPI importado, definiendo app...", file=sys.stderr)
sys.stderr.flush()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print("🚀 lifespan: iniciando...", file=sys.stderr)
        sys.stderr.flush()
        await database.init_db()
        print("✅ lifespan: BD inicializada", file=sys.stderr)
        sys.stderr.flush()
        yield
    except Exception as e:
        print(f"❌ lifespan CRASH: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback; traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise

app = FastAPI(title="TaskBot API", version="1.0", lifespan=lifespan)

class CommandInput(BaseModel):
    texto: str

@app.get("/")
def root():
    return {"status": "ok", "service": "TaskBot API"}

@app.get("/health")
def health():
    return {"status": "healthy", "python": sys.version}

@app.post("/ejecutar")
async def ejecutar_comando(input: CommandInput):
    try:
        cmd = commands.parsear(input.texto)
        if not cmd:
            return {"error": "Formato inválido"}
        resultado = await commands.ejecutar(cmd)
        return {"resultado": resultado}
    except Exception as e:
        print(f"❌ /ejecutar error: {e}", file=sys.stderr)
        import traceback; traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/consultar")
async def consultar(tipo: str = "PENDIENTES", filtro: str | None = None):
    try:
        cmd_texto = f"CONSULTA::{tipo}::{filtro}" if filtro else f"CONSULTA::{tipo}"
        cmd = commands.parsear(cmd_texto)
        if not cmd:
            raise HTTPException(status_code=400, detail="Consulta inválida")
        resultado = await commands.ejecutar(cmd)
        return {"resultado": resultado}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ /consultar error: {e}", file=sys.stderr)
        import traceback; traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail=str(e))

print("🔥 DEBUG: Fin de api.py alcanzado", file=sys.stderr)
sys.stderr.flush()