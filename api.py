# api.py
import os, sys, logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import database as db
import commands

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("lifespan: iniciando...")
        await db.init_db()
        logger.info("lifespan: BD inicializada")
        yield
    except Exception as e:
        logger.error(f"lifespan CRASH: {e}")
        raise

app = FastAPI(title="TaskBot API", lifespan=lifespan)

# Manejador global de errores
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled: {exc}")
    import traceback; traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"status": "error", "msg": f"{type(exc).__name__}: {exc}", "items": []}
    )

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
    logger.info(f"Recibido: '{input.texto}'")
    cmd = commands.parsear(input.texto)
    
    if not cmd:
        logger.warning(f"Parseo fallido para: '{input.texto}'")
        return JSONResponse(
            status_code=400,
            content={
                "status": "error", 
                "msg": f"Formato inválido. Recibí: '{input.texto}'. Usa 'help' para ver comandos.", 
                "items": []
            }
        )
    
    resultado = await commands.ejecutar(cmd)
    logger.info(f"Respuesta: {resultado['msg'][:50]}...")
    return {"status": "ok", "msg": resultado["msg"], "items": resultado["items"]}