#!/usr/bin/env python3
"""TaskBot CLI - Gestiona tareas desde la terminal del MacBook."""
import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

import database as db
import commands

PROMPT = "\033[36mtaskbot>\033[0m "

def color_output(msg: str) -> str:
    """Aplica color a la salida para mejor legibilidad en terminal."""
    lines = []
    for line in msg.split("\n"):
        if " · " in line and "[Pendiente]" in line:
            parts = line.split(" · ", 3)
            if len(parts) >= 4:
                line = f"\033[33m{parts[0]}\033[0m · \033[1m{parts[1]}\033[0m · \033[1m{parts[2]}\033[0m · \033[90m{parts[3]}\033[0m"
        elif " · " in line and "[Completada]" in line:
            parts = line.split(" · ", 3)
            if len(parts) >= 4:
                line = f"\033[32m{parts[0]}\033[0m · \033[1m{parts[1]}\033[0m · \033[1m{parts[2]}\033[0m · \033[90m{parts[3]}\033[0m"
        elif line.startswith("Error"):
            line = f"\033[31m{line}\033[0m"
        lines.append(line)
    return "\n".join(lines)


async def ejecutar_y_mostrar(texto: str):
    cmd = commands.parsear(texto)
    if not cmd:
        print(f"\033[31mComando inválido:\033[0m '{texto}'. Usa 'help'.")
        return
    resultado = await commands.ejecutar(cmd)
    print(color_output(resultado["msg"]))


async def modo_interactivo():
    print("\033[1mTaskBot CLI\033[0m — escribe \033[33mhelp\033[0m, \033[33msalir\033[0m o Ctrl+D.\n")
    try:
        while True:
            try:
                texto = input(PROMPT).strip()
            except (EOFError, KeyboardInterrupt):
                print("\n¡Hasta luego!")
                break
            if not texto:
                continue
            if texto.lower() in ("salir", "exit", "quit", "q"):
                print("¡Hasta luego!")
                break
            await ejecutar_y_mostrar(texto)
    except KeyboardInterrupt:
        print()


async def modo_comando(cmd_texto: str):
    await ejecutar_y_mostrar(cmd_texto)


async def main():
    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")
    if not url or not token:
        print("\033[31mError:\033[0m Variables TURSO_DATABASE_URL y TURSO_AUTH_TOKEN no encontradas.")
        print("Asegúrate de tener un archivo .env en el directorio del proyecto.")
        sys.exit(1)

    db.get_db()

    try:
        if len(sys.argv) > 1:
            await modo_comando(" ".join(sys.argv[1:]))
        else:
            await modo_interactivo()
    finally:
        await db.close_db()


if __name__ == "__main__":
    asyncio.run(main())
