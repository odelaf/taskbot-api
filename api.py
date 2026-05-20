# api.py (fragmentos clave)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import database, commands  # Tu commands.py actual

app = FastAPI()

# Inicializar BD al arrancar
@app.on_event("startup")
async def startup():
    await database.init_db()

class CommandInput(BaseModel):
    texto: str

@app.post("/ejecutar")
async def ejecutar_comando(input: CommandInput):
    try:
        cmd = commands.parsear(input.texto)
        if not cmd:
            return {"error": "Formato inválido"}
        resultado = await commands.ejecutar(cmd)  # ← Ahora async
        return {"resultado": resultado}
    except Exception as e:
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
        raise HTTPException(status_code=500, detail=str(e))