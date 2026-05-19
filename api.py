# api.py
# TaskBot API - FastAPI wrapper para commands.py + SQLite
# Compatible con Render.com Free Tier (sin Persistent Disk)

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 🎯 Definir 'app' PRIMERO (lo que busca uvicorn)
app = FastAPI(title="TaskBot API", version="1.0")

# 📁 Ruta de BD: directorio actual (escribible en Render)
# ⚠️ Nota Free Tier: Los datos se pierden al redeployar. 
# Para persistencia real, usa Turso/Supabase o upgrade a Render Paid.
DATA_DIR = Path.cwd() / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "tareas.db"
os.environ["DB_PATH"] = str(DB_PATH)

# 📦 Importar lógica local
try:
    import database
    import commands
except ImportError as e:
    print(f"❌ Error importando módulos: {e}", file=sys.stderr)
    print(f"📂 Archivos en directorio: {list(Path('.').iterdir())}", file=sys.stderr)
    raise

# Inicializar BD al arrancar
try:
    # Forzar uso de la ruta correcta en database.py
    database.DB_PATH = DB_PATH
    database.init_db()
    print(f"✅ BD inicializada en {DB_PATH}")
except Exception as e:
    print(f"❌ Error inicializando BD: {e}", file=sys.stderr)
    raise

# ── Modelos ──
class CommandInput(BaseModel):
    texto: str

# ── Endpoints ──
@app.get("/")
def root():
    return {"status": "ok", "service": "TaskBot API", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy", "db_path": str(DB_PATH)}

@app.post("/ejecutar")
def ejecutar_comando(input: CommandInput):
    try:
        cmd = commands.parsear(input.texto)
        if not cmd:
            return {"error": "Formato inválido"}
        resultado = commands.ejecutar(cmd)
        return {"resultado": resultado}
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/consultar")
def consultar(tipo: str = "PENDIENTES", filtro: str | None = None):
    try:
        cmd_texto = f"CONSULTA::{tipo}::{filtro}" if filtro else f"CONSULTA::{tipo}"
        cmd = commands.parsear(cmd_texto)
        if not cmd:
            raise HTTPException(status_code=400, detail="Consulta inválida")
        resultado = commands.ejecutar(cmd)
        return {"resultado": resultado}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error consulta: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))