# api.py
# TaskBot API - FastAPI + Turso (persistente)
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import database, commands

# ── Lifespan: inicializa BD al arrancar ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: inicializar BD
    await database.init_db()
    yield
    # Shutdown: (opcional) limpiar recursos si es necesario

# ── App con lifespan ──
app = FastAPI(title="TaskBot API", version="1.0", lifespan=lifespan)

# ── Modelos ──
class CommandInput(BaseModel):
    texto: str

# ── Endpoints ──
@app.get("/")
def root():
    return {"status": "ok", "service": "TaskBot API", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/ejecutar")
async def ejecutar_comando(input: CommandInput):
    try:
        cmd = commands.parsear(input.texto)
        if not cmd:
            return {"error": "Formato inválido. Usa: ACCIÓN::PARTE1::PARTE2"}
        resultado = await commands.ejecutar(cmd)
        return {"resultado": resultado}
    except Exception as e:
        print(f"❌ Error: {e}")
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
        print(f"❌ Error consulta: {e}")
        raise HTTPException(status_code=500, detail=str(e))