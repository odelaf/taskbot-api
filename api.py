# api.py
# TaskBot API - FastAPI + Turso (persistente) - Compatible con Render
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import database
import commands

# ── Lifespan: inicializa BD al arrancar (CORRECTO para FastAPI) ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print("🚀 Iniciando TaskBot API...", file=sys.stderr)
        await database.init_db()
        print("✅ BD persistente inicializada en Turso", file=sys.stderr)
        yield
    except Exception as e:
        print(f"❌ FALLO CRÍTICO AL INICIAR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

# ── App con lifespan ──
app = FastAPI(
    title="TaskBot API",
    version="1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None
)

# ── Modelos ──
class CommandInput(BaseModel):
    texto: str

# ── Endpoints ──
@app.get("/")
def root():
    return {"status": "ok", "service": "TaskBot API", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy", "python": sys.version}

@app.post("/ejecutar")
async def ejecutar_comando(input: CommandInput):
    try:
        cmd = commands.parsear(input.texto)
        if not cmd:
            return {"error": "Formato inválido. Usa: ACCIÓN::PARTE1::PARTE2"}
        resultado = await commands.ejecutar(cmd)
        return {"resultado": resultado}
    except Exception as e:
        print(f"❌ Error en /ejecutar: {e}", file=sys.stderr)
        import traceback; traceback.print_exc(file=sys.stderr)
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
        print(f"❌ Error en /consultar: {e}", file=sys.stderr)
        import traceback; traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))