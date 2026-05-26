# api.py
import os, sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
import database as db
import commands

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    yield

app = FastAPI(title="TaskBot API", lifespan=lifespan)

class CommandInput(BaseModel):
    texto: str

@app.post("/ejecutar")
async def ejecutar_comando(input: CommandInput):
    cmd = commands.parsear(input.texto)
    if not cmd:
        return {"status": "error", "msg": "Formato inválido. Usa: ACCIÓN::PARTE1::PARTE2", "items": []}
    
    resultado = await commands.ejecutar(cmd)
    return {"status": "ok", "msg": resultado["msg"], "items": resultado["items"]}

@app.get("/health")
def health():
    return {"status": "healthy", "python": sys.version}