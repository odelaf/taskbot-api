# api.py
# TaskBot API - FastAPI wrapper para commands.py + SQLite
# Compatible con Render.com (Free Tier)

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 🎯 Definir 'app' PRIMERO (lo que busca uvicorn)
app = FastAPI(title="TaskBot API", version="1.0")

# 📁 Configurar ruta de BD persistente para Render
DATA_DIR = Path("/app/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DB_PATH"] = str(DATA_DIR / "tareas.db")

# 📦 Importar lógica local (commands.py y database.py deben estar en la misma carpeta)
try:
    import database
    import commands
except ImportError as e:
    print(f"❌ Error importando módulos locales: {e}", file=sys.stderr)
    print(f"📂 Archivos en directorio: {list(Path('.').iterdir())}", file=sys.stderr)
    raise

# Inicializar BD al arrancar el servicio
try:
    database.init_db()
    print("✅ Base de datos inicializada en /app/data/tareas.db")
except Exception as e:
    print(f"❌ Error inicializando BD: {e}", file=sys.stderr)
    raise

# ── Modelos Pydantic ──
class CommandInput(BaseModel):
    texto: str  # Ej: "CREAR::TAREA::supermercado::leche;pan"

class QueryInput(BaseModel):
    tipo: str = "PENDIENTES"
    filtro: str | None = None

# ── Endpoints ──
@app.get("/")
def root():
    return {"status": "ok", "service": "TaskBot API", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/ejecutar")
def ejecutar_comando(input: CommandInput):
    """Ejecuta cualquier comando compatible con commands.py"""
    try:
        cmd = commands.parsear(input.texto)
        if not cmd:
            return {"error": "Formato inválido. Usa: ACCIÓN::PARTE1::PARTE2"}
        
        resultado = commands.ejecutar(cmd)
        return {"resultado": resultado, "input": input.texto}
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/consultar")
def consultar(tipo: str = "PENDIENTES", filtro: str | None = None):
    """Consulta rápida: /consultar?tipo=PENDIENTES&filtro=supermercado"""
    try:
        if filtro:
            cmd_texto = f"CONSULTA::{tipo}::{filtro}"
        else:
            cmd_texto = f"CONSULTA::{tipo}"
        
        cmd = commands.parsear(cmd_texto)
        if not cmd:
            raise HTTPException(status_code=400, detail="Tipo de consulta no válido")
        
        resultado = commands.ejecutar(cmd)
        return {"resultado": resultado, "query": cmd_texto}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en consulta: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))